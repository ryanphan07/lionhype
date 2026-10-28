import asyncio
import logging
import time
from typing import Any, Awaitable, Callable, Dict, List, Optional

from app.config import settings
from app.schemas.events import CommentaryQuip, CommentaryResponse
from app.services import llm as llm_service
from app.services import tts as tts_service
from app.services import video_processor as video_processor_service

logger = logging.getLogger("lionhype.commentary")


AUDIO_GAP_SEC = 0.3


def finalize_timeline(quips: List[Dict[str, Any]], duration: float) -> List[Dict[str, Any]]:
    """Sort, clamp to the video, enforce the minimum gap, drop empty text. Text is never cut: overlong lines are
    handled by schedule_quips after their real audio duration is known."""
    clamped = [
        {"timestamp": round(min(max(q["timestamp"], 0.0), duration), 2), "text": " ".join(q["text"].split())}
        for q in sorted(quips, key=lambda q: q["timestamp"])
    ]
    kept: List[Dict[str, Any]] = []
    for quip in clamped:
        if not quip["text"]:
            continue
        if kept and quip["timestamp"] - kept[-1]["timestamp"] < settings.MIN_QUIP_GAP_SEC:
            continue
        kept.append(quip)
    return kept


def schedule_quips(quips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Keep spoken quips from overlapping: shift late by up to MAX_SHIFT_SEC, else drop. Quips without audio never block."""
    result: List[Dict[str, Any]] = []
    audio_end: Optional[float] = None
    for quip in sorted(quips, key=lambda q: q["timestamp"]):
        quip = dict(quip)
        if quip.get("audio_url") and quip.get("duration_sec"):
            start = quip["timestamp"]
            if audio_end is not None and start < audio_end + AUDIO_GAP_SEC:
                new_start = audio_end + AUDIO_GAP_SEC
                shift = new_start - start
                if shift > settings.MAX_SHIFT_SEC:
                    logger.warning("Dropping quip at t=%.2f: would need a %.2fs shift (max %.2fs)", start, shift, settings.MAX_SHIFT_SEC)
                    continue
                logger.info("Shifting quip from t=%.2f to t=%.2f to avoid audio overlap", start, new_start)
                quip["timestamp"] = start = round(new_start, 2)
            audio_end = start + quip["duration_sec"]
        result.append(quip)
    return result


async def process_video_commentary(
    video_path: str,
    job_id: Optional[str] = None,
    progress_cb: Optional[Callable[[str, int, Optional[str]], Awaitable[None]]] = None
) -> CommentaryResponse:
    video_id = job_id or "default"
    started = time.monotonic()
    logger.info("Starting commentary generation for video_id: %s", video_id)

    async def _report(status: str, progress: int, message: Optional[str] = None) -> None:
        if progress_cb is None:
            return
        try:
            await progress_cb(status, progress, message)
        except Exception as e:
            logger.warning("Progress callback failed: %s", e)

    await _report("extracting", 10)
    duration = await asyncio.to_thread(video_processor_service.get_video_duration, video_path)
    box = await asyncio.to_thread(video_processor_service.compute_crop_box, video_path, duration)
    windows = video_processor_service.plan_windows(duration, settings.WINDOW_SECONDS)
    if not windows:
        raise ValueError("No frames could be extracted from video")

    raw_quips: List[Dict[str, Any]] = []
    previous: List[str] = []
    total_windows = len(windows)
    for i, (start, end) in enumerate(windows):
        await _report("analyzing", 20 + int(45 * i / total_windows), f"Analyzing part {i + 1} of {total_windows}")
        frames = await asyncio.to_thread(
            video_processor_service.sample_window_frames,
            video_path, start, end, settings.FRAMES_PER_WINDOW, settings.FRAME_WIDTH, box,
        )
        if not frames:
            raise ValueError(f"No frames could be extracted for window {i + 1} of {total_windows}")
        window_quips = await llm_service.analyze_window(
            frames, start, end, previous, label=f"window {i + 1}/{total_windows}"
        )
        raw_quips.extend(window_quips)
        if window_quips:
            previous = [q["text"] for q in window_quips[-2:]]

    normalized_quips = finalize_timeline(raw_quips, duration)
    if not normalized_quips:
        raise ValueError("The model produced no usable commentary")
    logger.info("Timeline: %d quips from %d windows", len(normalized_quips), total_windows)

    await _report("synthesizing", 70)
    semaphore = asyncio.Semaphore(settings.TTS_CONCURRENCY)

    async def _safe_generate_audio(quip: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        async with semaphore:
            try:
                return await tts_service.generate_audio_clip(quip, video_id=video_id)
            except Exception as e:
                logger.warning("TTS failed for t=%.2f: %s", quip["timestamp"], e)
                return None

    results = await asyncio.gather(*(_safe_generate_audio(q) for q in normalized_quips))
    await _report("synthesizing", 90)

    with_audio: List[Dict[str, Any]] = []
    for quip, result in zip(normalized_quips, results):
        payload = dict(quip)
        payload["audio_url"] = result.get("audio_url") if result else None
        payload["duration_sec"] = result.get("duration_sec") if result and payload["audio_url"] else None
        with_audio.append(payload)

    scheduled = schedule_quips(with_audio)
    audio_available = any(q["audio_url"] for q in scheduled)
    if not audio_available:
        logger.error("No audio clips available for video_id: %s", video_id)

    logger.info("Pipeline for %s finished in %.1fs", video_id, time.monotonic() - started)
    return CommentaryResponse(
        quips=[CommentaryQuip(**q) for q in scheduled], audio_available=audio_available
    )
