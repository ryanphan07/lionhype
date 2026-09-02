import base64

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.schemas.events import CommentaryQuip, CommentaryResponse
from app.services import commentary as commentary_module
from app.services import llm as llm_module
from app.services import tts as tts_module
from app.services import video_processor
from backend.main import app

client = TestClient(app)


class DummyVideoCapture:
    def __init__(self, frames):
        self.frames = frames
        self.index = 0
        self.fps = 2.0

    def isOpened(self):
        return self.index < len(self.frames) or self.frames

    def get(self, prop):
        if prop == video_processor.cv2.CAP_PROP_FPS:
            return self.fps
        return 0

    def read(self):
        if self.index >= len(self.frames):
            return False, None
        frame = self.frames[self.index]
        self.index += 1
        return True, frame

    def release(self):
        self.index = len(self.frames)


@pytest.mark.parametrize("frame_interval_sec", [1.0])
def test_extract_frames_returns_timestamped_payload(monkeypatch, frame_interval_sec):
    frames = [np.zeros((720, 1280, 3), dtype=np.uint8) for _ in range(4)]
    monkeypatch.setattr(video_processor.cv2, "VideoCapture", lambda _: DummyVideoCapture(frames))

    extracted = video_processor.extract_frames("fake.mp4", frame_interval_sec=frame_interval_sec)

    assert extracted
    assert all({"timestamp", "image_data"}.issubset(item) for item in extracted)
    assert extracted[0]["timestamp"] == 0.0
    assert isinstance(extracted[0]["image_data"], str)
    assert base64.b64decode(extracted[0]["image_data"])


import pytest

@pytest.mark.anyio
async def test_process_video_commentary_maps_audio_to_quips(monkeypatch):
    monkeypatch.setattr(commentary_module.video_processor_service, "extract_frames", lambda _: [
        {"timestamp": 0.0, "image_data": "abc"},
        {"timestamp": 1.0, "image_data": "def"},
    ])

    async def fake_generate_event_timeline(frames):
        return [
            {"timestamp": 0.0, "text": "first quip"},
            {"timestamp": 1.0, "text": "second quip"},
        ]

    async def fake_generate_audio_clip(quip, video_id="default"):
        return {
            "timestamp": quip["timestamp"],
            "text": quip["text"],
            "audio_url": f"http://example.com/{quip['timestamp']}.mp3",
        }

    monkeypatch.setattr(llm_module, "generate_event_timeline", fake_generate_event_timeline)
    monkeypatch.setattr(tts_module, "generate_audio_clip", fake_generate_audio_clip)

    result = await commentary_module.process_video_commentary("fake.mp4")

    assert isinstance(result, CommentaryResponse)
    assert result.quips[0].audio_url == "http://example.com/0.0.mp3"
    assert result.quips[1].text == "second quip"


def test_ws_analyze_returns_final_payload(monkeypatch):
    async def fake_process_video_commentary(_):
        return CommentaryResponse(quips=[CommentaryQuip(timestamp=1.25, text="quips", audio_url="http://example.com/clip.mp3")])

    monkeypatch.setattr("backend.main.process_video_commentary", fake_process_video_commentary)

    with client.websocket_connect("/ws/analyze") as websocket:
        websocket.send_json({"video_path": "fake.mp4"})
        first = websocket.receive_json()
        second = websocket.receive_json()
        third = websocket.receive_json()
        fourth = websocket.receive_json()

    assert first["status"] == "processing"
    assert first["message"] == "extracting"
    assert fourth["status"] == "completed"
    assert fourth["quips"][0]["text"] == "quips"
