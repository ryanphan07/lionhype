# Handoff: audit 4 (2026-10-28)

## 1. Done
- docs/AUDIT.md: audit 4 on top (baseline, goal check, findings M1-M7); audits 1-3 kept as history.
- docs/TASKS.md: new session 12 (M1-M5); docs/STATE.md: live-server verification note; README.md: troubleshooting section.
- No source code changed.

## 2. Decisions and deviations
- Audit only; defects are listed, not fixed. D4, LICENSE, Docker deletion, CLAUDE.md remain yours.
- A first probe falsely suggested the server loop blocks; cause was my harness leaving the server's stdout pipe unread (documented as M5 Windows console note, not a code bug).

## 3. Results
- pytest backend/tests -q: 101 passed. Lint clean, build ok, npm audit 0.
- Real uvicorn with LLM down: job fails in about 4 s with "The AI model is not reachable...", lock released, next upload accepted.

## 4. Not verified, needs manual testing
1. Live LLM + TTS + browser run (timing fixes, playback, polling fallback). llama-server, uvicorn, Vite were stopped.
2. 10+ minute clip on 9B and 35B.

## 5. Open issues and risks
- pipeline.py `sweep_uploads`: deletes everything in `<UPLOAD_DIR>/videos|audio`; a custom UPLOAD_DIR such as your home folder would match Windows `Videos` (M1).
- tts.py: no retry; 100-500 edge-tts requests on a long clip (M2).
- pipeline.py `friendly_error` mislabels HTTP errors (M3); jobs.py stale job not cancelled (M4).

## 6. Suggested next session
Session 12 in TASKS.md (M1 first), decide D4, then the live session 8 and ship (GIF, LICENSE, tag).
