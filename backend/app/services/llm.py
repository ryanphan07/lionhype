import json
import os
from typing import Any, Dict, List

try:
    from openai import AsyncOpenAI
except ImportError:  # pragma: no cover - optional dependency in lightweight CI
    AsyncOpenAI = None

from app.schemas.events import CommentaryResponse, EventTimeline

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://127.0.0.1:8080/v1")
llm_client = AsyncOpenAI(base_url=LLM_BASE_URL, api_key="local-key") if AsyncOpenAI is not None else None

SYSTEM_PROMPT = """You are an energetic, hilarious, over-the-top lion dance sports commentator. 
Analyze the provided performance timeline of events and output high-energy commentary quips with timestamps.
Return ONLY valid JSON with keys: performance_id, commentary (list of objects with timestamp_ms, text, sound_effect)."""


def _normalize_timeline_items(items):
    normalized = []
    for item in items:
        if not isinstance(item, dict):
            continue
        timestamp = item.get("timestamp")
        if timestamp is None and "timestamp_ms" in item:
            timestamp = float(item["timestamp_ms"]) / 1000.0
        if timestamp is None:
            timestamp = 0.0
        normalized.append({
            "timestamp": float(timestamp),
            "text": item.get("text") or item.get("commentary") or "",
        })
    return normalized


async def generate_event_timeline(frames: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert sampled video frames into a simple list of commentary cues."""
    if not frames:
        return []

    if llm_client is not None:
        payload = {"frames": frames}
        response = await llm_client.chat.completions.create(
            model="qwen-coder",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(payload)},
            ],
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        if isinstance(content, str):
            parsed = json.loads(content)
            commentary_items = parsed.get("commentary") or parsed.get("quips") or []
            if commentary_items:
                return _normalize_timeline_items(commentary_items)

    return [
        {
            "timestamp": float(frame["timestamp"]),
            "text": f"Frame at {float(frame['timestamp']):.2f}s captures the highlight reel energy.",
        }
        for frame in frames
    ]


async def generate_commentary(timeline: EventTimeline) -> CommentaryResponse:
    user_content = f"Generate commentary for these events: {timeline.model_dump_json()}"
    if llm_client is None:
        return CommentaryResponse(quips=[{"timestamp": 0.0, "text": "Commentary unavailable in offline mode."}])

    response = await llm_client.chat.completions.create(
        model="qwen-coder",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.7,
        response_format={"type": "json_object"},
    )

    raw_json = json.loads(response.choices[0].message.content)
    normalized = _normalize_timeline_items(raw_json.get("commentary") or raw_json.get("quips") or [])
    return CommentaryResponse(quips=normalized)