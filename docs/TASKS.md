# LionHype tasks (2026-10-28, after audit 3)

Goal: a credible, honest, demoable resume MVP, shipped fast. Items are tagged with audit ids (`docs/AUDIT.md`). Do not add features beyond this list without asking.

## Decisions (see `docs/DECISIONS.md`)
1. Clip length: long clips (10+ min) are a goal; limits become settings (session 7b).
2. Models: develop on the 9B, use the 35B-A3B for real runs.
3. TTS fallback: owner unsure; keep edge-tts + text-only fallback until v0.1.0, then consider an offline provider (D3).

## Session 11: robustness before long clips (SHOULD-FIX, all small, do next)
- [x] N2: `AsyncOpenAI(max_retries=0)`; a window now fails when its own timeout fires (tested: client setting).
- [x] N5: that test uses `fake_ai`; suite back to about 3 s.
- [x] N6: `has_active()` fails jobs with no progress update for `JOB_STALE_SECONDS` (1800) so uploads unblock (tested with a fake clock). Note: the TTS phase only reports at 70 and 90 percent, so a very slow TTS stage over 30 min would be cut off; per-clip progress is a possible follow-up.
- [ ] N4: map failures to safe messages ("The AI model is not reachable", "The model returned unusable output", "The video could not be processed"); log the detail server-side; test each category.
- [ ] N1: frontend: when the WebSocket is lost, fall back to polling `GET /api/jobs/{id}` every 5 s until terminal (no 5-try limit); keep `job_id` in sessionStorage so a refresh can resume status (the video blob needs re-selecting; show that).
- [ ] N10: clamp shifted timestamps to the video duration; delete the mp3 of a dropped quip.
- [ ] N7 (optional, prompt-level): pass the last 2-3 `seen` summaries to the next window to reduce repetition on long clips.

## Decision before long-clip testing: D4 (see DECISIONS.md)
- [ ] Owner: pick the long-job strategy (A keep all-or-nothing, B skip failed windows, C progressive results). Recommendation: B now (small), C after v0.1.0.

## Session 7: spoken-line timing (BLOCKS-DEMO) - DONE in code 2026-10-28, live re-check pending
- [x] F1: stop cutting quips mid-sentence. Remove the word truncation in `finalize_timeline` (`commentary.py:35-38`); rely on the prompt limit and `schedule_quips`. Update the tests that assert truncation.
- [x] F2 (gap 4.5, 3 quips per window, 10 words; `QUIP_WORDS_PER_SECOND` removed; `TTS_RATE` left at +10%, try +20% by ear): recalibrate with measured speech (8 words = 4.5 s, about 1.8 words/s). Suggested: `MIN_QUIP_GAP_SEC` 4.5, `QUIP_WORDS_PER_SECOND` 1.8 (if still used), `MAX_QUIPS_PER_WINDOW` 3, prompt "at most 10 words" and "at least 4.5 seconds apart". Consider `TTS_RATE=+20%`. Check by ear that +20% is still pleasant.
- [x] F3: round timestamps to 2 decimals after shifting (`schedule_quips`), round for display in VideoPlayer.
- [ ] Restart uvicorn (running process predates session 6 and the edge-tts upgrade).

## Session 7b: long clips (owner goal: 10+ minutes) - limits DONE, rest open
- [x] `MAX_VIDEO_SECONDS` 1800 and `MAX_UPLOAD_MB` 2048 as settings, tested.
- [x] ETA in the analyzing message ("part i of n, about m min left") from the running average window time (`commentary.analyzing_message`).
- [ ] Decide failure policy for one bad window in a long job: retry the window, or skip it with a logged gap, instead of failing after 40 minutes (changes the "fail loud" rule: ask first).
- [ ] After session 11 and D4: run one 10+ minute clip on the 9B model and record windows, total time, memory, and whether the WebSocket, blob playback and TTS count (about 100+ clips) hold up. Repeat on the 35B-A3B.
- [ ] Consider reading upload in chunks with early size rejection; large bodies are currently spooled to disk by Starlette before the check.

