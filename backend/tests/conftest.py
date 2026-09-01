import pytest
import os

@pytest.fixture(scope="session", autouse=True)
def create_test_video():
    # Create a dummy video file for testing
    with open("test_video.mp4", "wb") as f:
        f.write(b"dummy video data")

    yield

    # Clean up the dummy video file after tests
    os.remove("test_video.mp4")
