# LionHype: AI Lion Dance Commentator

LionHype is a local-first AI system that analyzes lion dance performances and generates real-time humor, roasts, and sound effects.

## 🚀 Overview
- **Live Roasts**: LLM generates commentary every few seconds based on visual frames.
- **Soundboard**: Automatically triggers Gongs, Cymbals, and Airhorns based on content.
- **Hybrid Architecture**: Uses Ollama for local inference with a Gemini fallback.

## 🏗️ Architecture
- **Frontend**: React + Tailwind + Web Audio API.
- **Backend**: FastAPI + WebSockets + OpenCV.
- **Inference**: Ollama (Qwen2.5-VL) / Google Gemini (Cloud Fallback).
- **Soundboard**: FastMCP logic for automated sound trigger management.

## 🛠️ Setup Instructions

### 1. Prerequisites
- Python 3.10+
- Node.js & npm/yarn
- Ollama installed with `qwen2.5-vl:7b` pulled.
- FFmpeg installed on your system.

### 2. Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd LionHype/backend
   ```
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the server:
   ```bash
   uvicorn main:app --port 8000 --host 0.0.0.0
   ```

### 3. Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run in development mode:
   ```bash
   npm run dev
   ```

### 4. Configuration
- **Video Source**: Place your lion dance video in `LionHype/video_input/lion_dance.mp4`.
- **Cloud Fallback**: To enable Gemini, set environment variable:
  `set USE_CLOUD_ENGINE=true` (Windows) or `export USE_CLOUD_ENGINE=true` (Linux/macOS).

## 📂 Folder Structure
- `backend/`: FastAPI, OpenCV processing, and MCP logic.
- `frontend/`: React-based dashboard and Web Audio management.
- `assets/`: Audio samples (`.wav`) and branding icons.
- `video_input/`: Source footage for analysis.

## 🧪 Testing
- Start the backend and ensure the WebSocket is reachable at `ws://localhost:8000/ws/analyze`.
- Connect the frontend and verify that the log scrolls and sound effects trigger.
