import base64
import os
from typing import Any, Dict, List

import cv2


def extract_frames(video_path: str, frame_interval_sec: float = 1.0) -> List[Dict[str, Any]]:
    """Sample a video into resized, base64-encoded JPEG payloads with timestamps."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        cap.release()
        raise IOError(f"Could not open video file: {video_path}")

    frames: List[Dict[str, Any]] = []
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        fps = fps if fps and fps > 0 else 1.0
        frame_stride = max(1, int(round(fps * frame_interval_sec)))
        frame_index = 0
        timestamp = 0.0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_index % frame_stride == 0:
                resized = cv2.resize(frame, (640, 360), interpolation=cv2.INTER_AREA)
                success, encoded = cv2.imencode(".jpg", resized)
                if not success:
                    frame_index += 1
                    continue

                image_data = encoded.tobytes()
                frames.append({
                    "timestamp": round(timestamp, 2),
                    "image_data": image_data,
                })

            frame_index += 1
            timestamp = frame_index / fps
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
import cv2
from typing import List, Dict, Any

def extract_frames(video_path: str, frame_interval_sec: float = 1.0) -> List[Dict[str, Any]]:
    frames = []
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Error opening video file")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * frame_interval_sec)
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            # Resize frame to standard inference dimensions (e.g., 224x224)
            resized_frame = cv2.resize(frame, (224, 224))
            timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            frames.append({"timestamp": timestamp, "image_data": resized_frame})

        frame_count += 1

    cap.release()
    return frames
