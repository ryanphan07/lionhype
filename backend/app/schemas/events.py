from pydantic import BaseModel

class CommentaryQuip(BaseModel):
    text: str

class CommentaryResponse(BaseModel):
    quips: List[CommentaryQuip]
