import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from app.config import Settings

logger = logging.getLogger("lionhype.tts")

try:
    from edge_tts import Communicate
except ImportError:  # pragma: no cover
    Communicate = None

settings = Settings()

async def _retry_tts_call(func, max_retries=settings.TTS_MAX_RETRIES, base_delay=1.0, timeout=settings.TTS_TIMEOUT):
    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            return await asyncio.wait_for(func(), timeout=timeout)
        except Exception as e:
            last_exc = e
            if attempt < max_retries:
                logger.warning("TTS call failed on attempt %d/%d: %s", attempt + 1, max_retries + 1, str(e))
                await asyncio.sleep(base_delay * (2 ** attempt))
            else:
                logger.error("TTS service is unreachable after %d attempts.", max_retries + 1)
    raise last_exc


async def generate_audio_clip(quip: Dict[str, Any], video_id: Optional[str] = None) -> Dict[str, Any]:
    timestamp = float(quip.get("timestamp", 0.0))
    text = str(quip.get("text", ""))
    video_id = video_id or "default"
    audio_dir = os.path.abspath(os.path.join("backend", "uploads", "audio", video_id))
    os.makedirs(audio_dir, exist_ok=True)

    audio_filename = f"audio_{timestamp:.2f}.mp3"
    audio_path = os.path.join(audio_dir, audio_filename)

    if settings.TTS_ENABLED and Communicate is not None:
        async def _call_tts():
            communicate = Communicate(text, settings.TTS_VOICE)
            await communicate.save(audio_path)
        try:
            await _retry_tts_call(_call_tts)
        except Exception:
            with open(audio_path, "wb") as fake_audio:
                fake_audio.write(b"fake-audio")
    else:
        with open(audio_path, "wb") as fake_audio:
            fake_audio.write(b"fake-audio")

    audio_url = f"http://localhost:8000/uploads/audio/{video_id}/{audio_filename}"
    return {"timestamp": timestamp, "text": text, "audio_url": audio_url}


async def generate_audio_commentary(video_id: str, commentary_data: List[Dict]) -> List[Dict]:
    results = []
    for quip in commentary_data:
        results.append(await generate_audio_clip(quip, video_id=video_id))
    return results
