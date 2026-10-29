# Handoff: session 16 (v0.1.0 NOT tagged yet: demo assets pending)

## 1. Done
- CLAUDE.md: scope line now says "items in docs/TASKS.md 'Before v0.1.0'" (only change).
- docs/BENCHMARKS.md: new 2026-10-28 20:41 section (old kept), notes LLM_JSON_SCHEMA=true and 0 retries.
- README.md: new benchmark table and numbers (251 s, ~6x), browser-check line, "(no audio)" troubleshooting entry.
- docs/AUDIT.md (M1-M4 FIXED), OWNER_TODO, STATE (maturity, new verified section), TASKS, BRIEFING refreshed.

## 2. Decisions and deviations
- Step 3 (demo.mp4/demo.gif) NOT done: the prompt's recording path was a placeholder and you never gave one. The only recent captures are terminal recordings (Vite console), not the app. ffmpeg is installed but not on this shell's PATH:
  C:\Users\ryanp\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin
- README Demo section still has the TODO and <VIDEO_URL>; the Status line still says the GIF is not recorded. Tag v0.1.0 held so the tag includes the demo.
- Step 5 skipped: parse_model_json is used by tests/test_audio.py and tests/test_vision.py.
- Browser check recorded as "no problems seen" per your answer.
- First benchmark attempt hit a down llama-server; that section was discarded, not committed. Benchmark ran hoco_40s and shorter_test only (no warm repeat, no hoco2026.MOV). Earlier uvicorn stopped; benchmark log in %TEMP%\lionhype_bench.log.
- TASKS "Before v0.1.0": demo and tag items left open; the browser-check item was removed (done).

## 3. Results
pytest 130 passed; eslint clean; vite build OK. Benchmark: hoco_40s 250.8 s, 6 quips, 0 retries; shorter_test 66.1 s.

## 4. Not verified
- Demo assets. Polling fallback, error paths, commentary quality by ear.

## 5. Open issues
- README.md Demo section and Status line (line 5); docs/TASKS.md Before v0.1.0.

## 6. Suggested next session
Finish v0.1.0: give the app recording path; make docs/demo.mp4 (720p, crf 28, AAC, <=10 MB) and docs/demo.gif (10-15 s, 640 px, 10 fps, <=8 MB); update README Demo/Status; `git tag -a v0.1.0 -m "LionHype v0.1.0"`.
Then v0.1.1: HTTP 400 fallback for response_format, sequential crop sampling (12 s extract), 35B and long-clip measurements.
