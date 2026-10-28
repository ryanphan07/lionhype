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


@pytest.fixture(autouse=True)
def clean_job_store():
    """The module-level job_store is shared; unfinished jobs from one test must not block uploads in the next."""
    from app.services.jobs import job_store

    job_store._jobs.clear()
    job_store._subscribers.clear()
    yield
    job_store._jobs.clear()
    job_store._subscribers.clear()
