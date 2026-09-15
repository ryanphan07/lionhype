import asyncio
import logging
from typing import Any, Dict, List

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


async def process_video_commentary(video_path: str) -> CommentaryResponse:
    logger.info("Starting commentary generation for video_id: %s", video_path)
    
    frames = await asyncio.to_thread(video_processor_service.extract_frames, video_path)
    
    if not frames:
        logger.warning("Frame extraction returned 0 frames for video_id: %s", video_path)
        return CommentaryResponse(quips=[])
        
    logger.info("Frame extraction completed. Extracted %d frames.", len(frames))
    
    event_timeline = await llm_service.generate_event_timeline(frames)
    logger.info("LLM event timeline generated successfully.")

    if not event_timeline:
        return CommentaryResponse(quips=[])

    normalized_quips = [_normalize_quip(quip) for quip in event_timeline]
    audio_tasks = [tts_service.generate_audio_clip(quip, video_id="default") for quip in normalized_quips]
    
    try:
        synthesized_audio = await asyncio.gather(*audio_tasks)
        logger.info("TTS synthesis completed successfully.")
    except Exception as e:
        logger.exception("TTS synthesis failed.")
        raise

    quips: List[CommentaryQuip] = []
    for index, quip in enumerate(normalized_quips):
        audio_data = synthesized_audio[index]
        quip_payload = dict(quip)
        quip_payload["audio_url"] = audio_data["audio_url"]
        quips.append(CommentaryQuip(**quip_payload))

    return CommentaryResponse(quips=quips)


async def generate_video_commentary(video_id: str) -> CommentaryResponse:
    """Backward-compatible wrapper for the older video-id-based API."""
    from pathlib import Path

    candidate_paths = [
        Path("backend/uploads/frames") / video_id,
        Path("uploads/frames") / video_id,
        Path("backend") / "uploads" / "frames" / video_id,
    ]

    for frame_dir in candidate_paths:
        if frame_dir.exists():
            frame_paths = sorted(frame_dir.glob("*.jpg"))
            frames = []
            for frame_path in frame_paths:
                frames.append({"timestamp": float(frame_path.stem.split("_")[-1]) if frame_path.stem.split("_")[-1].replace(".", "", 1).isdigit() else 0.0, "image_data": ""})
            return await process_video_commentary(str(frame_dir.parent / "video.mp4"))

    return CommentaryResponse(quips=[])
