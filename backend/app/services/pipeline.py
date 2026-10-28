import logging
import os
import shutil
from typing import Optional

from app.config import settings
from app.services.commentary import process_video_commentary
from app.services.llm import LLMOutputError
from app.services.jobs import job_store

logger = logging.getLogger("lionhype.pipeline")


GENERIC_FAILURE = "Commentary generation failed"


def friendly_error(exc: BaseException) -> str:
    """A safe, user-facing reason for a failed job. Details stay in the server log."""
    try:
        import openai
    except ImportError:  # pragma: no cover
        openai = None
    if openai is not None and isinstance(exc, (openai.APIConnectionError, openai.APIStatusError)):
        return "The AI model is not reachable or timed out. Is llama-server running?"
    if isinstance(exc, LLMOutputError):
        return "The AI model returned unusable output. Try again."
    if isinstance(exc, ValueError):
        return "The video could not be processed."
    return GENERIC_FAILURE


def cleanup_job_files(job_id: str, video_path: str) -> None:
    """Delete the job's video, frames dir and audio dir. Never raises."""
    if os.path.exists(video_path):
        try:
            os.remove(video_path)
        except OSError:
            logger.exception("Could not delete video for job %s", job_id)
    for sub in ("frames", "audio"):
        shutil.rmtree(os.path.join(settings.UPLOAD_DIR, sub, job_id), ignore_errors=True)


def sweep_uploads() -> int:
    """Delete leftover videos and audio from earlier runs. Call at startup, when the in-memory job store is empty."""
    removed = 0
    for sub in ("videos", "audio"):
        folder = os.path.join(settings.UPLOAD_DIR, sub)
        if not os.path.isdir(folder):
            continue
        for entry in os.scandir(folder):
            try:
                if entry.is_dir(follow_symlinks=False):
                    shutil.rmtree(entry.path)
                else:
                    os.remove(entry.path)
                removed += 1
            except OSError:
                logger.warning("Could not delete leftover %s", entry.path)
    if removed:
        logger.info("Startup sweep removed %d leftover upload entries", removed)
    return removed


async def run_pipeline(job_id: str, video_path: str) -> None:
    async def progress_cb(status: str, progress: int, message: Optional[str] = None) -> None:
        try:
            job_store.update(job_id, status, progress, message)
        except Exception:
            logger.warning("Progress update failed for job %s", job_id, exc_info=True)

    try:
        result = await process_video_commentary(video_path, job_id=job_id, progress_cb=progress_cb)
        job_store.complete(job_id, result)
        try:
            os.remove(video_path)  # the browser plays its own copy; nothing reads the source again
        except OSError:
            logger.warning("Could not delete video for job %s", job_id)
    except Exception as exc:
        logger.exception("Commentary generation failed for job %s", job_id)
        try:
            job_store.fail(job_id, friendly_error(exc))
        finally:
            cleanup_job_files(job_id, video_path)
