# Handoff: session 14 benchmark and docs (2026-10-28)

## 1. Done
- backend/scripts/benchmark.py + tests/test_benchmark.py (5 tests, no network): uploads clips, polls every 2 s, parses the backend log per job ("Created job" to next), overlap check, appends a dated section to docs/BENCHMARKS.md. `--warm-first` repeats clip 1.
- Ran it (docs/BENCHMARKS.md): shorter_test cold 124 s / warm 50 s; hoco_40s 299 s, 7 quips all with audio, 27.5 s spoken, 0 overlaps/shifts/drops/TTS failures; hoco2026.MOV rejected (6 GB > 2048 MB cap).
- README: Benchmarks table, Demo section (TODO gif + <VIDEO_URL>), "How it was tested", measured limitations; fixed stale TTS_CONCURRENCY default (4 -> 1) in the config table. Test count 117 and measured speed in CONVENTIONS, STATE, DECISIONS, BRIEFING, TASKS (pruned), OWNER_TODO.

## 2. Decisions and deviations
- Port 8000 was held by a uvicorn I did not start (PID 29212), so I ran mine on 8001. It had stopped listening by the end; I did not kill it, cause unknown.
- The "windows" column is LLM calls including retries (renamed in header). Server run from backend/ with no .env (defaults); the log and output files were moved to %TEMP%, not committed.
- LICENSE already says "Ryan Phan". No source, settings or prompt changed.

## 3. Results
- pytest 117 passed; eslint clean; vite build OK.

## 4. Not verified, needs manual testing
- Browser playback sync, seek, pause, error paths; listening to the audio and reading the quips; whether commentary is funny/accurate; GIF and video link.

## 5. Open issues and risks
- 3 of 9 LLM calls returned unusable JSON (two objects or fenced without `quips`) and were retried, ~50 s each (llm.py parse path).
- Constant 12.0 s from extracting to analyzing in all runs: unexplained.
- Over-2 GB/long clips and 35B model unmeasured.

## 6. Suggested next session
Owner eye/ear check in the browser, record GIF, fill README TODOs, tag v0.1.0; then (after release) fix the double-JSON reply.
