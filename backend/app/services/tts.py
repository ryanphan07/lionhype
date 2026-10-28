import asyncio
import hashlib
import logging
import os
import re
from typing import Any, Dict, List, Optional

from app.config import settings

logger = logging.getLogger("lionhype.tts")

try:
    from edge_tts import Communicate
except ImportError:  # pragma: no cover
    Communicate = None

try:
    import aiohttp
except ImportError:  # pragma: no cover
    aiohttp = None

try:
    from mutagen.mp3 import MP3
except ImportError:  # pragma: no cover
    MP3 = None

MIN_AUDIO_BYTES = 200


def measure_duration(path: str) -> Optional[float]:
    """Return the mp3 duration in seconds, or None if it cannot be read."""
    if MP3 is None:
        return None
    try:
        length = float(MP3(path).info.length)
    except Exception:
        logger.warning("Could not measure duration of %s", path, exc_info=True)
        return None
    return length if length > 0 else None


def _is_transient(exc: BaseException) -> bool:
    """Timeouts and dropped connections are worth one more try; auth failures and bad requests are not."""
    if isinstance(exc, (asyncio.TimeoutError, ConnectionError)):
        return True
    if aiohttp is not None:
        if isinstance(exc, aiohttp.ClientResponseError):
            return exc.status >= 500
        if isinstance(exc, aiohttp.ClientConnectionError):
            return True
    return False


def _remove_quietly(path: str) -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
    except OSError:
        logger.warning("Could not delete partial audio file %s", path)


def remove_clip_file(video_id: str, audio_url: Optional[str]) -> None:
    """Delete the mp3 behind an audio_url (used for quips the scheduler dropped). Never raises."""
    if not audio_url or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", video_id):
        return
    name = os.path.basename(audio_url.split("?")[0])
    if not re.fullmatch(r"[A-Za-z0-9_.-]+\.mp3", name):
        return
    _remove_quietly(os.path.join(settings.UPLOAD_DIR, "audio", video_id, name))


async def generate_audio_clip(quip: Dict[str, Any], video_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Synthesize one quip. Returns the quip with audio_url and duration_sec, or None if no usable audio was produced."""
    timestamp = float(quip.get("timestamp", 0.0))
    text = str(quip.get("text", ""))
    video_id = video_id or "default"

    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", video_id):
        raise ValueError(f"Invalid video_id: {video_id}")

    if not text.strip():
        logger.warning("Skipping TTS for empty text at timestamp %s", timestamp)
        return None
    if not settings.TTS_ENABLED or Communicate is None:
        logger.warning("TTS is disabled or edge-tts is not installed; no audio for t=%.2f", timestamp)
        return None

    audio_dir = os.path.join(settings.UPLOAD_DIR, "audio", video_id)
    os.makedirs(audio_dir, exist_ok=True)
    text_hash = hashlib.sha1(text.encode()).hexdigest()[:8]
    audio_filename = f"audio_{timestamp:.2f}_{text_hash}.mp3"
    audio_path = os.path.join(audio_dir, audio_filename)

    attempts = 1 + max(0, settings.TTS_RETRIES)
    for attempt in range(1, attempts + 1):
        try:
            communicate = Communicate(text, settings.TTS_VOICE, rate=settings.TTS_RATE)
            await asyncio.wait_for(communicate.save(audio_path), timeout=settings.TTS_TIMEOUT_SECONDS)
            if not os.path.exists(audio_path) or os.path.getsize(audio_path) < MIN_AUDIO_BYTES:
                raise RuntimeError("TTS produced an empty or tiny file")
            break
        except Exception as e:
            _remove_quietly(audio_path)
            if attempt < attempts and _is_transient(e):
                logger.warning("TTS attempt %d failed for t=%.2f (%s); retrying", attempt, timestamp, e or type(e).__name__)
                await asyncio.sleep(settings.TTS_RETRY_DELAY_SECONDS)
                continue
            logger.warning("TTS failed for t=%.2f: %s", timestamp, e or type(e).__name__)
            return None

    duration = measure_duration(audio_path)
    if duration is None:
        logger.warning("Discarding audio for t=%.2f: duration unreadable", timestamp)
        _remove_quietly(audio_path)
        return None

    audio_url = f"{settings.PUBLIC_BASE_URL.rstrip('/')}/uploads/audio/{video_id}/{audio_filename}"
    return {"timestamp": timestamp, "text": text, "audio_url": audio_url, "duration_sec": duration}

