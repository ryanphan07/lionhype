# LionHype: current state (2026-10-28)

What exists today. Verified means checked by a test or by a run; untested means written but never exercised. Source of truth for gaps: `docs/AUDIT.md`; for next work: `docs/TASKS.md`.

## Flow

```
upload -> validate + save -> job created -> background pipeline:
  extracting   duration, motion crop box (once per video)
  analyzing    per 10 s window: sample frames -> vision LLM -> quips (sequential)
  synthesizing finalize timeline -> edge-tts per quip (bounded concurrency) -> measure durations -> schedule
  completed    GET /api/jobs/{id} returns quips + audio_available
```
The browser keeps the file as a blob URL for playback; the server never serves videos.

## Backend (`backend/app/`)

| File | What it does | Status |
|---|---|---|
| `main.py` | FastAPI app, CORS, `POST /api/upload`, `GET /api/jobs/{id}`, `WS /ws/analyze/{job_id}`, audio-only static mount, generic 500 handler, periodic job cleanup | Route tests (LLM/TTS faked); upload and ws exercised by hand in earlier sessions |
| `config.py` | Single `settings` object, `.env` resolved relative to the file. Full list in `backend/.env.example` | Verified |
| `services/jobs.py` | In-memory `JobStore`: status/progress monotonic, terminal states sticky, subscriber queues, TTL purge | Verified (12 tests) |
| `services/pipeline.py` | Background runner; failure marks job `error` with a generic message and deletes the job's files | Verified |
| `services/video_processor.py` | Filename sanitizing, extension/size checks, corruption check, duration, `motion_box` / `compute_crop_box`, `plan_windows`, `sample_window_frames` (same crop for all frames, aspect-preserving resize to `FRAME_WIDTH`) | Verified on synthetic video; crop validated on real footage via the spike |
| `services/llm.py` | `analyze_window`: system prompt + `image_url` parts, `<think>` and fence stripping, first-JSON-object parse (`raw_decode`), one retry with a JSON nudge, token/time logging. No canned fallback: failures raise | Verified live (one window, Qwen3.5-9B, 44.7 s for 6 frames / 3248 prompt tokens) |
| `services/commentary.py` | Window loop, `finalize_timeline` (sort, clamp, round to 2 decimals, `MIN_QUIP_GAP_SEC`; text is never cut), TTS fan-out, `schedule_quips`, `audio_available` | Verified live before the F1-F3 fixes; re-verify live |
| `services/tts.py` | edge-tts with `TTS_VOICE`/`TTS_RATE`, per-clip `TTS_TIMEOUT_SECONDS`; any failure deletes partial files and returns None; durations via mutagen (unreadable duration counts as failure) | Verified live with edge-tts 7.3.1 |
| `schemas/events.py` | `CommentaryQuip{timestamp,text,audio_url,duration_sec}`, `CommentaryResponse{quips,video_url,audio_available}` | Verified |
| `prompts/commentary_system.txt` | Owner-written announcer prompt; `MAX_QUIPS` replaced at load; cached per process (restart after editing) | Works with the 9B model; quality on real motion not judged |

### Behavior worth knowing
- Limits: extensions `.mp4 .mov .avi`, `MAX_UPLOAD_MB` (2048), `MAX_VIDEO_SECONDS` (1800). Long clips (10+ min) are allowed by the limits but untested: see TASKS session 7b. Rejections are HTTP 400 `{"detail": ...}` and delete the file.
- A window that fails (transport error, unusable JSON after one retry) fails the whole job. A job with zero usable quips fails.
- TTS failures never fail the job: the quip is kept with `audio_url: null, duration_sec: null`; if no clip has audio the job message is "Commentary ready (audio unavailable)".
- `schedule_quips`: audio quips are processed in time order and may not start before the previous audio ends + 0.3 s; shift up to `MAX_SHIFT_SEC` (2.0) else drop; no-audio quips never block. Every shift/drop is logged.
- Cleanup: failure deletes video, frames and audio for the job; success deletes the source video immediately (audio stays until the job expires); a loop purges expired jobs (TTL 1 h) and their files; startup sweeps `uploads/videos` and `uploads/audio` (the store is empty then).
- One job at a time: an upload while another job is running gets HTTP 409. (No queue.)
- Removed earlier: `/api/commentary/*`, presigned/boto3 endpoint, `backend/main.py`, `mcp_server.py`, canned LLM output, fake audio, 224x224 JSON-text frames.

## Frontend (`frontend/src/`)
- `App.jsx`: upload via axios, then `WS /ws/analyze/{job_id}` with capped exponential reconnect (5 tries), switches on `msg.status` only, on `completed` fetches `GET /api/jobs/{id}`, shows toast + inline error, `VITE_API_BASE` (default http://localhost:8000).
- `components/VideoPlayer.jsx`: blob-URL video, quip queue driven by `timeupdate`, one clip at a time, video ducked to 0.3 while a clip plays, stale lines (older than 4 s) skipped, seek resets, pause/resume handled, autoplay-block notice, "audio unavailable" notice, clickable commentary list that seeks.
- Lint and build pass. No frontend tests. Browser behavior (progress, sync, seek) has not been re-verified since session 6.

## Tests: 95 passing (`pytest backend/tests -q`)
- `test_jobs.py` JobStore. `test_api.py` upload, job GET, WebSocket, cleanup, videos not served, validators. `test_main.py` orchestration with LLM/TTS faked (file name is historical). `test_vision.py` crop, windows, frame sampling on real tiny videos, prompt/message building, parser, finalize, window failure. `test_audio.py` TTS success/failure/timeout/no leftover files, mutagen on a hand-built mp3, `schedule_quips`, `audio_available`, parser edge cases.
- Not covered: real LLM or real edge-tts in CI (both need external services), real `motion_box` on moving-subject video, frontend.

## Environment
- Windows native, no Docker (Docker files are stale and untested).
- llama-server at 127.0.0.1:8080 with `--mmproj`. In use now: Qwen3.5-9B Q4_K_M; CLAUDE.md names Qwen3.6-35B-A3B. Decide which one is the demo model.
- edge-tts must be >= 7.3.1 (7.2.8 gets 403).

## Maturity
Local-first prototype that runs end to end with no fake output. Not hardened: single in-memory job store, no auth, no queue, unpinned dependencies, one unofficial TTS endpoint. Honest and demoable once the README/GIF exist and real-footage runs are done (timing defects F1-F3 are fixed in code, not yet re-run live).
