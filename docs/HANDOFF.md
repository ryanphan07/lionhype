# Handoff: session 11 (robustness before long clips)

## 1. Done
- llm.py: `max_retries=0` (N2). jobs.py/config: `JOB_STALE_SECONDS` 1800, `has_active()` fails stale jobs (N6).
- pipeline.py: `friendly_error` safe categorized job errors (N4); commentary.py raises `LLMOutputError` for "no usable commentary".
- commentary.py/tts.py: `schedule_quips(quips, video_duration)` drops quips shifted past the end; `tts.remove_clip_file` deletes dropped clips (N10).
- App.jsx: polling fallback after WebSocket reconnects are exhausted (N1).
- tests: hermetic upload-lock test (N5), new tests for each item. Docs (TASKS, AUDIT, STATE, README, CONVENTIONS) updated after each commit.

## 2. Decisions and deviations
- N7 (`seen` continuity) not done: it changes `analyze_window`'s return shape. Refresh-resume part of N1 not done (needs a re-select-video flow).
- D4 (long-job strategy), LICENSE, Docker deletion, CLAUDE.md update are yours; not touched.

## 3. Results
- pytest backend/tests -q: 101 passed (3 s). Frontend lint clean, build ok. Fresh venv and fresh `npm ci` both verified.

## 4. Not verified, needs manual testing
1. Polling fallback in a browser: start a job, stop and restart nothing but kill the WS (e.g. restart uvicorn mid-job gives 404 message; briefly block the port instead).
2. Live re-check of timing fixes and playback with llama-server up (session 8).
3. Error messages with llama-server stopped: expect "The AI model is not reachable...".

## 5. Open issues and risks
- commentary.py window loop: all-or-nothing job (D4). TTS phase reports progress only at 70/90, so JOB_STALE_SECONDS could cut a 30+ min TTS stage.
- No frontend test runner. VideoPlayer ducking/jitter (F14).

## 6. Suggested next session
Decide D4, restart services, run session 8 (real clips, short then 10+ min), throughput experiments, then GIF, LICENSE, tag v0.1.0.
