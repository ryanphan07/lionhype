import os
from typing import Any, Dict, List, Optional

try:
    from edge_tts import Communicate
except ImportError:  # pragma: no cover
    Communicate = None


async def generate_audio_clip(quip: Dict[str, Any], video_id: Optional[str] = None) -> Dict[str, Any]:
    timestamp = float(quip.get("timestamp", 0.0))
    text = str(quip.get("text", ""))
    video_id = video_id or "default"
    audio_dir = os.path.abspath(os.path.join("backend", "uploads", "audio", video_id))
    os.makedirs(audio_dir, exist_ok=True)

    audio_filename = f"audio_{timestamp:.2f}.mp3"
    audio_path = os.path.join(audio_dir, audio_filename)

    if Communicate is not None:
        communicate = Communicate(text, "en-US-AnaNeural")
        await communicate.save(audio_path)
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
