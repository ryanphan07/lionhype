# Project Conventions

## Project context
LionHype is a local-first app that turns lion dance videos into humorous, time-synced AI commentary with TTS audio. FastAPI backend (OpenCV frames, OpenAI-compatible multimodal LLM, edge-tts) + React/Vite frontend with WebSocket progress.

Goal: a credible, honest, demoable MVP for a resume (upload a clip of 90s or less; the goal is now long clips, 10+ min: `MAX_VIDEO_SECONDS` 1800 and `MAX_UPLOAD_MB` 2048 are guards, see docs/DECISIONS.md D1, see progress, get commentary with non-overlapping audio, run locally in a few commands). Do not add features beyond `docs/AUDIT.md` and `TASKS.md` without asking.

## Environment
- Windows + PowerShell. Native run; Docker is untested and not part of the MVP.
- LLM: llama-server (OpenAI-compatible) at `http://127.0.0.1:8080/v1`, multimodal via `--mmproj`. Configure via `backend/.env` (see `backend/.env.example` for LLM_*, WINDOW_SECONDS, FRAMES_PER_WINDOW, FRAME_WIDTH, MAX_QUIPS_PER_WINDOW, MAX_VIDEO_SECONDS).
- Model in use on 2026-10-28: Qwen3.5-9B Q4_K_M (CLAUDE.md names Qwen3.6-35B-A3B). Measured: about 45 s per 10 s window.
- Start it with: `llama-server -m <gguf> --mmproj <mmproj-F16.gguf> -c 32768 -np 1 -ngl 99 --port 8080 --jinja`
- The system prompt lives in `backend/app/prompts/commentary_system.txt` (owner-written; `MAX_QUIPS` is replaced by MAX_QUIPS_PER_WINDOW at load). The LLM step never falls back to canned text: a failed window ends the job in `error`.
- TTS: edge-tts (needs internet). Failures yield no audio (`audio_url` null), never placeholder files. Settings: TTS_VOICE, TTS_RATE, TTS_TIMEOUT_SECONDS, MAX_SHIFT_SEC.
- All settings come from the single shared `settings` object in `backend/app/config.py`. No hardcoded URLs or paths elsewhere.

## Commands
(If any of these is wrong, fix this section.)
Run from the repo root in PowerShell unless noted. Tests (95) verified 2026-10-28; lint and build verified 2026-10-28, `uvicorn` last verified 2026-10-27. edge-tts must be >= 7.3.1 (re-run `pip install -r requirements.txt` after pulling).
- Backend setup (once): `cd backend; python -m venv venv; venv\Scripts\Activate.ps1; pip install -r requirements.txt` .
- Backend tests: `pytest backend/tests -q` (works from the repo root or from `backend/`).
- Backend run: `cd backend; uvicorn app.main:app --port 8000`. `backend/.env` is resolved relative to `config.py`, so the working directory does not matter for `.env`. `CORS_ORIGINS` (JSON list) is configurable there.
- Frontend setup (once): `cd frontend; npm install`. Optional `frontend/.env` with `VITE_API_BASE` (default http://localhost:8000); see `.env.example`.
- Frontend: `cd frontend; npm run lint; npm run build; npm run dev` (dev server on http://localhost:5173).

## Documentation
- Update docs once at the end of each work session, not after every edit:
  - `STATE.md`: what is implemented
  - `TASKS.md`: what is missing or next
  - `README.md`: what it is, architecture, quickstart, route list, known limitations
- Docs must match the code. Mark anything unverified as untested.
- No pasted chat text, citation markers, or meta commentary in docs.

## API & WebSocket Contract
- `POST /api/upload` returns JSON including `job_id`. The job runs in the background.
- `WS /ws/analyze/{job_id}` is server-to-client only. Every message is:
  ```json
  {
    "status": "uploading" | "extracting" | "analyzing" | "synthesizing" | "completed" | "error",
    "progress": 0-100,
    "message": "optional human-readable detail, required when status is 'error'"
  }
  ```
- On subscribe the server sends the current state first, so reconnects are safe. Unknown job: send an error message, close with code 4404.
- The `completed` message carries no result. Fetch it from `GET /api/jobs/{job_id}`, which returns `{job_id, status, progress, message, result}`.
- Frontend listeners switch on `msg.status` only (never `msg.phase`, never fall back to `msg.message`).
- HTTP errors: `HTTPException` with `{"detail": "<clear message>"}`.

## Canonical Processing Phases
```
idle -> uploading -> extracting -> analyzing -> synthesizing -> completed
                                                               -> error
```
- `idle` exists only as the frontend's initial state; the backend never sends it.
- Use these exact strings everywhere (state values, WebSocket payloads, UI labels). Don't add or reorder phases without updating this list.

## Backend Rules
- Any upload/processing failure must delete the job's temporary/uploaded files before raising or finishing.
- Client-facing error messages are generic. Log details server-side with `logger.exception`. Never log base64 frame data or secrets.
- Never trust client-supplied paths. The server owns all file paths. `job_id` is the `video_id` for storage (video, frames, audio).
- Serve only the audio folder statically, never raw videos.
- Validation (filename sanitization, extension/size/duration limits, corruption checks) happens before a write is considered final.

## Testing
- Tests assert behavior. Mock only external boundaries (LLM client, TTS, OpenCV I/O), not the logic under test.
- Run backend tests and frontend lint/build before every commit. One logical change per commit.

## Timing
- Spoken-line scheduling is server-side (`commentary.schedule_quips`). Measured TTS speed: about 1.8 words per second including padding (8 words = 4.5 s). Keep `MIN_QUIP_GAP_SEC` (4.5) and the prompt's spacing and length rules (4.5 s apart, 10 words) consistent with that. Quip text is never truncated.
- Quip timestamps in results are rounded to 2 decimals.

## Library / API Pins
- **react-toastify**: use string literals for position, e.g. `toast.error(msg, { position: "top-right" })`. Do NOT use `toast.POSITION.TOP_RIGHT` (deprecated).

## File & Folder Layout
- Backend routes/entrypoint: `backend/app/main.py`
- Backend services: `backend/app/services/` (e.g. `jobs.py`, `commentary.py`, `llm.py`, `tts.py`, `video_processor.py`)
- Backend settings/schemas: `backend/app/config.py`, `backend/app/schemas/`
- Backend tests: `backend/tests/`; dev scripts: `backend/scripts/`
- Frontend app/state: `frontend/src/App.jsx`; components: `frontend/src/components/`
- Docs: `README.md`, `STATE.md`, `TASKS.md`, `docs/AUDIT.md`