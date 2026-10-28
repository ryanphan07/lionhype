import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional

from app.schemas.events import CommentaryQuip, CommentaryResponse
from app.services import llm as llm_service
from app.services import tts as tts_service
from app.services import video_processor as video_processor_service

logger = logging.getLogger("lionhype.commentary")


def _normalize_quip(quip: Dict[str, Any]) -> Dict[str, Any]:
    timestamp = quip.get("timestamp")
    if timestamp is None and "timestamp_ms" in quip:
        timestamp = float(quip["timestamp_ms"]) / 1000.0
    if timestamp is None:
        timestamp = 0.0
    return {
        "timestamp": float(timestamp),
        "text": quip.get("text") or quip.get("commentary") or "",
    }


async def process_video_commentary(
    video_path: str,
    job_id: Optional[str] = None,
    progress_cb: Optional[Callable[[str, int, Optional[str]], Awaitable[None]]] = None
) -> CommentaryResponse:
    video_id = job_id or "default"
    logger.info("Starting commentary generation for video_id: %s", video_id)

    async def _report(status: str, progress: int, message: Optional[str] = None) -> None:
        if progress_cb is None:
            return
        try:
            await progress_cb(status, progress, message)
        except Exception as e:
            logger.warning("Progress callback failed: %s", e)

    await _report("extracting", 10)
    frames = await asyncio.to_thread(video_processor_service.extract_frames, video_path)
    
    if not frames:
        raise ValueError("No frames could be extracted from video")
        
    logger.info("Frame extraction completed. Extracted %d frames.", len(frames))
    
    await _report("analyzing", 40)
    event_timeline = await llm_service.generate_event_timeline(frames)
    logger.info("LLM event timeline generated successfully.")

    if not event_timeline:
        return CommentaryResponse(quips=[])

    normalized_quips = [_normalize_quip(quip) for quip in event_timeline]
    
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

    return CommentaryResponse(quips=quips)
