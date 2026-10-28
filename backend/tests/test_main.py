import base64

import numpy as np
import pytest
from app.schemas.events import CommentaryResponse
from app.services import commentary as commentary_module
from app.services import llm as llm_module
from app.services import tts as tts_module
from app.services import video_processor


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


async def fake_tts(quip, video_id=None):
    return {"timestamp": quip["timestamp"], "text": quip["text"], "audio_url": "http://example.com/clip.mp3"}


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


@pytest.mark.anyio
async def test_job_id_forwarded_to_tts(monkeypatch):
    captured_video_id = []
    async def fake_generate_audio_clip(quip, video_id=None):
        captured_video_id.append(video_id)
        return {"timestamp": quip["timestamp"], "text": quip["text"], "audio_url": "http://example.com/clip.mp3"}
    
    monkeypatch.setattr(commentary_module.video_processor_service, "extract_frames", lambda _: [{"timestamp": 0.0, "image_data": "abc"}])
    async def fake_llm(frames): return [{"timestamp": 0.0, "text": "quip"}]
    monkeypatch.setattr(llm_module, "generate_event_timeline", fake_llm)
    monkeypatch.setattr(tts_module, "generate_audio_clip", fake_generate_audio_clip)

    await commentary_module.process_video_commentary("fake.mp4", job_id="job-123")
    assert captured_video_id == ["job-123"]


@pytest.mark.anyio
async def test_progress_cb_receives_statuses_in_order(monkeypatch):
    statuses = []
    async def fake_progress_cb(status, progress, message=None):
        statuses.append(status)
        
    monkeypatch.setattr(commentary_module.video_processor_service, "extract_frames", lambda _: [{"timestamp": 0.0, "image_data": "abc"}])
    async def fake_llm(frames): return [{"timestamp": 0.0, "text": "quip"}]
    monkeypatch.setattr(llm_module, "generate_event_timeline", fake_llm)
    monkeypatch.setattr(tts_module, "generate_audio_clip", fake_tts)

    await commentary_module.process_video_commentary("fake.mp4", progress_cb=fake_progress_cb)
    
    assert "extracting" in statuses
    assert "analyzing" in statuses
    assert "synthesizing" in statuses
    assert "completed" not in statuses
    assert statuses.index("extracting") < statuses.index("analyzing") < statuses.index("synthesizing")


@pytest.mark.anyio
async def test_progress_cb_raises_does_not_break_pipeline(monkeypatch):
    async def fake_progress_cb(status, progress, message=None):
        if status == "extracting":
            raise RuntimeError("Callback failed")
            
    monkeypatch.setattr(commentary_module.video_processor_service, "extract_frames", lambda _: [{"timestamp": 0.0, "image_data": "abc"}])
    async def fake_llm(frames): return [{"timestamp": 0.0, "text": "quip"}]
    monkeypatch.setattr(llm_module, "generate_event_timeline", fake_llm)
    monkeypatch.setattr(tts_module, "generate_audio_clip", fake_tts)

    result = await commentary_module.process_video_commentary("fake.mp4", progress_cb=fake_progress_cb)
    assert isinstance(result, CommentaryResponse)
    assert len(result.quips) == 1
    assert result.quips[0].audio_url == "http://example.com/clip.mp3"


@pytest.mark.anyio
async def test_one_failing_tts_call_leaves_audio_url_none(monkeypatch):
    call_count = 0
    async def fake_generate_audio_clip(quip, video_id=None):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise RuntimeError("TTS failed")
        return {"timestamp": quip["timestamp"], "text": quip["text"], "audio_url": f"http://example.com/{quip['timestamp']}.mp3"}
        
    monkeypatch.setattr(commentary_module.video_processor_service, "extract_frames", lambda _: [
        {"timestamp": 0.0, "image_data": "abc"},
        {"timestamp": 1.0, "image_data": "def"},
    ])
    async def fake_llm(frames): return [
        {"timestamp": 0.0, "text": "quip1"},
        {"timestamp": 1.0, "text": "quip2"},
    ]
    monkeypatch.setattr(llm_module, "generate_event_timeline", fake_llm)
    monkeypatch.setattr(tts_module, "generate_audio_clip", fake_generate_audio_clip)

    result = await commentary_module.process_video_commentary("fake.mp4")
    assert result.quips[0].audio_url == "http://example.com/0.0.mp3"
    assert result.quips[1].audio_url is None


@pytest.mark.anyio
async def test_zero_frames_raises_valueerror_and_skips_llm(monkeypatch):
    llm_called = False
    async def fake_generate_event_timeline(frames):
        nonlocal llm_called
        llm_called = True
        return []
        
    monkeypatch.setattr(commentary_module.video_processor_service, "extract_frames", lambda _: [])
    monkeypatch.setattr(llm_module, "generate_event_timeline", fake_generate_event_timeline)

    with pytest.raises(ValueError, match="No frames could be extracted from video"):
        await commentary_module.process_video_commentary("fake.mp4")
        
    assert not llm_called


@pytest.mark.anyio
async def test_generate_audio_clip_rejects_invalid_video_id(monkeypatch):
    with pytest.raises(ValueError):
        await tts_module.generate_audio_clip({"timestamp": 0.0, "text": "test"}, video_id="../evil")
