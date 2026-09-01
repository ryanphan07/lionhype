import os
import uuid
import shutil
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from app.services.llm import generate_commentary
from app.services.video_processor import process_video
from app.services.commentary import generate_video_commentary
from app.schemas.events import CommentaryResponse, CommentaryQuip

app = FastAPI()

@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    video_id = str(uuid.uuid4())
    base_dir = os.path.abspath(os.path.dirname(__file__))
    upload_dir = os.path.join(base_dir, "..", "uploads")
    video_path = os.path.join(upload_dir, file.filename)
    frame_dir = os.path.join(upload_dir, "frames", video_id)

    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    if not os.path.exists(frame_dir):
        os.makedirs(frame_dir)

    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    frame_paths = await process_video(video_path, frame_dir, sample_interval_sec=2)

    return JSONResponse(content={"video_id": video_id, "frame_paths": frame_paths})

@app.websocket("/ws/analyze")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Handle the received data
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        await websocket.close()

@app.post("/api/commentary/mock", response_model=CommentaryResponse)
async def get_mock_commentary():
    # Mock implementation
    return CommentaryResponse(quips=[CommentaryQuip(text="Mock commentary")])

@app.post("/api/commentary/generate", response_model=CommentaryResponse)
async def generate_commentary_endpoint(video_id: str):
    return await generate_video_commentary(video_id)
