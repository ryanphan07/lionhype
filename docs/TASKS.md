# Maneframe roadmap (v0.1.0 shipped 2026-10-28)

Design decisions are in `docs/DECISIONS.md`; what is implemented is in `docs/STATE.md`.

## Done
- Upload validation, job store, WebSocket progress, background pipeline with cleanup of job files.
- Motion-based crop and windowed frame sampling with OpenCV.
- Vision-LLM commentary through an OpenAI-compatible endpoint (llama-server, multimodal), with tolerant JSON parsing and constrained output.
- edge-tts synthesis with retries, and server-side scheduling so audio never overlaps.
- React player: blob-URL video, quip queue, ducking while a clip plays, seek and pause handling.
- Limits as settings, ETA in progress messages, safety and robustness fixes.
- Benchmark script and results (`docs/BENCHMARKS.md`), browser playback check, demo GIF and video.

## Direction
The goal is a better product for real users: lion dance teams turning performance clips into shareable posts. Honesty rules stay: no canned LLM text, no fake audio.

## Phase 1: shareable output and commentary quality
- mp4 export: the video with the commentary audio mixed in and captions burned in.
- Commentary quality: lion dance domain vocabulary in the prompt, few-shot examples, `seen` continuity across windows, a style option, and a small eval set to compare prompts and models.

## Phase 2: speed and robustness
- 9B vs 35B-A3B throughput table (`FRAME_WIDTH` 640, `FRAMES_PER_WINDOW` 4, `WINDOW_SECONDS` 20, optionally `llama-server -np 2`).
- Sequential crop sampling instead of seeking.
- Progressive results (D4 option C).
- HEVC/.MOV transcode so the browser can play more phone footage.
- Smaller items: warn in the UI when the browser cannot play the format; Vitest tests for the VideoPlayer queue; show dropped quips as skipped; keep the volume setting while a clip ducks the video; offline TTS provider behind `TTS_PROVIDER` (D3).

## Phase 3: distribution (undecided)
Local packaging versus a hosted service.

## Out of scope
Auth, persistence or a database, a multi-user queue, S3 or presigned uploads, Docker, deployment, an MCP server, an analytics dashboard.
