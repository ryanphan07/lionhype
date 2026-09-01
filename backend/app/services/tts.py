import os
import asyncio
from edge_tts import Communicate
from typing import List, Dict

async def generate_audio_commentary(video_id: str, commentary_data: List[Dict]) -> List[Dict]:
    audio_dir = os.path.join("backend", "uploads", "audio", video_id)
    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)

    audio_urls = []

    for quip in commentary_data:
        timestamp = quip["timestamp"]
        text = quip["text"]
        audio_filename = f"audio_{timestamp:.2f}.mp3"
        audio_path = os.path.join(audio_dir, audio_filename)

        communicate = Communicate(text, "en-US-AnaNeural")
        await communicate.save(audio_path)

        audio_url = f"/uploads/audio/{video_id}/{audio_filename}"
        audio_urls.append({"timestamp": timestamp, "text": text, "audio_url": audio_url})

    return audio_urls
