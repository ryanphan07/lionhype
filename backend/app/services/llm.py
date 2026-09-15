import asyncio
import json
import logging
from typing import Any, Dict, List

from app.config import Settings
from app.schemas.events import CommentaryResponse, EventTimeline

logger = logging.getLogger("lionhype.llm")

try:
    from openai import AsyncOpenAI
except ImportError:  # pragma: no cover - optional dependency in lightweight CI
    AsyncOpenAI = None

settings = Settings()

llm_client = AsyncOpenAI(
    base_url=settings.LLM_BASE_URL,
    api_key=settings.LLM_API_KEY,
    timeout=settings.LLM_TIMEOUT,
) if AsyncOpenAI is not None else None

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


async def _retry_llm_call(func, max_retries=settings.LLM_MAX_RETRIES, base_delay=1.0, timeout=settings.LLM_TIMEOUT):
    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            return await asyncio.wait_for(func(), timeout=timeout)
        except Exception as e:
            last_exc = e
            if attempt < max_retries:
                logger.warning("LLM call failed on attempt %d/%d: %s", attempt + 1, max_retries + 1, str(e))
                await asyncio.sleep(base_delay * (2 ** attempt))
            else:
                logger.error("LLM service is unreachable after %d attempts.", max_retries + 1)
    raise last_exc


async def generate_event_timeline(frames: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert sampled video frames into a simple list of commentary cues."""
    if not frames:
        return []

    if settings.LLM_ENABLED and llm_client is not None:
        async def _call_llm():
            payload = {"frames": frames}
            response = await llm_client.chat.completions.create(
                model=settings.LLM_MODEL,
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
                    logger.debug("Successfully parsed %d raw items.", len(commentary_items))
                    return _normalize_timeline_items(commentary_items)
            return None

        try:
            result = await _retry_llm_call(_call_llm)
            if result:
                return result
        except Exception:
            pass

    return [
        {
            "timestamp": float(frame["timestamp"]),
            "text": f"Frame at {float(frame['timestamp']):.2f}s captures the highlight reel energy.",
        }
        for frame in frames
    ]


async def generate_commentary(timeline: EventTimeline) -> CommentaryResponse:
    user_content = f"Generate commentary for these events: {timeline.model_dump_json()}"
    
    if not settings.LLM_ENABLED or llm_client is None:
        return CommentaryResponse(quips=[{"timestamp": 0.0, "text": "Commentary unavailable in offline mode."}])

    async def _call_llm():
        response = await llm_client.chat.completions.create(
            model=settings.LLM_MODEL,
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

    try:
        return await _retry_llm_call(_call_llm)
    except Exception:
        return CommentaryResponse(quips=[{"timestamp": 0.0, "text": "Commentary unavailable in offline mode."}])
