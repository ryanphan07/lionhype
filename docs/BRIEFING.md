# Briefing for the planning chat

Paste this file (plus the files listed in "What to share") into the planning chat. The chat cannot see the repo. Last updated 2026-10-28 after audit 4. Claude Code (the coding agent) works one scoped session at a time on the repo and reads `CLAUDE.md`; the owner relays prompts and results.

## The project
LionHype turns a lion dance video into humorous, time-synced AI commentary with spoken audio. FastAPI backend (OpenCV frames with a motion-based crop, a local multimodal LLM through an OpenAI-compatible llama-server, edge-tts for speech) and a React/Vite frontend with WebSocket progress. Runs natively on Windows, no Docker. LLM: Qwen3.5-9B while developing, Qwen3.6-35B-A3B for real runs.

## Owner goals and constraints
- This is the last project going on the owner's resume before recruiting; speed matters. Goal: a credible, demoable, **honest** MVP, not a finished product.
- Must: upload a clip, see real progress, get real vision-LLM commentary played in sync with non-overlapping speech, run locally in a few commands, clean README, demo GIF.
- New goal (D1): long clips, 10+ minutes, eventually. Today's limits: 30 min and 2 GB (settings).
- No features beyond `docs/AUDIT.md` and `docs/TASKS.md` without asking. Never push (the owner pushes). One logical change per commit; tests before commit.
- Honesty rule: no canned LLM text, no fake audio. Failures are shown, not hidden.

## State (2026-10-28)
- Implemented and tested (117 backend tests, fresh venv and `npm ci` verified, lint and build clean, 0 npm vulnerabilities): upload validation, job API (`POST /api/upload`, `GET /api/jobs/{id}`, `WS /ws/analyze/{id}`), windowed vision pipeline, TTS with measured durations, server-side overlap scheduling, categorized safe error messages, stale-job lock, startup upload sweep, polling fallback in the browser, time-left estimate.
- Verified live (session 14, docs/BENCHMARKS.md): 3 accepted real jobs completed on the 9B with no audio overlap and no TTS failures; a 40 s clip took 299 s (7 quips, 27.5 s spoken); about 3000 prompt tokens per call; real edge-tts works with edge-tts 7.3.1. Verified on a real server with the LLM down: the job fails in about 4 s with a clear message.
- **Not verified:** browser behavior (progress, sync, seek, pause, polling), listening to the commentary and audio, any run over 40 s, 35B throughput.
- **Session 14 findings (docs/BENCHMARKS.md):** about 1 in 3 model calls returns unusable JSON (two objects, or fenced without `quips`) and is retried, which adds about 50 s each; the 12 s extracting-to-analyzing step is unexplained; the 6 GB test clip is over the 2 GB upload cap.
- Measured cost: about 7x real time on the 9B (40 s clip = 299 s); about 1 in 3 model calls needed the JSON retry. The 327 s test clip was 6 GB and hit the 2 GB upload limit. 10-minute runs untested.

## Decisions
- Made: D1 long clips are a goal; D2 9B for dev, 35B for real runs; timing constants recalibrated to real speech (4.5 s gap, 3 quips and 10 words per window).
- **Decided 2026-10-28:** D4 = A (all-or-nothing for v0.1.0; B/C after release), MIT license, Docker files deleted. Session 12 (M1-M5) done. D3 TTS fallback is deferred (edge-tts is an unofficial endpoint; an offline voice is possible later). Session 13 (TTS hardening: retry NoAudioReceived, TTS_CONCURRENCY=1 with stagger, duration re-check, failure diagnostics, `backend/scripts/tts_check.py`) done, motivated by "No audio was received" with two clips in parallel. Remaining: live session, GIF, tag.

## Roadmap (details in `docs/TASKS.md`, owner actions in `docs/OWNER_TODO.md`)
1. Session 12 (done): M1 sweep deletes only app-created files, M2 TTS retry, M3 LLM HTTP error text, M4 stale job tasks cancelled, M5 README note.
2. Owner decides D4; Claude Code implements it (B is small; C is a larger API and player change).
3. Live session (owner): checklist in `OWNER_TODO.md` section C; results go back to the chat and to Claude Code.
4. Tune the prompt and settings from the measurements (frames, width, window length, TTS rate); pick 35B defaults.
5. Ship: GIF, LICENSE, final README read, tag v0.1.0, resume bullets.

## Ready-to-paste Claude Code session prompts
**Session 12:** "Session 12: safety and long-clip hardening. Read CLAUDE.md, docs/HANDOFF.md, docs/TASKS.md (Session 12), docs/AUDIT.md (audit 4, M1-M4). Implement M1 (sweep only deletes job-id-prefixed videos and 32-hex audio folders; test that unrelated files survive), M2 (TTS_RETRIES default 1, short delay, per-clip progress), M3 (HTTP status errors say 'The AI model rejected the request'), M4 (cancel the pipeline task of a stale job). Update STATE/TASKS/AUDIT/README per CONVENTIONS, refresh docs/BRIEFING.md, then the handoff."

**D4 = B:** "Implement DECISIONS D4 option B: after one retry a failed window is skipped and logged; the result lists skipped time ranges and the UI says 'skipped n of m parts'; a job where every window fails still errors. Tests for partial and total failure. Update docs, BRIEFING and the handoff."

**Results session:** "Here are my live-run numbers: <table>. Tune defaults in config, .env.example and the prompt accordingly, and record the measurements in docs/STATE.md and docs/DECISIONS.md."

## Resume-claim guardrails (only claim what the repo proves)
Supported: local multimodal LLM pipeline with motion-based cropping and windowed analysis; WebSocket job progress; server-side scheduling so speech never overlaps, using measured clip durations; honest failure handling (no fabricated output); 117 automated tests. Not yet supported: anything about long-clip performance beyond 40 s, commentary quality metrics, or live demo robustness until the live session is done.

## What to share with the planning chat
Give: `docs/BRIEFING.md` (this file), `docs/OWNER_TODO.md`, `docs/TASKS.md`, `docs/DECISIONS.md`, `docs/HANDOFF.md`. Add `docs/AUDIT.md` only when asking about specific findings (it is long; the top "audit 4" section is enough). Do not share CLAUDE.md, CONVENTIONS.md, STATE.md, README.md or code: the chat does not need them and they go stale; ask Claude Code instead. After each Claude Code session, give the chat the new `docs/HANDOFF.md` (and `docs/BRIEFING.md` if it changed).
