from pydantic import BaseModel
from typing import List

class CommentaryQuip(BaseModel):
    timestamp: float
    text: str

class CommentaryResponse(BaseModel):
    quips: List[CommentaryQuip]
