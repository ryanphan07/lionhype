# LionHype: AI lion dance commentator

Upload a short lion dance video and get humorous, time-synced play-by-play commentary, read aloud while the video plays. A local vision LLM watches the footage, edge-tts speaks the lines, and the server schedules them so they never overlap.

Status: working local prototype, not a product. It runs end to end with no fake output: if the model or TTS fails, you see an error or a "no audio" notice, never placeholder content. Demo GIF: not recorded yet.

## How it works

```
Browser (React/Vite)                    FastAPI backend                         Local services
  upload ---------------------------->  POST /api/upload  (validate, save, create job)
  progress <---- WS /ws/analyze/{id} -  background pipeline
                                          1 extracting    OpenCV: duration, motion crop box
                                          2 analyzing     10 s windows, 6 frames each ------> llama-server
                                                          (image_url parts, JSON quips) <---- (multimodal Qwen, --mmproj)
                                          3 synthesizing  edge-tts per quip --------------> Microsoft edge-tts (internet)
                                                          mp3 durations (mutagen), schedule so audio never overlaps
  result <---- GET /api/jobs/{id} ----  quips: timestamp, text, audio_url, duration_sec
  plays video + queued audio clips in sync (video ducks while a clip plays)
```

Key design points:
- Motion-based crop: wide stage shots are cropped once per video to where the bright, moving performers are, so the model sees them at useful resolution.
- Windowed analysis: one LLM call per 10 s window, passing the last two quips to avoid repeats.
- Server-side scheduling: an audio line never starts before the previous one ends plus 0.3 s. It is shifted up to 2 s later, otherwise dropped. Lines without audio are still shown.
- Honest failure: a failed LLM window fails the job; a failed TTS clip only removes that line's audio.

## Requirements
- Windows (developed natively on Windows 11), Python 3.12, Node 20+ (tested on 24).
- A running llama-server with a multimodal Qwen model and its mmproj file.
- Internet access for edge-tts (an unofficial Microsoft endpoint; needs `edge-tts>=7.3.1`).

## Quickstart (PowerShell, from the repo root)

```powershell
# 1. LLM (separate terminal; adjust paths)
llama-server -m <model.gguf> --mmproj <mmproj-F16.gguf> -c 32768 -np 1 -ngl 99 --port 8080 --jinja

# 2. Backend (first time: create the venv and install)
cd backend
python -m venv venv; venv\Scripts\Activate.ps1; pip install -r requirements.txt
copy .env.example .env      # optional; every value shown is the default
uvicorn app.main:app --port 8000

# 3. Frontend (another terminal)
cd frontend; npm install; npm run dev     # http://localhost:5173
```
Open http://localhost:5173, choose a clip (`.mp4`, `.mov`, `.avi`; at most 30 min and 2 GB by default, see `MAX_VIDEO_SECONDS`/`MAX_UPLOAD_MB`), wait for the progress bar, press play. Expect minutes of processing: a 10 s window took about 45 s on a 9B model (measured).

## API

| Route | Purpose |
|---|---|
| `POST /api/upload` (multipart `file`) | Validates and saves the clip, starts a job. Returns `{job_id, filename}`. 400 `{"detail": ...}` on bad input |
| `GET /api/jobs/{job_id}` | `{job_id, status, progress, message, result}`; `result` is `{quips: [{timestamp, text, audio_url, duration_sec}], audio_available}` once completed. 404 if unknown |
| `WS /ws/analyze/{job_id}` | Server to client only: `{status, progress, message?}` with status in `uploading, extracting, analyzing, synthesizing, completed, error`. Sends the current state first, closes after a terminal state; unknown job closes with 4404 |
| `GET /uploads/audio/{job_id}/{file}.mp3` | Generated speech clips. Videos are never served |

## Configuration (`backend/.env`, see `backend/.env.example`)

| Setting | Default | Meaning |
|---|---|---|
| `LLM_BASE_URL`, `LLM_MODEL`, `LLM_TIMEOUT`, `LLM_MAX_TOKENS`, `LLM_ENABLE_THINKING` | `http://127.0.0.1:8080/v1`, ..., 300 s, 500, false | LLM endpoint and limits |
| `WINDOW_SECONDS`, `FRAMES_PER_WINDOW`, `FRAME_WIDTH` | 10, 6, 896 | Vision windowing |
| `MAX_QUIPS_PER_WINDOW`, `MIN_QUIP_GAP_SEC` | 3, 4.5 | Quip budget (4.5 s is about the speech time of an 8-word line) |
| `TTS_VOICE`, `TTS_RATE`, `TTS_TIMEOUT_SECONDS`, `TTS_CONCURRENCY`, `TTS_ENABLED` | en-US-GuyNeural, +10%, 30, 4, true | Speech |
| `MAX_SHIFT_SEC` | 2.0 | Largest delay allowed to avoid audio overlap |
| `MAX_VIDEO_SECONDS`, `MAX_UPLOAD_MB` | 1800, 2048 | Upload limits (guards, not speed promises) |
| `JOB_TTL_SECONDS`, `CLEANUP_INTERVAL_SECONDS` | 3600, 600 | Job and file expiry |
| `CORS_ORIGINS`, `PUBLIC_BASE_URL`, `LOG_LEVEL` | localhost:5173/3000, http://localhost:8000, INFO | Server |

The system prompt is `backend/app/prompts/commentary_system.txt` (restart the backend after editing).

## Tests

```powershell
pytest backend/tests -q          # 91 tests: LLM and edge-tts faked, real tiny videos and a real mp3 for the rest
cd frontend; npm run lint; npm run build
```
Not covered by automated tests: the real model, the real TTS service, browser playback sync.

## Known limitations
- Single user, in-memory jobs, no auth, one job at a time is recommended (the LLM server is single-slot).
- Processing is slow on local hardware: about 45 s per 10 s of video on a 9B model, so a 10 minute clip takes roughly 45 minutes. One failed window fails the whole job; jobs are lost on restart.
- Speech needs internet. If edge-tts is unreachable the app shows the commentary as text with a notice.
- `.avi` and some `.mov` files are accepted by the server but may not play in the browser.
- Docker files in the repo are stale and untested; the app is run natively.

## More
- `docs/STATE.md` what is implemented, `docs/TASKS.md` what is next, `docs/AUDIT.md` latest audit, `docs/CONVENTIONS.md` contracts and rules.
