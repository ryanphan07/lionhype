import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_upload_video():
    test_file = open("test_video.mp4", "rb")
    response = client.post("/api/upload", files={"file": ("test_video.mp4", test_file, "video/mp4")})
    test_file.close()

    assert response.status_code == 200
    assert "video_id" in response.json()
    assert "frame_paths" in response.json()
