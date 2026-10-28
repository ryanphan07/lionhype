import pytest


@pytest.fixture(autouse=True)
def clean_job_store():
    """The module-level job_store is shared; unfinished jobs from one test must not block uploads in the next."""
    from app.services.jobs import job_store

    job_store._jobs.clear()
    job_store._subscribers.clear()
    yield
    job_store._jobs.clear()
    job_store._subscribers.clear()
