import json
import logging
import re
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings

logger = logging.getLogger("maneframe.llm")

try:
    from openai import AsyncOpenAI
except ImportError:  # pragma: no cover - optional dependency in lightweight CI
    AsyncOpenAI = None

llm_client = AsyncOpenAI(
    base_url=settings.LLM_BASE_URL,
    api_key=settings.LLM_API_KEY,
    timeout=settings.LLM_TIMEOUT,
    max_retries=0,  # the SDK default of 2 would turn one 300 s timeout into 15 minutes
) if AsyncOpenAI is not None else None

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "commentary_system.txt"
JSON_NUDGE = "Your previous reply was not valid JSON. Return only the JSON object, no prose and no code fences."


class LLMOutputError(Exception):
    """The model replied, but not with usable JSON."""


@lru_cache(maxsize=1)
def _read_prompt_file() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def load_system_prompt() -> str:
    """The prompt file with the literal MAX_QUIPS replaced by MAX_QUIPS_PER_WINDOW."""
    return re.sub(r"MAX_QUIPS(?!_)", str(settings.MAX_QUIPS_PER_WINDOW), _read_prompt_file())


def strip_think(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return re.sub(r"^.*?</think>", "", text, flags=re.DOTALL).strip()  # opening tag was in the template


def parse_model_objects(text: str) -> List[Dict[str, Any]]:
    """Every top-level JSON object in the reply, in order. Strips <think> blocks and code fences, skips prose."""
    text = re.sub(r"```(?:json)?", "", strip_think(text or ""), flags=re.IGNORECASE)
    decoder = json.JSONDecoder()
    objects: List[Dict[str, Any]] = []
    pos = text.find("{")
    while pos != -1:
        try:
            obj, length = decoder.raw_decode(text[pos:])
        except json.JSONDecodeError:
            pos = text.find("{", pos + 1)
            continue
        if isinstance(obj, dict):
            objects.append(obj)
            pos = text.find("{", pos + length)
        else:
            pos = text.find("{", pos + 1)
    return objects


def parse_model_json(text: str) -> Dict[str, Any]:
    """The first JSON object in the reply."""
    objects = parse_model_objects(text)
    if not objects:
        raise LLMOutputError("No JSON object found in model reply")
    return objects[0]


def extract_quips(objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Quips from the first object with a 'quips' list; else from objects that are themselves single quips."""
    for obj in objects:
        if isinstance(obj.get("quips"), list):
            return clean_quips(obj)
    singles = [o for o in objects if "t" in o and "text" in o]
    if singles:
        quips = clean_quips({"quips": singles})
        if quips:
            return quips
    raise LLMOutputError("Model JSON has no 'quips' list")


def response_format() -> Dict[str, Any]:
    """JSON schema for the prompt's output: {"seen": str, "quips": [{"t": number, "text": str}]}."""
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "commentary",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "seen": {"type": "string"},
                    "quips": {
                        "type": "array",
                        "maxItems": settings.MAX_QUIPS_PER_WINDOW,
                        "items": {
                            "type": "object",
                            "properties": {"t": {"type": "number"}, "text": {"type": "string"}},
                            "required": ["t", "text"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["seen", "quips"],
                "additionalProperties": False,
            },
        },
    }


def clean_quips(parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return [{"timestamp", "text"}] sorted by time, dropping malformed or empty entries."""
    raw = parsed.get("quips")
    if not isinstance(raw, list):
        raise LLMOutputError("Model JSON has no 'quips' list")
    quips = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            t = float(item["t"])
        except (KeyError, TypeError, ValueError):
            continue
        text = " ".join(str(item.get("text") or "").split())
        if text and t == t:  # t == t rejects NaN
            quips.append({"timestamp": t, "text": text})
    return sorted(quips, key=lambda q: q["timestamp"])


def build_messages(
    frames: List[Dict[str, Any]],
    start: float,
    end: float,
    previous_quips: List[str],
    nudge: bool = False,
) -> List[Dict[str, Any]]:
    """System prompt first, the images last, so the server can reuse its prefix cache."""
    intro = f"These frames cover {start:.1f}s to {end:.1f}s of the video."
    if previous_quips:
        intro += " Your most recent previous quips (do not repeat them): " + json.dumps(previous_quips)
    if nudge:
        intro += " " + JSON_NUDGE
    content: List[Dict[str, Any]] = [{"type": "text", "text": intro}]
    for frame in frames:
        content.append({"type": "text", "text": f"Frame at t={frame['timestamp']}s:"})
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{frame['image_data']}"},
        })
    return [
        {"role": "system", "content": load_system_prompt()},
        {"role": "user", "content": content},
    ]


async def _call(messages: List[Dict[str, Any]], frame_count: int, label: str) -> str:
    started = time.monotonic()
    kwargs: Dict[str, Any] = {}
    if settings.LLM_JSON_SCHEMA:
        kwargs["response_format"] = response_format()
    response = await llm_client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=messages,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
        extra_body={"chat_template_kwargs": {"enable_thinking": settings.LLM_ENABLE_THINKING}},
        **kwargs,
    )
    usage = getattr(response, "usage", None)
    logger.info(
        "LLM %s: frames=%d prompt_tokens=%s completion_tokens=%s seconds=%.1f",
        label,
        frame_count,
        getattr(usage, "prompt_tokens", "?"),
        getattr(usage, "completion_tokens", "?"),
        time.monotonic() - started,
    )
    return response.choices[0].message.content or ""


async def analyze_window(
    frames: List[Dict[str, Any]],
    start: float,
    end: float,
    previous_quips: Optional[List[str]] = None,
    label: str = "window",
) -> List[Dict[str, Any]]:
    """One LLM call for one window. Retries once with a JSON nudge if the reply is unusable.

    Raises on transport errors/timeouts (no retry: a slow model would double the wait) and on a second bad reply.
    """
    if llm_client is None:
        raise RuntimeError("openai package is not installed")
    previous_quips = previous_quips or []
    last_error: Optional[Exception] = None
    for attempt in range(2):
        messages = build_messages(frames, start, end, previous_quips, nudge=attempt > 0)
        reply = await _call(messages, len(frames), label)
        try:
            objects = parse_model_objects(reply)
            quips = extract_quips(objects)
            seen = next((o["seen"] for o in objects if "seen" in o), None)
            logger.debug("%s seen: %s", label, str(seen)[:300])
            return quips
        except LLMOutputError as exc:
            last_error = exc
            logger.warning("%s: unusable reply on attempt %d (%s); full reply: %r", label, attempt + 1, exc, reply[:2000])
    raise LLMOutputError(f"{label}: model returned no usable JSON after retry") from last_error
