# Handoff: sessions 7, 7b, 9 (+ decisions)

## 1. Done
- docs/DECISIONS.md (new): D1 long clips (10+ min) are a goal, D2 9B for dev / 35B-A3B for real runs, D3 TTS fallback (deferred; recommendation: edge-tts + text-only until v0.1.0, then offline Piper).
- commentary.py/config/prompt: no more quip truncation, `MIN_QUIP_GAP_SEC` 4.5, 3 quips/window, 10 words, timestamps rounded; `QUIP_WORDS_PER_SECOND` removed. `analyzing_message` adds a time-left estimate.
- config/video_processor: `MAX_VIDEO_SECONDS` 1800, `MAX_UPLOAD_MB` 2048 (settings).
- pipeline/main/jobs: startup sweep of uploads, source video deleted after success, 409 when a job is running.
- requirements.txt pinned + `websockets` added (fresh installs had no WS library: /ws returned 404); requirements-dev.txt; npm audit fix; LLM_TEMPERATURE; removed TTS_PROVIDER; spike script uses shared motion_box; VideoPlayer stops audio on `ended`; test_main.py renamed test_commentary.py. Docs updated after each change.

## 2. Decisions and deviations
- Docker files not deleted (needs your OK). frontend/README.md (Vite boilerplate) deleted.
- LICENSE not added (your choice). Per-window failure policy for long jobs left open (changes "fail loud").
- You moved README to the repo root; I edited it there.

## 3. Results
- pytest backend/tests -q: 95 passed. npm run lint clean, build ok, npm audit 0 vulnerabilities.

## 4. Not verified, needs manual testing
1. Live re-check of F1-F3: llama-server was down. Restart uvicorn (new code, websockets) and run a clip in the browser.
2. A 10+ minute clip on 9B, then 35B (time, memory, ~100 TTS clips, ETA text).
3. Fresh-venv install from requirements.txt and the README quickstart.

## 5. Open issues and risks
- commentary.py window loop: one failed window fails a possibly 40-minute job; jobs are lost on restart.
- VideoPlayer.jsx: volume-ducking overwrite, 250 ms timeupdate jitter.
- docker-compose.yml, Dockerfiles stale. Upload body is spooled before the size check (main.py).

## 6. Suggested next session
Session 8 in TASKS.md: real clips in the browser, tune prompt/TTS_RATE (try +20%), record the GIF; then LICENSE and tag v0.1.0.
