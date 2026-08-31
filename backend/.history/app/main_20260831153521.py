from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import shutil
import os

from app.schemas.events import EventTimeline, PerformanceEvent, CommentaryResponse
from app.services.llm import generate_commentary

app = FastAPI(title="LionHype API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)
app.mount("/video_files", StaticFiles(directory="uploads"), name="uploads")

@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename, "url": f"/video_files/{file.filename}"}

@app.post("/api/commentary/mock", response_model=CommentaryResponse)
async def get_mock_commentary():
    mock_timeline = EventTimeline(
        performance_id="lion_01",
        timeline=[
            PerformanceEvent(timestamp_ms=2500, events=["crouch", "drum_roll"]),
            PerformanceEvent(timestamp_ms=5100, events=["high_pole_jump", "cymbal_crash", "crowd_cheer"]),
            PerformanceEvent(timestamp_ms=8300, events=["head_shake", "gong_hit"])
        ]
    )
    return await generate_commentary(mock_timeline)