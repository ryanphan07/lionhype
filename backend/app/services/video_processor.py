import os
import cv2
from typing import List

async def process_video(video_path: str, frame_dir: str, sample_interval_sec: int = 2) -> List[str]:
    cap = cv2.VideoCapture(video_path)
    frame_paths = []
    frame_count = 0
    sample_frame_count = sample_interval_sec * cap.get(cv2.CAP_PROP_FPS)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % sample_frame_count == 0:
            frame_filename = f"frame_{frame_count}.jpg"
            frame_path = os.path.join(frame_dir, frame_filename)
            cv2.imwrite(frame_path, frame)
            frame_paths.append(frame_path)

        frame_count += 1

    cap.release()
    return frame_paths
