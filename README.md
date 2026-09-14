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

## Developer Documentation

- [Current Implementation Status & Features](./STATE.md)
- [Active Development Roadmap & Tasks](./TASKS.md)

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
