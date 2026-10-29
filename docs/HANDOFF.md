# Handoff: session 15 multi-object JSON reply (2026-10-28)

## 1. Done
- backend/app/services/llm.py: `parse_model_objects` collects every top-level JSON object (think/fences stripped, prose skipped); `extract_quips` uses the first object with a `quips` list, else bare `{"t","text"}` objects (the prompt's keys); seen-only still raises, one retry kept. Unusable replies are logged in full (2000-char cap) at WARNING.
- `LLM_JSON_SCHEMA` (config.py, .env.example): sends `response_format` json_schema (seen + quips[t,text], maxItems = MAX_QUIPS_PER_WINDOW). Default true.
- frontend/src/App.jsx: no stale status message after "error".
- tests/test_vision.py: 13 new tests (130 total). Docs: README, STATE, TASKS, BRIEFING, CONVENTIONS, .env.example.
- Commits: parser, frontend, schema feature, then schema default + docs.

## 2. Decisions and deviations
- Live check (hoco_40s.mp4 from Downloads, first window, 6 frames, 2917 prompt tokens): llama-server accepted the schema; valid quips every time. Schema on: 41.2 s cold, 12.5 s warm; off: 17.5 s warm. Not slower, so default true (the ~54 s baseline included cold cache).
- Kept `parse_model_json` (first object) for compatibility; the pipeline no longer uses it.
- Wrote files with LF to match the repo; `pytest` must run from backend/venv (system Python fails test_measure_duration_real_mp3, also on the earlier commit).

## 3. Results
- pytest 130 passed (venv); eslint clean; vite build OK.

## 4. Not verified, needs manual testing
- A full browser/benchmark job with the fix (window 2/4 of hoco 40 s is the failing case); only one window was run live.
- Other servers/models may reject `response_format`: then set LLM_JSON_SCHEMA=false.
- Everything from session 14 (sync, seek, audio, GIF).

## 5. Open issues and risks
- llm.py `_call`: a server HTTP 400 on response_format would surface as a model error, with no auto-fallback.
- 12 s extracting step unexplained; long clips and 35B unmeasured.

## 6. Suggested next session
Re-run `backend/scripts/benchmark.py` on hoco_40s, then owner browser check, GIF, tag v0.1.0.
