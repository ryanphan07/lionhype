from pydantic import BaseModel
from typing import List, Optional

class EventTimeline(BaseModel):
    events: List[dict]

class CommentaryQuip(BaseModel):
    timestamp: float
    text: str
    audio_url: Optional[str] = None

class CommentaryResponse(BaseModel):
    quips: List[CommentaryQuip]
    video_url: Optional[str] = None  # Add this line
