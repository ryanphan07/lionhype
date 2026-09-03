# LionHype: AI Lion Dance Commentator

LionHype is a local-first AI application for analyzing lion dance performances and turning them into humorous, time-synced commentary with audio playback. The project blends a FastAPI backend, OpenCV-based frame extraction, LLM-driven event analysis, TTS synthesis, and a lightweight React frontend. In its current form it is a working prototype and proof-of-concept rather than a production-ready SaaS or broadcast platform.

## High-level overview

The repo is organized around a simple end-to-end flow:

1. A user uploads a video.
2. The backend extracts sampled frames with OpenCV.
3. Frames are converted to base64 JPEG payloads for downstream vision/LLM processing.
4. The app generates commentary quips with timestamps.
5. Audio clips are synthesized for each quip.
6. The frontend connects to a WebSocket for live progress updates and then renders the final timeline and playback controls.

This gives the app a real-time “commentary pipeline” pattern: extraction -> analysis -> synthesis -> UI updates.

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

These helpers are ready for integration into the upload pipeline.

#### Commentary orchestration
`backend/app/services/commentary.py` implements the async commentary pipeline.

Features in place:
- `process_video_commentary(video_path)` as the core async orchestrator
- CPU-bound frame extraction offloaded via `asyncio.to_thread`
- LLM event timeline generation via `generate_event_timeline(frames)`
- Concurrent TTS generation via `asyncio.gather`
- Mapping audio URLs back to corresponding quip objects
- Structured `CommentaryResponse` return values

This is the main “content pipeline” that turns extracted visual frames into final commentary items with audio.

#### LLM integration
`backend/app/services/llm.py` contains the LLM-facing logic.

Features in place:
- Local/offline-friendly fallback when no LLM client is configured
- Timeline normalization for both `timestamp` and `timestamp_ms` formats
- A generated event timeline based on input frames when external services are unavailable
- A system prompt designed for energetic lion-dance-style commentary

The code is intentionally resilient in CI and offline environments.

#### TTS synthesis
`backend/app/services/tts.py` adds audio clip generation.

Features in place:
- Per-quip audio generation based on timestamp and text
- Output path in the backend upload/audio folder
- URL generation for playback from the app server
- Fallback behavior if TTS dependency is missing

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
- `/api/upload` for video upload handling
- `/api/commentary/generate` for direct commentary generation
- `/api/commentary/mock` retained as a deprecated endpoint
- `@app.websocket("/ws/analyze")` for real-time analysis progress
- JSON progress messages with statuses such as `processing` and `completed`
- Error propagation with standardized 500 JSON responses from the global exception handler
- WebSocket disconnect handling

This is the main runtime entrypoint for the backend app.

#### Schemas
`backend/app/schemas/events.py` defines the data models used by the app:
- `EventTimeline`
- `CommentaryQuip`
- `CommentaryResponse`

It includes the `audio_url` field needed to attach generated audio to each commentary quip.

### Frontend

The frontend lives in `frontend/src`.

#### App-level flow
`frontend/src/App.jsx` does the following:
- Accepts video upload input
- Posts the file to the backend
- Opens a WebSocket to `ws://localhost:8000/ws/analyze`
- Tracks backend processing messages
- Updates UI status/progress indicators
- Stores final commentary quips when processing completes
- Displays explicit error messaging if analysis fails

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

## What works today

At a high level, the codebase already supports the following flow successfully:

- A video file can be uploaded to the backend.
- The app can extract frames from the video using OpenCV.
- Sampled frames are turned into base64-encoded JPEG payloads.
- A commentary timeline can be generated in async style.
- The result can include synthesized audio URLs attached to quips.
- WebSocket progress updates can be emitted during analysis.
- A React client can connect to the backend and display final commentary output.
- The backend tests cover the primary code path in a mocked environment.

In practical terms: the application is already a functional prototype of the intended pipeline.

## What is missing or incomplete

The repo is not yet production-grade. The current state is best described as a working prototype with a few critical gaps.

