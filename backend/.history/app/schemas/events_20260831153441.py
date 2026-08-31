from pydantic import BaseModel
from typing import List, Optional

class PerformanceEvent(BaseModel):
    timestamp_ms: int
    events: List[str]

class EventTimeline(BaseModel):
    performance_id: str
    timeline: List[PerformanceEvent]

class CommentaryQuip(BaseModel):
    timestamp_ms: int
    text: str
    sound_effect: Optional[str] = None

class CommentaryResponse(BaseModel):
    performance_id: str
    commentary: List[CommentaryQuip]