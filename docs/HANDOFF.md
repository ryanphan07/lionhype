# Handoff: audit 3 (2026-10-28)

## 1. Done
- docs/AUDIT.md: new audit 3 on top (baseline, goal check, findings N1-N11, verified-good list, plan); audits 1-2 kept as history.
- docs/TASKS.md: new session 11 (robustness before long clips), D4 decision item, throughput experiments, reordered pointers.
- docs/DECISIONS.md: D4 (long-job strategy: A all-or-nothing, B skip failed windows, C progressive results; recommends B then C).
- docs/STATE.md, README.md: long-clip gaps note, DECISIONS link. No source code changed.

## 2. Decisions and deviations
- Audit only: found bugs are listed, not fixed. CLAUDE.md not edited (still says 90 s and the 35B only).
- No live run: llama-server, uvicorn and Vite were stopped.

## 3. Results
- pytest backend/tests -q: 95 passed (10.5 s). npm run lint clean, build ok, npm audit 0.

## 4. Not verified, needs manual testing
1. Live re-check of the F1-F3 timing fixes and browser playback (progress, sync, seek, pause, error paths).
2. Fresh-venv install from requirements.txt.
3. A 10+ minute clip on 9B and 35B.

## 5. Open issues and risks
- llm.py:18-22 SDK max_retries=2: a hung window can take 15 min to fail.
- App.jsx:104-115 gives up after about 25 s of WS loss, no polling fallback.
- commentary.py:83-135 all-or-nothing job (D4).
- jobs.py has_active can wedge uploads with 409.
- test_api.py last test uses the real network (7.7 s).

## 6. Suggested next session
Session 11 in TASKS.md (N2, N5, N6, N4, N1, N10), decide D4, then session 8 on real footage.
