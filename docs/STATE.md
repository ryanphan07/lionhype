This file tracks the current architectural reality and completed features of the LionHype project.

## What is already implemented

### Backend

#### Frame extraction
The core extraction logic is implemented in `backend/app/services/video_processor.py`.

Features in place:
- OpenCV video capture via `cv2.VideoCapture`
- Failure handling when a file cannot be opened
- FPS-based sampling via `frame_interval_sec`
- Frame resizing to a smaller output size (224x224) for efficient downstream payload size
- JPEG encoding and base64 conversion for each selected frame
- Timestamp generation in seconds with rounding
- Resource cleanup via `finally` and `cap.release()`

This is the critical “raw media to model-ready payload” component.

#### Validation & Security helpers
`backend/app/services/video_processor.py` includes utility functions for input validation and integrity checks:
- `sanitize_filename()` to prevent path traversal attacks
- `validate_upload_metadata()` to enforce allowed file extensions and size limits
- `is_video_corrupt()` to verify video container integrity using OpenCV

These helpers are actively integrated into the upload pipeline in `backend/app/main.py` to enforce file constraints and sanitize inputs upon user upload.

#### Commentary orchestration
`backend/app/services/commentary.py` implements the async commentary pipeline.

Features in place:
- `process_video_commentary(video_path, job_id, progress_cb)` as the core async orchestrator; `job_id` is the `video_id` for the audio folder
- CPU-bound frame extraction offloaded via `asyncio.to_thread`
- Vision LLM: motion crop (once per video), windows of frames sent as image_url parts, one call per window via `analyze_window`, merged and budgeted in `commentary.finalize_timeline` (untested against a live model)
- Concurrent TTS generation via `asyncio.gather`
- Mapping audio URLs back to corresponding quip objects
- Structured `CommentaryResponse` return values
- Detailed step-by-step lifecycle logging for frame extraction, LLM timeline generation, and TTS synthesis

This is the main “content pipeline” that turns extracted visual frames into final commentary items with audio.

#### LLM integration
`backend/app/services/llm.py` contains the LLM-facing logic.

Features in place:
- Local/offline-friendly fallback when no LLM client is configured
- Timeline normalization for both `timestamp` and `timestamp_ms` formats
- A generated event timeline based on input frames when external services are unavailable
- A system prompt designed for energetic lion-dance-style commentary
- Observability logging for retry wrappers and fallback parsing

The code is intentionally resilient in CI and offline environments.

#### TTS synthesis
`backend/app/services/tts.py` adds audio clip generation.

Features in place:
- Per-quip edge-tts synthesis (`TTS_VOICE`, `TTS_RATE`, per-clip `TTS_TIMEOUT_SECONDS`, concurrency `TTS_CONCURRENCY`), untested against live edge-tts
- Any failure (exception, timeout, empty/tiny file, unreadable duration) logs a warning, deletes partial files and returns None, so `audio_url` is null. No fake audio is ever written.
- mp3 duration measured with mutagen and stored as `duration_sec`
- `commentary.schedule_quips`: audio quips never start before the previous audio ends + 0.3s; shifted up to `MAX_SHIFT_SEC`, else dropped; no-audio quips are kept and never block
- Result carries `audio_available`; with no audio the job message is "Commentary ready (audio unavailable)" and the UI shows a notice

#### FastAPI app, job API and websocket flow
`backend/app/main.py` (routes), `backend/app/services/jobs.py` (in-memory `JobStore`) and `backend/app/services/pipeline.py` (background runner). Unverified against real footage and the real LLM/TTS; covered by route tests with the LLM and TTS mocked.

