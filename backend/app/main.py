import asyncio
import os
import shutil
import uuid

from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, HTTPException, Request
from pydantic import BaseModel
import boto3
from botocore.exceptions import NoCredentialsError
from app.services.video_processor import validate_upload_metadata, sanitize_filename, is_video_corrupt
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.schemas.events import CommentaryResponse
from app.services.commentary import process_video_commentary
from app.services.video_processor import process_video

app = FastAPI()
UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.exception_handler(Exception)
async def global_exception_handler(_, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": str(exc) or "Internal server error"})


@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    video_id = str(uuid.uuid4())
    base_dir = os.path.abspath(os.path.dirname(__file__))
    upload_dir = os.path.join(base_dir, "..", "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    # Sanitize filename
    safe_name = sanitize_filename(file.filename or f"upload_{video_id}.mp4")
    video_path = os.path.join(upload_dir, safe_name)
    frame_dir = os.path.join(upload_dir, "frames", video_id)
    os.makedirs(frame_dir, exist_ok=True)

    # Validate file
    validate_upload_metadata(file.filename, file.file.tell())

    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Check for file corruption
    if is_video_corrupt(video_path):
        return JSONResponse(status_code=400, content={"detail": "The uploaded video file is corrupt."})

    frame_paths = await process_video(video_path, frame_dir, sample_interval_sec=2)
    return JSONResponse(content={"video_id": video_id, "video_path": video_path, "frame_paths": frame_paths})


@app.websocket("/ws/analyze")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_json()
            video_path = payload.get("video_path")
            if not video_path:
                raise ValueError("video_path is required")

            await websocket.send_json({"status": "processing", "progress": 15, "message": "extracting"})
            commentary = await process_video_commentary(video_path)
            await websocket.send_json({"status": "processing", "progress": 70, "message": "analyzing"})
            await websocket.send_json({"status": "processing", "progress": 90, "message": "synthesizing"})
            await websocket.send_json({
                "status": "completed",
                "progress": 100,
                "message": "completed",
                "quips": [quip.model_dump() for quip in commentary.quips],
            })
    except WebSocketDisconnect:
        await websocket.close()
    except Exception as exc:
        await websocket.send_json({"status": "error", "progress": 100, "message": str(exc)})


@app.post("/api/commentary/mock", response_model=CommentaryResponse, deprecated=True)
async def get_mock_commentary(payload: dict | None = None):
    payload = payload or {}
    video_path = payload.get("video_path")
    if not video_path:
        raise ValueError("video_path is required for commentary generation; /api/commentary/mock is deprecated")
    return await process_video_commentary(video_path)


@app.post("/api/commentary/generate", response_model=CommentaryResponse)
async def generate_commentary_endpoint(video_url: str):
    # Implement logic to process the video from the S3 URL
    # For now, return a mock response
    return CommentaryResponse(quips=[], video_url=video_url)
