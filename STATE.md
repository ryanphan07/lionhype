### `STATE.md`
I updated the **Validation & Security helpers** section to explicitly state that the functions are already actively integrated into the `backend/app/main.py` upload pipeline[cite: 1, 3].

```markdown
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
- `process_video_commentary(video_path)` as the core async orchestrator
- CPU-bound frame extraction offloaded via `asyncio.to_thread`
- LLM event timeline generation via `generate_event_timeline(frames)`
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
- Per-quip audio generation based on timestamp and text
- Output path in the backend upload/audio folder
- URL generation for playback from the app server
- Fallback behavior if TTS dependency is missing
- Observability logging for retry wrappers and fallback behavior

#### MCP Soundboard Server
`backend/mcp_server.py` implements a FastMCP server for LLM-driven sound effects.

Features in place:
- Exposes a `trigger_sfx` tool to LLM agents
- Supports effects like gong, cymbals, airhorn, and drumroll
- Returns structured event strings for timestamp synchronization
- Designed to integrate with the commentary pipeline for dynamic audio cues

#### FastAPI app and websocket flow
`backend/app/main.py` implements the API and real-time processing flow.

Features in place:
- `/api/upload` for video upload handling (including validation constraints)
- `/api/upload/presigned-url` for generating secure upload URLs
- `/api/commentary/generate` for direct commentary generation using background tasks
- `/api/commentary/mock` retained as a deprecated endpoint
- `@app.websocket("/ws/analyze")` for real-time analysis progress
- JSON progress messages using canonical phases: `uploading`, `extracting`, `analyzing`, `synthesizing`, `completed`, and `error`
- Error propagation with standardized 500 JSON responses from the global exception handler
- Background job tracking via `job_tracker` dictionary for asynchronous commentary generation
- WebSocket disconnect handling and auto-reconnect logic on the frontend

This is the main runtime entrypoint for the backend app.

#### Schemas
`backend/app/schemas/events.py` defines the data models used by the app:
- `EventTimeline`
- `CommentaryQuip`
- `CommentaryResponse`

It includes the `audio_url` field needed to attach generated audio to each commentary quip.

#### Deployment & Configuration
The project is fully Dockerized via `docker-compose`, providing a consistent environment for development and production. It uses a strict `.env` configuration pattern to manage external AI provider credentials and settings, with built-in retry logic for resilient service communication.

### Frontend

The frontend lives in `frontend/src`.

#### App-level flow
`frontend/src/App.jsx` does the following:
- Accepts video upload input and posts it to the backend
- Opens a WebSocket to `ws://backend:8000/ws/analyze`
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
`backend/tests/test_main.py` contains mocked integration-style tests covering:
- frame extraction payload structure
- commentary generation with audio mapping
- WebSocket flow for final output exchange

These tests mock OpenCV capture, LLM output, and TTS generation so they can run in CI without actual video hardware or paid external APIs.

## Current maturity assessment

This repo is best categorized as:
- a local-first prototype,
- capable of demonstrating the requested flow,
- useful for iteration and experimentation,
- not yet a hardened shipped product.

The main architecture and flow are in place. The remaining work is mostly about robustness, real-world validation, operational polish, and deployment readiness.
