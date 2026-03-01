import pytest

from app.core.jobs.store import JobStore
from app.core.models import JobStatus


@pytest.fixture
def job_store(tmp_media):
    store = JobStore.__new__(JobStore)
    store.status_dir = tmp_media / "job-data" / "status"
    return store


def _make_job(job_id="job-1", status="pending"):
    return JobStatus(job_id=job_id, status=status, overall_percent=0.0)


def test_save_job_writes_file(job_store, tmp_media):
    job = _make_job("save-test")
    job_store.save_job(job)

    status_file = tmp_media / "job-data" / "status" / "save-test.json"
    assert status_file.exists()


def test_get_job_reads_correct_data(job_store):
    job = _make_job("get-test", status="processing")
    job_store.save_job(job)

    retrieved = job_store.get_job("get-test")
    assert retrieved is not None
    assert retrieved.job_id == "get-test"
    assert retrieved.status == "processing"


def test_get_nonexistent_job_returns_none(job_store):
    result = job_store.get_job("does-not-exist")
    assert result is None


def test_list_jobs_returns_all_saved(job_store):
    job_store.save_job(_make_job("list-a", "pending"))
    job_store.save_job(_make_job("list-b", "completed"))

    jobs = job_store.list_jobs()
    ids = {j.job_id for j in jobs}
    assert "list-a" in ids
    assert "list-b" in ids


def test_list_active_jobs_returns_only_pending_and_processing(job_store):
    job_store.save_job(_make_job("active-pending", "pending"))
    job_store.save_job(_make_job("active-processing", "processing"))
    job_store.save_job(_make_job("active-completed", "completed"))
    job_store.save_job(_make_job("active-failed", "failed"))

    active = job_store.list_active_jobs()
    active_ids = {j.job_id for j in active}

    assert "active-pending" in active_ids
    assert "active-processing" in active_ids
    assert "active-completed" not in active_ids
    assert "active-failed" not in active_ids
