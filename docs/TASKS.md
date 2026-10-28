# LionHype tasks (2026-10-28)

Goal: a credible, honest, demoable resume MVP, shipped fast. Items are tagged with audit ids (`docs/AUDIT.md`). Do not add features beyond this list without asking.

## Decisions needed from the owner
1. Clip limit: 60 s (code) or 90 s (goal text)? At 44.7 s per 10 s window on the 9B model, 90 s is about 7 minutes of waiting. Recommendation: keep 60, say "up to 60 s" everywhere, demo with a 20-30 s clip.
2. Demo model: Qwen3.5-9B (running now) or Qwen3.6-35B-A3B (named in CLAUDE.md)? Pick one, state it in the README, update CLAUDE.md.
3. TTS risk (F7): accept edge-tts as the only provider and rely on the honest text-only fallback plus a pre-recorded GIF with sound, or approve an offline TTS provider as a new feature (not recommended before the first resume send-out).

## Session 7: spoken-line timing (BLOCKS-DEMO, about 1 session)
- [ ] F1: stop cutting quips mid-sentence. Remove the word truncation in `finalize_timeline` (`commentary.py:35-38`); rely on the prompt limit and `schedule_quips`. Update the tests that assert truncation.
- [ ] F2: recalibrate with measured speech (8 words = 4.5 s, about 1.8 words/s). Suggested: `MIN_QUIP_GAP_SEC` 4.5, `QUIP_WORDS_PER_SECOND` 1.8 (if still used), `MAX_QUIPS_PER_WINDOW` 3, prompt "at most 10 words" and "at least 4.5 seconds apart". Consider `TTS_RATE=+20%`. Check by ear that +20% is still pleasant.
- [ ] F3: round timestamps to 2 decimals after shifting (`schedule_quips`), round for display in VideoPlayer.
- [ ] Restart uvicorn (running process predates session 6 and the edge-tts upgrade).

## Session 8: real footage, in the browser (BLOCKS-DEMO)
- [ ] Run 3 real clips (e.g. `hoco2026_7star.mp4`, `shorter_test.mp4`, one more) through the UI. Record per clip: duration, window count, seconds per window, quips kept vs shifted vs dropped, subjective commentary quality.
- [ ] Check in the browser: progress bar and "Analyzing part i of n", audio starts in sync, no overlap, seek backward and forward, pause/resume, autoplay-blocked notice, error path (stop llama-server mid-job), no-audio path (disconnect network).
- [ ] Tune prompt, `FRAME_WIDTH`, `FRAMES_PER_WINDOW`, `WINDOW_SECONDS`. Restart after prompt edits (cached).
- [ ] Record the demo GIF (20-30 s clip, sound shown via captions or a short linked mp4).

## Session 9: hygiene (SHOULD-FIX, small)
- [ ] F4: at startup, delete everything in `uploads/videos` and `uploads/audio` (the in-memory store is empty then). Test with a temp dir.
- [ ] F5: delete the source video as soon as frames are sampled (end of the analyzing phase) or on completion.
- [ ] F6: allow one running job at a time; extra uploads get a clear 409/429 message (or queue). Test.
- [ ] F8: pin `requirements.txt` to the installed versions, split `requirements-dev.txt` (pytest), drop `pytest-asyncio`. Verify with a fresh venv and the README quickstart.
- [ ] F9: delete `docker-compose.yml` and the Dockerfiles, or keep and label "untested, not part of the MVP". Recommendation: delete (ask first).
- [ ] `npm audit fix` (follow-redirects), `.gitignore` `spike_frames/`, delete `frontend/README.md` boilerplate, remove unused `TTS_PROVIDER`, rename `LLM_MODEL` default to the real model name, make temperature a setting.
- [ ] F11: make `vision_spike.py` import `motion_box` from `app.services.video_processor`, or delete the script once tuning is done.

## Session 10: ship (docs and GIF)
- [ ] README at the repo root (`git mv docs/README.md README.md` and fix links): what it is, GIF, architecture diagram, prerequisites (Python 3.12, Node 20+, llama-server + model + mmproj), 5-command quickstart, route list, config table, known limitations (60 s clips, minutes of processing, needs internet for TTS, single user, no auth), honest "how it was tested".
- [ ] Add a LICENSE. Final pass on STATE/TASKS. Tag `v0.1.0`.
- [ ] Resume bullet draft (only claims the repo proves): local multimodal LLM windowed analysis with motion-based crop, time-synced TTS with server-side overlap scheduling, WebSocket job progress, 92+ tests.

## Polish, only if time remains
- [ ] F14: stop audio when the video ends; do not overwrite a user volume change while ducked; use `requestVideoFrameCallback` or a 100 ms timer for tighter sync.
- [ ] F13: warn in the UI when the browser cannot play the uploaded format, or restrict to `.mp4`/`.mov`.
- [ ] F15: rename `test_main.py` to `test_commentary.py`, remove the unused `conftest.py` fixture, add a moving-subject fixture for `motion_box`, add 2-3 Vitest tests for the VideoPlayer queue.
- [ ] Show dropped-quip text as "(skipped, overlapped)" instead of silently removing it (changes result shape: ask first).

## Out of scope (do not start)
Auth, persistence/database, multi-user queue, S3/presigned uploads, Docker, deployment, offline TTS provider, MCP server, timeline analytics dashboard.
