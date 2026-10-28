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


LAST_QUIP_MAX_WORDS = 14
MIN_QUIP_WORDS = 3


def finalize_timeline(quips: List[Dict[str, Any]], duration: float) -> List[Dict[str, Any]]:
    """Sort, clamp to the video, enforce the minimum gap, and cut each quip to fit the time before the next."""
    clamped = [
        {"timestamp": min(max(q["timestamp"], 0.0), duration), "text": q["text"]}
        for q in sorted(quips, key=lambda q: q["timestamp"])
    ]
    kept: List[Dict[str, Any]] = []
    for quip in clamped:
        if kept and quip["timestamp"] - kept[-1]["timestamp"] < settings.MIN_QUIP_GAP_SEC:
            continue
        kept.append(quip)
    result = []
    for i, quip in enumerate(kept):
        if i + 1 < len(kept):
            gap = kept[i + 1]["timestamp"] - quip["timestamp"]
            max_words = max(MIN_QUIP_WORDS, int(gap * settings.QUIP_WORDS_PER_SECOND))
        else:
            max_words = LAST_QUIP_MAX_WORDS
        text = " ".join(quip["text"].split()[:max_words])
        if text:
            result.append({"timestamp": quip["timestamp"], "text": text})
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
    semaphore = asyncio.Semaphore(4)
    
    async def _safe_generate_audio(quip: Dict[str, Any]) -> Dict[str, Any]:
        async with semaphore:
            return await tts_service.generate_audio_clip(quip, video_id=video_id)

    audio_tasks = [_safe_generate_audio(quip) for quip in normalized_quips]
    synthesized_audio = await asyncio.gather(*audio_tasks, return_exceptions=True)
    
    total = len(normalized_quips)
    done = 0
    quips: List[CommentaryQuip] = []
    all_failed = True
    
    for index, quip in enumerate(normalized_quips):
        result = synthesized_audio[index]
        done += 1
        await _report("synthesizing", 70 + int(25 * done / total))
        
        if isinstance(result, Exception):
            logger.warning("TTS failed for quip index %d: %s", index, result)
            audio_url = None
        else:
            audio_url = result.get("audio_url")
            
        if audio_url is not None:
            all_failed = False
            
        quip_payload = dict(quip)
        quip_payload["audio_url"] = audio_url
        quips.append(CommentaryQuip(**quip_payload))

    if all_failed:
        logger.error("All TTS clips failed for video_id: %s", video_id)

    logger.info("Pipeline for %s finished in %.1fs", video_id, time.monotonic() - started)
    return CommentaryResponse(quips=quips)
