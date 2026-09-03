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
    frame_count = 0
    frame_interval = max(1, int(fps * frame_interval_sec))

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

    return frames if frames else None

import os
import re
import cv2
from pathlib import Path

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi"}
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB


def sanitize_filename(filename: str) -> str:
    """
    Sanitize incoming filenames to prevent path traversal attacks.
    Strips directory paths and restricts characters to alphanumeric, underscores, hyphens, and periods.
    """
    basename = os.path.basename(filename)
    sanitized = re.sub(r"[^a-zA-Z0-9_\.-]", "_", basename)
    return sanitized.lstrip(".")


def validate_upload_metadata(filename: str, file_size: int) -> None:
    """
    Validates file extension and file size.
    Raises ValueError on failure to be caught by route handlers.
    """
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Invalid file extension '{ext}'. Allowed extensions are: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError("File size exceeds the maximum limit of 100MB.")


def is_video_corrupt(file_path: str) -> bool:
    """
    Verifies video file integrity using OpenCV by ensuring the container opens
    and at least the initial frame can be decoded successfully.
    """
    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        return True

    ret, frame = cap.read()
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    if not ret or frame is None or frame.size == 0 or frame_count <= 0:
        return True

    return False


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
