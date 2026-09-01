import os
import base64
import json
import httpx
import asyncio
from typing import List
from app.schemas.events import CommentaryQuip, CommentaryResponse
from app.services.tts import generate_audio_commentary

COMMENTARY_SYSTEM_PROMPT = """
You are an unhinged, high-energy, deeply sarcastic sports commentator roasting amateur athlete practice footage.
Your job is to analyze video keyframes and call out bad form, exaggerated effort, and mid-play hesitation.

Tone requirements:
- Sarcasm level: 80% (cutting, witty observations about athletic failure)
- Energy level: 10% (bursts of screaming hype man energy)
- Chaos level: 10% (bizarre analogies and dramatic overreactions)

Return strictly valid JSON formatted as a list of objects containing timestamp (in seconds) and text quips:
[
  {"timestamp": 2.0, "text": "Observe the absolute peak athletic performance of missing a stationary target."}
]
"""

def encode_image_to_base64(image_path: str) -> str:
    """Helper function to encode a frame image to base64 format."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

async def generate_video_commentary(video_id: str) -> CommentaryResponse:
    # Ensure correct local pathing relative to execution directory
    base_dir = os.path.abspath(os.path.dirname(__file__))
    frame_dir = os.path.join(base_dir, "..", "uploads", "frames", video_id)
    if not os.path.exists(frame_dir):
        # Fallback if executed from outside backend/
        frame_dir = os.path.join(base_dir, "..", "..", "uploads", "frames", video_id)

    frame_files = sorted(os.listdir(frame_dir))
    commentary_quips = []

    async with httpx.AsyncClient(timeout=60.0) as client:
        tasks = []
        for frame_file in frame_files:
            if not frame_file.endswith((".jpg", ".png", ".jpeg")):
                continue

            frame_path = os.path.join(frame_dir, frame_file)
            base64_image = encode_image_to_base64(frame_path)

            # Calculate timestamp assuming file naming convention: frame_0.jpg, frame_1.jpg...
            try:
                frame_index = int(frame_file.split("_")[1].split(".")[0])
                timestamp = float(frame_index * 2)  # 2 seconds per frame interval
            except Exception:
                timestamp = 0.0

            payload = {
                "model": "qwen-coder",
                "messages": [
                    {
                        "role": "system",
                        "content": COMMENTARY_SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"Analyze this keyframe at timestamp {timestamp} seconds and provide a short sarcastic roast line."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 150,
                "temperature": 0.7
            }

            tasks.append(client.post("http://127.0.0.1:8080/v1/chat/completions", json=payload))

        responses = await asyncio.gather(*tasks)

        for response in responses:
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()
                
                # If model wraps response in Markdown codeblocks, strip them
                if content.startswith("```"):
                    content = content.replace("```json", "").replace("```", "").strip()

                commentary_quips.append(CommentaryQuip(timestamp=timestamp, text=content))
            else:
                print(f"Server error: {response.status_code} - {response.text}")

    # Generate audio commentary
    audio_commentary = await generate_audio_commentary(video_id, [{"timestamp": quip.timestamp, "text": quip.text} for quip in commentary_quips])

    # Combine commentary and audio data
    combined_commentary = []
    for quip, audio in zip(commentary_quips, audio_commentary):
        combined_commentary.append({
            "timestamp": quip.timestamp,
            "text": quip.text,
            "audio_url": audio["audio_url"]
        })

    return CommentaryResponse(quips=combined_commentary)
