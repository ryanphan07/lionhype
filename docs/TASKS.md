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

## Next (v0.1.1)
- Warn in the UI when the browser cannot play the uploaded format (`.avi`, some `.mov`).
- Throughput experiments on the 9B and 35B-A3B models: `FRAME_WIDTH` 640, `FRAMES_PER_WINDOW` 4, `WINDOW_SECONDS` 20, optionally `llama-server -np 2`.
- A few Vitest tests for the VideoPlayer queue.
- Show dropped quips as skipped; keep the volume setting while a clip ducks the video.

## Later
- Long clips (10+ minutes): skip a failed window after one retry and report the gap (D4 option B), progressive results (D4 option C), early size rejection, a one-line summary of earlier windows to avoid repeats.
- Offline TTS provider (for example Piper) behind a `TTS_PROVIDER` setting (D3).

## Out of scope
Auth, persistence or a database, a multi-user queue, S3 or presigned uploads, Docker, deployment, an MCP server, an analytics dashboard.
