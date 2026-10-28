"""
Job management for video commentary processing.
Uses a single event loop, so no threading locks are required.
"""

import asyncio
import logging
import time
import uuid
from typing import Optional

from pydantic import BaseModel, Field

from app.config import settings
from app.schemas.events import CommentaryResponse

logger = logging.getLogger("lionhype.jobs")

PHASES = ("uploading", "extracting", "analyzing", "synthesizing", "completed", "error")
TERMINAL = {"completed", "error"}


class JobNotFoundError(KeyError):
    pass


class Job(BaseModel):
    job_id: str
    video_path: str
    status: str = "uploading"
    progress: int = 0
    message: Optional[str] = None
    result: Optional[CommentaryResponse] = None
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


def snapshot(job: Job) -> dict:
    data = {"status": job.status, "progress": job.progress}
    if job.message is not None:
        data["message"] = job.message
    return data


class JobStore:
    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._subscribers: dict[str, list[asyncio.Queue]] = {}

    def create(self, video_path: str, job_id: Optional[str] = None) -> Job:
        self.purge_expired()
        if job_id is None:
            job_id = str(uuid.uuid4())
        if job_id in self._jobs:
            raise ValueError(f"Job {job_id} already exists")
        job = Job(job_id=job_id, video_path=video_path)
        self._jobs[job_id] = job
        logger.info(f"Created job {job_id}")
        return job

    def get(self, job_id: str) -> Job:
        if job_id not in self._jobs:
            raise JobNotFoundError(job_id)
        return self._jobs[job_id]

    def update(self, job_id: str, status: str, progress: int, message: Optional[str] = None) -> Job:
        if status not in PHASES:
            raise ValueError(f"Invalid status: {status}")
        
        job = self.get(job_id)
        
        if job.status in TERMINAL:
            logger.debug(f"Job {job_id} is already terminal, ignoring update")
            return job

        # Clamp progress
        progress = max(0, min(100, progress))
        
        # Monotonicity for non-error updates
        if status != "error":
            progress = max(job.progress, progress)
            
        job.status = status
        job.progress = progress
        if message is not None:
            job.message = message
        job.updated_at = time.time()
        
        # Publish to subscribers
        if job_id in self._subscribers:
            snap = snapshot(job)
            for q in self._subscribers[job_id]:
                q.put_nowait(snap)
                
        return job

    def complete(self, job_id: str, result: CommentaryResponse):
        job = self.get(job_id)
        if job.status not in TERMINAL:
            job.result = result
            self.update(job_id, "completed", 100, "Commentary ready")

    def fail(self, job_id: str, message: str):
        if not message:
            message = "Processing failed"
        job = self.get(job_id)
        if job.status in TERMINAL:
            job.message = message
            job.updated_at = time.time()
            return job
        self.update(job_id, "error", job.progress, message)

    def subscribe(self, job_id: str) -> asyncio.Queue:
        job = self.get(job_id)
        q = asyncio.Queue()
        q.put_nowait(snapshot(job))
        if job_id not in self._subscribers:
            self._subscribers[job_id] = []
        self._subscribers[job_id].append(q)
        return q

    def unsubscribe(self, job_id: str, queue: asyncio.Queue):
        if job_id in self._subscribers:
            try:
                self._subscribers[job_id].remove(queue)
            except ValueError:
                pass

    def video_paths(self) -> dict[str, str]:
        return {job_id: job.video_path for job_id, job in self._jobs.items()}

    def purge_expired(self) -> list[str]:
        now = time.time()
        purged = []
        for job_id, job in list(self._jobs.items()):
            if job.status in TERMINAL and (now - job.updated_at) > settings.JOB_TTL_SECONDS:
                del self._jobs[job_id]
                self._subscribers.pop(job_id, None)
                purged.append(job_id)
        return purged


job_store = JobStore()
