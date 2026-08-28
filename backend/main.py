import os
import json
import cv2
import base64
import asyncio
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocket_Exception
from typing import List
import ollama
import warnings

# Suppress warnings from OpenCV/FFmpeg if any
warnings.filterwarnings("ignore")

app = FastAPI(title="LionHype Backend")

# Configuration
USE_CLOUD_ENGINE = os.getenv("USE_CLOUD_ENGINE", "false").lower() == "true"
MODEL_NAME = "qwen2.5-vl:7b"
VIDEO_PATH = "video_input/lion_dance.mp4"

def extract_key_moments(video_path: str, sample_interval_sec: int = 3) -> List[dict]:
    \"\"\"
    Extracts keyframes from the video and returns a list of dictionaries containing
    the timestamp and base64 encoded image.
    \"\"\"
    keyframes = []
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return []

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % int(fps * sample_interval_sec) == 0:
            sec = frame_count / fps
            timestamp = f"{{int(sec // 60):02d}}:{{int(sec % 60):02d}}"
            # Resize for model compatibility
            resized_frame = cv2.resize(frame, (640, 360))
            success, buffer = cv2.imencode('.jpg', resized_frame)
            if success:
                # Encode to base64 for easy transmission to LLM
                img_b64 = base64.b64encode(buffer).decode('utf-8')
                keyframes.append({
                    "timestamp": timestamp,
                    "seconds": sec,
                    "image_b64": img_b64
                })
        frame_count += 1

    cap.release()
    return keyframes

@app.websocket("/ws/analyze")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected to WebSocket")

    keyframes = extract_key_moments(VIDEO_PATH)

    prompt = \"\"\"You are LionHype, an energetic lion dance commentator. Analyze the frame.
    Return STRICT JSON: {"commentary": "1-2 sentence roast/hype", "sfx": "gong|cymbals|airhorn|drumroll|none"}
    \"\"\"

    for kf in keyframes:
        try:
            if USE_CLOUD_ENGINE:
                # Placeholder for Gemini logic
                # In a production environment, you would use the google-generativeai library
                # For now, we'll use a simplified logic or the default if not configured
                pass

            response = ollama.chat(
                model=MODEL_NAME,
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': [kf["image_b64"]]
                }]
            )

            content = response['message']['content']
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                # Fallback if response is not strict JSON
                data = {"commentary": content, "sfx": "none"}

            payload = {
                "timestamp": kf["timestamp"],
                "seconds": kf["seconds"],
                "commentary": data.get("commentary", ""),
                "sfx": data.get("sfx", "none").lower()
            }

            await websocket.send_json(payload)
            await asyncio.sleep(1) # Reduced wait to match processing
        except Exception as e:
            print(f"Error processing frame at {kf['timestamp']}: {e}")
            continue
