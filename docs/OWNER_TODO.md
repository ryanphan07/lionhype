# Owner to-do (things only you can do)

Everything Claude Code can do on its own is in `docs/TASKS.md` (v0.1.0 prep is next). This list is what is blocked on you, in order. Updated 2026-10-28 after session 16. Settled: A1-3 (D4 = A, MIT, Docker removed), CLAUDE.md edits, the browser check (C1 sync/seek/pause) and the 40 s benchmark.

## A. Decisions
1. **D4, long-job strategy** (`docs/DECISIONS.md`) was settled as A for v0.1.0 (all-or-nothing). Revisit B/C after release.
2. **Optional features**, default is no: N7 (pass the model's own scene summaries to the next window); resume after a page refresh.
3. **TTS fallback** (D3): nothing to decide until after v0.1.0. If edge-tts breaks again, decide on an offline voice (Piper).

## C. Still open (needs llama-server, internet and a browser; start commands are in the README Quickstart)
1. **By ear**: is `TTS_RATE=+10%` fine, or try `+20%` in `backend/.env`; is the commentary funny and accurate?
2. **Error paths**: stop llama-server mid-job (expect "The AI model is not reachable..."); block edge-tts (expect the "audio unavailable" notice); restart uvicorn mid-job (expect "The server no longer has this job").
3. **After v0.1.0**: long clip (10+ min) and throughput table on the 9B and 35B (see `docs/TASKS.md` After v0.1.0).

## D. Ship
1. Demo assets: done in session 17 (docs/demo.gif, docs/demo.mp4).
2. Push the `v0.1.0` tag (Claude Code never pushes).
3. Draft resume bullets with the planning chat from what the repo proves (see `docs/BRIEFING.md`).

## E. Housekeeping (optional)
- Root has `repomix-output.xml` and `.aider.chat.history.md` (ignored by git, large): delete them if you do not need them.
- `backend/uploads/` is swept at server start; the sweep now deletes only `<job id>_*` videos and job-id audio folders (M1).
