# Handoff: audit session (2026-10-28)

## 1. Done
- docs/AUDIT.md: replaced with audit 2 (baseline, goal check, live run, findings F1-F17, status of every old finding).
- docs/STATE.md, docs/TASKS.md, docs/README.md: rewritten to match the code (old ones described removed code and a stale frontend/API).
- docs/CONVENTIONS.md: model in use, 60 vs 90 s note, timing section, test/verify dates.
- Environment: upgraded venv edge-tts 7.2.8 -> 7.3.1 via `pip install -r requirements.txt` (real TTS was 403ing).
- No source code changed.

## 2. Decisions and deviations
- The audit prompt was broad; I only edited docs and the venv. All defects are listed in TASKS, not fixed.
- Did not read or touch uploads/ (CLAUDE.md rule): its stale contents are reported from `ls` only.
- Kept README at docs/README.md; moving it to the repo root is a TASKS item.
- CLAUDE.md not edited (it names the 35B model; the running model is the 9B).

## 3. Results
- pytest backend/tests -q: 92 passed. npm run lint: clean. npm run build: ok. npm audit: 1 high (follow-redirects, transitive).
- Live in-process run (real llama-server 9B + real edge-tts, 10 s slideshow of spike frames): ok, 46 s.

## 4. Not verified, needs manual testing
1. Restart uvicorn (it predates session 6), run a real clip in the browser: progress, sync, seek, pause, error and no-audio paths.
2. Commentary quality on real motion (this audit used stills).
3. Fresh-venv install from requirements.txt (not done).

## 5. Open issues and risks
- commentary.py:35-38 truncates quips mid-sentence (reproduced live).
- config.py:24-25 and the prompt assume 2.5 words/s; measured 1.8, so lines get shifted or dropped.
- commentary.py:53-60 float noise in shifted timestamps shows in the UI (VideoPlayer.jsx:150).
- main.py:25 no startup sweep: backend/uploads holds about 130 MB of orphaned videos and 10-byte fake mp3 dirs.
- Edge-tts is an unofficial endpoint; demo needs a fallback plan.

## 6. Suggested next session
Session 7 in TASKS.md: fix F1-F3 (remove truncation, recalibrate gap/words/prompt, round timestamps), restart backend, then real-footage runs.