## Session 8: real footage, in the browser (BLOCKS-DEMO)
- [ ] Run 3 real clips (e.g. `hoco2026_7star.mp4`, `shorter_test.mp4`, one more) through the UI. Record per clip: duration, window count, seconds per window, quips kept vs shifted vs dropped, subjective commentary quality.
- [ ] Check in the browser: progress bar and "Analyzing part i of n", audio starts in sync, no overlap, seek backward and forward, pause/resume, autoplay-blocked notice, error path (stop llama-server mid-job), no-audio path (disconnect network).
- [ ] Tune prompt, `FRAME_WIDTH`, `FRAMES_PER_WINDOW`, `WINDOW_SECONDS`. Restart after prompt edits (cached).
- [ ] Re-run the F1-F3 live check (llama-server was down at the end of this session): 10 s clip, confirm no cut lines and fewer drops.
- [ ] Record the demo GIF (20-30 s clip, sound shown via captions or a short linked mp4).

## Session 9: hygiene (SHOULD-FIX, small)
- [x] F4: at startup, delete everything in `uploads/videos` and `uploads/audio` (the in-memory store is empty then). Test with a temp dir.
- [x] F5 (video deleted right after a successful job): delete the source video as soon as frames are sampled (end of the analyzing phase) or on completion.
- [x] F6 (409 "Another clip is still being processed"): allow one running job at a time; extra uploads get a clear 409/429 message (or queue). Test.
- [x] F8: `requirements.txt` pinned to the installed versions, `requirements-dev.txt` added (pytest, anyio), `pytest-asyncio` dropped. Also added `websockets` (F18). Still to do: verify once in a brand-new venv.
- [ ] F9: delete `docker-compose.yml` and the Dockerfiles, or keep and label "untested, not part of the MVP". Recommendation: delete (ask first).
- [x] `npm audit fix` (0 vulnerabilities), `.gitignore` `spike_frames/`, deleted `frontend/README.md` boilerplate, removed unused `TTS_PROVIDER`, `LLM_MODEL` default now `local`, `LLM_TEMPERATURE` setting.
- [x] F11: `vision_spike.py` imports the shared `motion_box`.

## Session 10: ship (docs and GIF)
- [ ] README at the repo root (moved to the root 2026-10-28; links still to verify): what it is, GIF, architecture diagram, prerequisites (Python 3.12, Node 20+, llama-server + model + mmproj), 5-command quickstart, route list, config table, known limitations (60 s clips, minutes of processing, needs internet for TTS, single user, no auth), honest "how it was tested".
- [ ] Add a LICENSE (owner picks: MIT is the usual choice for a portfolio repo). Final pass on STATE/TASKS. Tag `v0.1.0`.
- [ ] Resume bullet draft (only claims the repo proves): local multimodal LLM windowed analysis with motion-based crop, time-synced TTS with server-side overlap scheduling, WebSocket job progress, 95+ tests.

## Polish, only if time remains
- [x] F14 (partly): audio stops when the video ends. Still open: user volume change while ducked is overwritten; `timeupdate` jitter (up to 250 ms).
- [ ] F13: warn in the UI when the browser cannot play the uploaded format, or restrict to `.mp4`/`.mov`.
- [x] F15 (partly): renamed `test_commentary.py`, removed the unused `conftest.py` fixture. Still open: moving-subject fixture for `motion_box`, 2-3 Vitest tests for the VideoPlayer queue.
- [ ] Show dropped-quip text as "(skipped, overlapped)" instead of silently removing it (changes result shape: ask first).

## Throughput experiments for long clips (N8, measure before choosing)
- [ ] On one 60 s clip, record seconds per window for: baseline; `FRAME_WIDTH` 640; `FRAMES_PER_WINDOW` 4; `WINDOW_SECONDS` 20; each on the 9B and the 35B-A3B. Pick defaults for the 35B from the numbers.
- [ ] Optional: `llama-server -np 2` with two windows in flight (drops the previous-quips dependency; needs a quality check).

## Out of scope (do not start)
Auth, persistence/database, multi-user queue, S3/presigned uploads, Docker, deployment, offline TTS provider, MCP server, timeline analytics dashboard.
