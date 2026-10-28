# Owner to-do (things only you can do)

Everything Claude Code can do on its own is in `docs/TASKS.md` (session 12 is next). This list is what is blocked on you, in order. Updated 2026-10-28.

## A. Decisions (1-3 settled in session 12: D4 = A, MIT, Docker files deleted)
1. **D4, long-job strategy** (`docs/DECISIONS.md`): A keep all-or-nothing, B skip a failed window after one retry and report the gap, C progressive results. Recommendation: B now, C after v0.1.0.
2. **LICENSE**: pick one (MIT is the usual choice for a portfolio repo) and the name to put on it.
3. **Docker files** (`docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`): delete them (recommended: stale, untested, not part of the MVP) or keep and label.
4. **Optional features**, default is no: N7 (pass the model's own scene summaries to the next window to reduce repeated jokes on long clips); resume after a page refresh (needs a "re-select the video" flow).
5. **TTS fallback** (D3): nothing to decide until after v0.1.0. If edge-tts breaks again, decide on an offline voice (Piper).

## B. Edit CLAUDE.md (Claude Code will not edit your instructions file)
- Replace "upload a clip (90s or less)" with "upload a clip (long clips, 10+ min, are a goal; limits are `MAX_VIDEO_SECONDS` 1800 and `MAX_UPLOAD_MB` 2048)".
- Change "The LLM is a local Qwen3.6-35B-A3B" to "The LLM is local llama-server: Qwen3.5-9B while developing, Qwen3.6-35B-A3B for real runs".
- Optionally add `docs/DECISIONS.md` and `docs/OWNER_TODO.md` to the reading list.

## C. Live session (needs llama-server, internet and a browser; nothing has been verified live since the timing fixes)
Start three terminals from the repo root:
```powershell
llama-server -m <model.gguf> --mmproj <mmproj-F16.gguf> -c 32768 -np 1 -ngl 99 --port 8080 --jinja
cd backend; venv\Scripts\Activate.ps1; uvicorn app.main:app --port 8000      # restart it: the old process predates sessions 6-11
cd frontend; npm run dev                                                        # http://localhost:5173
```
Then, and write the numbers down:
1. **Short clip (20-30 s)**: progress bar and "Analyzing part i of n, about m min left"; audio plays in sync; lines are complete and not cut; no overlap; seek back and forward; pause and resume. Check the backend log for "Shifting" and "Dropping" lines: how many per clip?
2. **By ear**: is `TTS_RATE=+10%` fine, or try `+20%` in `backend/.env`.
3. **Error paths**: stop llama-server mid-job (expect "The AI model is not reachable..."); block the network or edge-tts (expect the "audio unavailable" notice); restart uvicorn mid-job (expect "The server no longer has this job"); briefly drop the page's connection to see the polling fallback ("Live updates lost, checking the server...").
4. **Real clips**: `hoco2026_7star.mp4`, `shorter_test.mp4` and one more: record duration, seconds per window, quips kept/shifted/dropped, and your quality rating of the commentary.
5. **Long clip (10+ min)** after D4 is decided: total time, memory, whether the WebSocket, playback and 100+ TTS clips hold. Repeat on the 35B.
6. **Throughput table** on one 60 s clip, for the 9B and the 35B: baseline, `FRAME_WIDTH=640`, `FRAMES_PER_WINDOW=4`, `WINDOW_SECONDS=20`; seconds per window each.
Give the results (a short table is fine) to the planning chat and to the next Claude Code session.

## D. Ship
1. Record the demo GIF (20-30 s clip; show the progress bar and commentary; a GIF has no sound, so also link a short mp4 with audio or caption the lines).
2. Add the LICENSE file (after A2), put the GIF in `README.md`, do a final read of the README.
3. Tag `v0.1.0` and push (Claude Code never pushes).
4. Draft resume bullets with the planning chat from what the repo proves (see `docs/BRIEFING.md`).

## E. Housekeeping (optional)
- Root has `repomix-output.xml` and `.aider.chat.history.md` (ignored by git, large): delete them if you do not need them.
- `backend/uploads/` is swept at server start; the sweep now deletes only `<job id>_*` videos and job-id audio folders (M1).
