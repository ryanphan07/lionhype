import logging
import os
import shutil
from typing import Optional

from app.config import settings
from app.services.commentary import process_video_commentary
from app.services.jobs import job_store

logger = logging.getLogger("lionhype.pipeline")


def cleanup_job_files(job_id: str, video_path: str) -> None:
    """Delete the job's video, frames dir and audio dir. Never raises."""
    if os.path.exists(video_path):
        try:
            os.remove(video_path)
        except OSError:
            logger.exception("Could not delete video for job %s", job_id)
    for sub in ("frames", "audio"):
        shutil.rmtree(os.path.join(settings.UPLOAD_DIR, sub, job_id), ignore_errors=True)


async def run_pipeline(job_id: str, video_path: str) -> None:
    async def progress_cb(status: str, progress: int, message: Optional[str] = None) -> None:
        try:
            job_store.update(job_id, status, progress, message)
        except Exception:
            logger.warning("Progress update failed for job %s", job_id, exc_info=True)

    try:
        result = await process_video_commentary(video_path, job_id=job_id, progress_cb=progress_cb)
        job_store.complete(job_id, result)
    except Exception:
        logger.exception("Commentary generation failed for job %s", job_id)
        try:
            job_store.fail(job_id, "Commentary generation failed")
        finally:
            cleanup_job_files(job_id, video_path)