- `POST /api/upload`: validates (filename, extension, size) before writing, saves to `<UPLOAD_DIR>/videos/<job_id>_<safe_name>`, checks the container, creates the job and runs the pipeline via `BackgroundTasks`. Returns `{job_id, filename}`. No frame extraction at upload time.
- `GET /api/jobs/{job_id}`: `{job_id, status, progress, message, result}`; 404 `{"detail": "Job not found"}`.
- `WS /ws/analyze/{job_id}`: server-to-client only. Sends the current snapshot, then live updates, and closes 1000 after `completed`/`error`. Unknown job: error message and close 4404. Detects client disconnect while idle and always unsubscribes.
- Pipeline runner: `process_video_commentary(video_path, job_id=..., progress_cb=...)` drives `extracting`, `analyzing`, `synthesizing`; then `job_store.complete`. On any exception it logs, marks the job `error` with a generic message, and deletes the job's video, frames dir and audio dir. A failing progress callback never aborts the pipeline.
- Only `<UPLOAD_DIR>/audio` is served statically (`/uploads/audio/...`); videos are never served.
- Unhandled exceptions return a generic 500 `{"detail": "Internal server error"}` and are logged.
- Removed: `/api/commentary/generate`, `/api/commentary/mock`, `job_tracker`, `backend/mcp_server.py`, `generate_video_commentary`.

#### Schemas
`backend/app/schemas/events.py` defines the data models used by the app:
- `EventTimeline`
- `CommentaryQuip`
- `CommentaryResponse`

It includes the `audio_url` field needed to attach generated audio to each commentary quip.

#### Deployment & Configuration
Docker is untested and not part of the MVP; the app runs natively. Configuration uses a `.env` pattern to manage external AI provider credentials and settings, with built-in retry logic for resilient service communication.

### Frontend

The frontend lives in `frontend/src`.

#### App-level flow
`frontend/src/App.jsx` does the following:
- Accepts video upload input and posts it to the backend
- Opens a WebSocket to `/ws/analyze` (not yet updated to the job API: still needs `job_id` and the new upload response)
- Tracks backend processing messages across canonical phases (`uploading`, `extracting`, `analyzing`, `synthesizing`, `completed`, `error`)
- Updates UI status/progress indicators and pipeline stage labels
- Stores final commentary quips when processing completes
- Displays explicit error messaging via `react-toastify` if analysis fails
- Implements auto-reconnect logic for WebSocket drops

#### Video player UI
`frontend/src/components/VideoPlayer.jsx` handles the playback experience.

Features in place:
- Displays the uploaded video
- Watches the current playback time against quip timestamps
- Triggers audio playback as each commentary point is reached
- Renders the final quip list once processing is complete
- Includes audio controls for the synthesized clips

### Testing
92 backend tests, all passing. LLM and edge-tts are faked; `tests/test_audio.py` covers TTS paths, mutagen duration on a hand-built mp3, scheduling, audio_available and the JSON parser.
- `tests/test_jobs.py`: JobStore behavior
- `tests/test_main.py`: frame extraction, commentary orchestration, progress callback, TTS failure handling
- `tests/test_api.py`: upload, GET job, WebSocket (replay, 4404, live progress, idle disconnect), pipeline failure cleanup, videos not served

## Current maturity assessment

This repo is best categorized as:
- a local-first prototype,
- capable of demonstrating the requested flow,
- useful for iteration and experimentation,
- not yet a hardened shipped product.

The main architecture and flow are in place. The remaining work is mostly about robustness, real-world validation, operational polish, and deployment readiness.

## Safety and cleanup (session 3B)
- Only `<UPLOAD_DIR>/audio` is served (`/uploads/audio`). Uploads over `MAX_VIDEO_SECONDS` (default 90) or unreadable are rejected with 400 and their file is deleted.
- Unhandled errors return `{"detail": "Internal server error"}` and are logged; logging is configured in `app/main.py`.
- Any failure after the first disk write deletes the job's files. A lifespan task purges expired jobs and their files every `CLEANUP_INTERVAL_SECONDS` (600).
- `llm.py` and `tts.py` use the shared `settings`. `backend/.env.example` lists all settings.
