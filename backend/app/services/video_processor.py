import base64
import os
from typing import Any, Dict, List

import cv2


def extract_frames(video_path: str, frame_interval_sec: float = 1.0) -> List[Dict[str, Any]]:
    frames: List[Dict[str, Any]] = []
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Error opening video file")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_interval = max(1, int(fps * frame_interval_sec))
    frame_count = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_interval == 0:
                resized_frame = cv2.resize(frame, (224, 224))
                success, encoded = cv2.imencode(".jpg", resized_frame)
                if success:
                    b64_str = base64.b64encode(encoded.tobytes()).decode("utf-8")
                    timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                    frames.append({
                        "timestamp": round(timestamp, 2),
                        "image_data": b64_str,
                    })

            frame_count += 1
    finally:
        cap.release()

    return frames


async def process_video(video_path: str, frame_dir: str, sample_interval_sec: int = 2) -> List[str]:
    """Compatibility helper retained for existing upload flow."""
    frames = extract_frames(video_path, frame_interval_sec=sample_interval_sec)
    frame_paths: List[str] = []
    os.makedirs(frame_dir, exist_ok=True)

    for idx, frame in enumerate(frames):
        image_path = os.path.join(frame_dir, f"frame_{idx}.jpg")
        with open(image_path, "wb") as out_file:
            out_file.write(base64.b64decode(frame["image_data"]))
        frame_paths.append(image_path)

    return frame_paths
