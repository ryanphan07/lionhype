from pydantic import BaseModel
from typing import List

class CommentaryQuip(BaseModel):
    text: str

class CommentaryResponse(BaseModel):
    quips: List[CommentaryQuip]
