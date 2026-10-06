import asyncio
import time

import pytest

from app.schemas.events import CommentaryResponse
from app.services.jobs import JobNotFoundError, JobStore


@pytest.fixture
def store():
    # Reset store for each test
    store_instance = JobStore()
    store_instance._jobs.clear()
    store_instance._subscribers.clear()
    return store_instance


@pytest.mark.anyio
async def test_create_and_get(store):
    job = store.create("video.mp4")
    assert job.job_id is not None
    assert job.video_path == "video.mp4"
    assert job.status == "uploading"
    assert job.progress == 0
    
    retrieved = store.get(job.job_id)
    assert retrieved is job


@pytest.mark.anyio
async def test_get_unknown_raises(store):
    with pytest.raises(JobNotFoundError):
        store.get("nonexistent")


@pytest.mark.anyio
async def test_duplicate_id_raises(store):
    job = store.create("video.mp4", job_id="fixed-id")
    with pytest.raises(ValueError):
        store.create("video2.mp4", job_id="fixed-id")


@pytest.mark.anyio
async def test_invalid_status_raises(store):
    job = store.create("video.mp4")
    with pytest.raises(ValueError):
        store.update(job.job_id, "invalid_status", 50)


@pytest.mark.anyio
async def test_progress_clamping_and_monotonicity(store):
    job = store.create("video.mp4")
    store.update(job.job_id, "extracting", 150)
    assert job.progress == 100
    
    store.update(job.job_id, "analyzing", 50)
    assert job.progress == 100  # monotonicity
    
    store.update(job.job_id, "error", 10)
    assert job.progress == 10  # error can lower progress


@pytest.mark.anyio
async def test_terminal_jobs_ignore_updates_and_publish_nothing(store):
    job = store.create("video.mp4")
    store.complete(job.job_id, CommentaryResponse.model_construct(quips=[]))
    assert job.status == "completed"
    
    # Try to update terminal job
    store.update(job.job_id, "analyzing", 50)
    assert job.status == "completed"
    assert job.progress == 100
    
    # Subscribe and check no new messages after terminal
    q = store.subscribe(job.job_id)
    assert q.qsize() == 1  # seeded snapshot
    store.update(job.job_id, "extracting", 10)
    assert q.qsize() == 1  # no new message


@pytest.mark.anyio
async def test_subscribe_delivers_seeded_and_live_updates(store):
    job = store.create("video.mp4")
    q = store.subscribe(job.job_id)
    
    # Seeded snapshot
    snap = await q.get()
    assert snap["status"] == "uploading"
    assert snap["progress"] == 0
    
    # Live update
    store.update(job.job_id, "extracting", 30)
    snap2 = await q.get()
    assert snap2["status"] == "extracting"
    assert snap2["progress"] == 30


@pytest.mark.anyio
async def test_unsubscribe_is_idempotent(store):
    job = store.create("video.mp4")
    q = store.subscribe(job.job_id)
    store.unsubscribe(job.job_id, q)
    store.unsubscribe(job.job_id, q)  # should not raise
    store.unsubscribe("nonexistent", q)  # should not raise


@pytest.mark.anyio
async def test_purge_expired_removes_only_expired_terminal_jobs(store):
    job1 = store.create("video1.mp4")
    store.complete(job1.job_id, CommentaryResponse.model_construct(quips=[]))
    job1.updated_at = time.time() - 7200  # 2 hours ago
    
    job2 = store.create("video2.mp4")
    store.complete(job2.job_id, CommentaryResponse.model_construct(quips=[]))
    # job2.updated_at is recent
    
    purged = store.purge_expired()
    assert job1.job_id in purged
    assert job2.job_id not in purged
    assert job1.job_id not in store._jobs
    assert job2.job_id in store._jobs


@pytest.mark.anyio
async def test_fail_sets_error_status_and_message(store):
    job = store.create("video.mp4")
    store.fail(job.job_id, "Disk full")
    assert job.status == "error"
    assert job.message == "Disk full"
    
    store.fail(job.job_id, "")
    assert job.message == "Processing failed"


@pytest.mark.anyio
async def test_complete_stores_result(store):
    job = store.create("video.mp4")
    result = CommentaryResponse.model_construct(quips=[])
    store.complete(job.job_id, result)
    assert job.status == "completed"
    assert job.result is result
    assert job.progress == 100
    assert job.message == "Commentary ready"