### 1. Production hardening
Missing or incomplete areas include:
- integration of existing validation helpers (`validate_upload_metadata`, `is_video_corrupt`) into the `/api/upload` route
- stronger input validation for uploaded files
- safe handling of missing or invalid videos
- more robust logging and monitoring
- deployment packaging and environment configuration

### 2. Real LLM/TTS production integration
The current code anticipates external AI services but also includes offline fallbacks.

This means:
- LLM calls can work if a compatible local or remote service is available
- but the repo does not yet enforce a production-grade single integration path
- TTS output is generated locally as a fallback pattern, but real production deployment still needs a finalized choice of model/provider and audio storage strategy

### 3. End-to-end real-world validation
The project is tested with mock objects, but it is not yet proven against:
- real uploaded lion dance footage
- real OpenCV capture edge cases
- high-volume processing
- long videos
- actual WebSocket stress/load conditions

### 4. Frontend polish
The frontend is functional but still relatively minimal:
- limited state models for richer status transitions
- no strong error toast UX beyond basic alert blocks
- limited playback orchestration beyond timestamp-based triggers
- no deeper visual dashboard or timeline analytics

### 5. Deployment and infrastructure
The repo does not yet present a fully defined deployment strategy for:
- backend hosting
- frontend hosting
- audio/static asset serving in production
- environment variables and configuration separation
- containerization or cloud deployment

### 6. Security and operational concerns
Potential follow-ups include:
- limiting upload size and file extensions
- securing WebSocket access
- avoiding direct trust of user-supplied file paths
- sanitizing and validating generated filenames
- controlling backend access to AI services and external endpoints

## Current maturity assessment

This repo is best categorized as:
- a local-first prototype,
- capable of demonstrating the requested flow,
- useful for iteration and experimentation,
- not yet a hardened shipped product.

The main architecture and flow are in place. The remaining work is mostly about robustness, real-world validation, operational polish, and deployment readiness.

## Recommended next steps

### Priority 1: make the pipeline production-safe
- Add stricter validation around uploaded videos and file paths
- Define exact config for LLM and TTS providers
- Standardize error handling and logging across all services
- Decide how generated audio files are stored and exposed in production

### Priority 2: harden backend reliability
- Add more unit tests around failure cases
- Validate behavior on invalid video files
- Add retry and timeout logic for external AI services
- Ensure WebSocket clients handle reconnects gracefully

### Priority 3: improve frontend UX
- Add richer progress states such as `extracting`, `analyzing`, `synthesizing`, `completed`, `error`
- Improve toast/alert handling and visible user feedback
- Consider timeline playback improvements and better quip highlighting
- Add basic loading and empty states

### Priority 4: validate on real content
- Test against actual lion dance footage
- Measure runtime and performance across different video lengths
- Tune the frame sampling strategy for quality vs. latency vs. cost

### Priority 5: prepare for deployment
- Add Dockerfile and/or deployment scripts if needed
- Define environment variables and `.env` conventions
- Decide hosting strategy for frontend and API
- Document how to run in a real environment

## Repo structure

- `backend/` – FastAPI application, OpenCV processing, LLM/TTS services, schemas, tests
- `backend/app/main.py` – app entrypoint and API/WebSocket routes
- `backend/app/services/video_processor.py` – frame extraction logic
- `backend/app/services/commentary.py` – async processing pipeline
- `backend/app/services/llm.py` – event timeline generation
- `backend/app/services/tts.py` – audio generation
- `backend/tests/` – mocked integration tests
- `frontend/src/` – React app and real-time UI
- `assets/` – local media and sound assets
- `video_input/` – video source samples

## Quick run instructions

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Test run
```bash
cd backend
pytest -q
```

## Bottom line

LionHype has already achieved the foundation of a real AI commentator pipeline: upload video, sample frames, generate timeline, attach audio, and present the result live in a UI. The implementation is coherent and mostly working as a prototype. The key remaining work is not invention of the core idea—it is hardening, validation, deployment readiness, and turning the prototype into a reliable product-grade experience.
