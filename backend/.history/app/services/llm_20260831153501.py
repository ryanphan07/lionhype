import os
import json
from openai import AsyncOpenAI
from app.schemas.events import EventTimeline, CommentaryResponse

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://127.0.0.1:8080/v1")
llm_client = AsyncOpenAI(base_url=LLM_BASE_URL, api_key="local-key")

SYSTEM_PROMPT = """You are an energetic, hilarious, over-the-top lion dance sports commentator. 
Analyze the provided performance timeline of events and output high-energy commentary quips with timestamps.
Return ONLY valid JSON with keys: performance_id, commentary (list of objects with timestamp_ms, text, sound_effect)."""

async def generate_commentary(timeline: EventTimeline) -> CommentaryResponse:
    user_content = f"Generate commentary for these events: {timeline.model_dump_json()}"
    
    response = await llm_client.chat.completions.create(
        model="qwen-coder",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    
    raw_json = json.loads(response.choices[0].message.content)
    return CommentaryResponse(**raw_json)