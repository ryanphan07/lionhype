# LionHype tasks (2026-10-28, after session 16)

Owner-only items (decisions, live run, ship steps) are in `docs/OWNER_TODO.md`; the planning chat reads `docs/BRIEFING.md`.

Goal: a credible, honest, demoable resume MVP, shipped fast. Items are tagged with audit ids (`docs/AUDIT.md`). Do not add features beyond this list without asking.

## Decisions (see `docs/DECISIONS.md`)
1. Clip length: long clips (10+ min) are a goal; limits become settings (session 7b).
2. Models: develop on the 9B, use the 35B-A3B for real runs.
3. TTS fallback: owner unsure; keep edge-tts + text-only fallback until v0.1.0, then consider an offline provider (D3).

## Done (details in docs/STATE.md, docs/HANDOFF.md, git log)
Sessions 7, 7b (limits, ETA), 9 (hygiene), 11 (robustness), 12 (safety), 13 (TTS hardening) 14 (benchmark, docs), 15 (multi-object JSON reply: tolerant parser, constrained output) 16 (re-benchmark, README, docs) and 17 (demo GIF and video, v0.1.0 tag, 2026-10-28). Browser check done by the owner 2026-10-28, no problems. Benchmark results are in `docs/BENCHMARKS.md`.

## Before v0.1.0 (owner: see docs/OWNER_TODO.md)
- [ ] Tag `v0.1.0` (the owner pushes). Resume bullet: local multimodal LLM windowed analysis with motion-based crop, time-synced TTS with server-side overlap scheduling, WebSocket job progress, 130 tests, measured about 6x real time (40 s clip in 251 s) on a 9B model.

## After v0.1.0 (do not start before; ask first)
- Long clips (owner goal, 10+ min): D4 failure policy B/C, one 10+ minute run, upload chunking/early size rejection, `seen` summaries across windows (N7).
- Throughput experiments (N8): `FRAME_WIDTH` 640, `FRAMES_PER_WINDOW` 4, `WINDOW_SECONDS` 20 on 9B and 35B-A3B; optional `-np 2`.
- Polish: warn when the browser cannot play the format (F13), volume change while ducked, 2-3 Vitest tests for the VideoPlayer queue, show dropped quips as skipped.

## Out of scope (do not start)
Auth, persistence/database, multi-user queue, S3/presigned uploads, Docker (files removed), deployment, offline TTS provider, MCP server, timeline analytics dashboard.
