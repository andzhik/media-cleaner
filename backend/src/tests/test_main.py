import asyncio
import time
from unittest.mock import patch, AsyncMock

import pytest

from app.core.models import JobStatus
from app.main import _cleanup_old_jobs, _poll_status_files


def _make_job(job_id="job-1", status="pending"):
    return JobStatus(job_id=job_id, status=status, overall_percent=0.0)


# ---------------------------------------------------------------------------
# _poll_status_files
# ---------------------------------------------------------------------------

async def test_poll_emits_update_for_new_status_file(tmp_path):
    status_dir = tmp_path / "status"
    status_dir.mkdir()

    job = JobStatus(job_id="poll-j1", status="processing", overall_percent=50.0)
    (status_dir / "poll-j1.json").write_text(job.model_dump_json())

    async def fake_sleep(_):
        raise asyncio.CancelledError()

    with patch("app.main.JOB_DATA_ROOT", tmp_path), \
         patch("app.main.event_manager") as mock_em, \
         patch("app.main.job_store") as mock_store, \
         patch("asyncio.sleep", fake_sleep):
        mock_em.emit_update = AsyncMock()
        mock_em.emit_global = AsyncMock()
        mock_store.list_active_jobs.return_value = [job]

        with pytest.raises(asyncio.CancelledError):
            await _poll_status_files()

    mock_em.emit_update.assert_called_once()
    emitted = mock_em.emit_update.call_args[0][0]
    assert emitted.job_id == "poll-j1"
    assert emitted.status == "processing"


async def test_poll_emits_global_when_files_change(tmp_path):
    status_dir = tmp_path / "status"
    status_dir.mkdir()

    job = _make_job("poll-j2")
    (status_dir / "poll-j2.json").write_text(job.model_dump_json())

    async def fake_sleep(_):
        raise asyncio.CancelledError()

    with patch("app.main.JOB_DATA_ROOT", tmp_path), \
         patch("app.main.event_manager") as mock_em, \
         patch("app.main.job_store") as mock_store, \
         patch("asyncio.sleep", fake_sleep):
        mock_em.emit_update = AsyncMock()
        mock_em.emit_global = AsyncMock()
        mock_store.list_active_jobs.return_value = [job]

        with pytest.raises(asyncio.CancelledError):
            await _poll_status_files()

    mock_em.emit_global.assert_called_once()


async def test_poll_skips_unchanged_files_on_second_iteration(tmp_path):
    status_dir = tmp_path / "status"
    status_dir.mkdir()

    job = _make_job("poll-j3")
    (status_dir / "poll-j3.json").write_text(job.model_dump_json())

    sleep_calls = 0

    async def fake_sleep(_):
        nonlocal sleep_calls
        sleep_calls += 1
        if sleep_calls >= 2:
            raise asyncio.CancelledError()

    with patch("app.main.JOB_DATA_ROOT", tmp_path), \
         patch("app.main.event_manager") as mock_em, \
         patch("app.main.job_store") as mock_store, \
         patch("asyncio.sleep", fake_sleep):
        mock_em.emit_update = AsyncMock()
        mock_em.emit_global = AsyncMock()
        mock_store.list_active_jobs.return_value = [job]

        with pytest.raises(asyncio.CancelledError):
            await _poll_status_files()

    # File seen on iteration 1, skipped on iteration 2
    assert mock_em.emit_update.call_count == 1


async def test_poll_handles_invalid_json_gracefully(tmp_path):
    status_dir = tmp_path / "status"
    status_dir.mkdir()

    (status_dir / "bad.json").write_text("not-valid-json")

    async def fake_sleep(_):
        raise asyncio.CancelledError()

    with patch("app.main.JOB_DATA_ROOT", tmp_path), \
         patch("app.main.event_manager") as mock_em, \
         patch("app.main.job_store") as mock_store, \
         patch("asyncio.sleep", fake_sleep):
        mock_em.emit_update = AsyncMock()
        mock_em.emit_global = AsyncMock()
        mock_store.list_active_jobs.return_value = []

        # Should not propagate any exception other than CancelledError
        with pytest.raises(asyncio.CancelledError):
            await _poll_status_files()

    # Bad JSON means emit_update is never called; emit_global IS called
    # because changed=True is set before the try block
    mock_em.emit_update.assert_not_called()
    mock_em.emit_global.assert_called_once()


async def test_poll_does_nothing_when_status_dir_absent(tmp_path):
    # status/ dir does not exist

    async def fake_sleep(_):
        raise asyncio.CancelledError()

    with patch("app.main.JOB_DATA_ROOT", tmp_path), \
         patch("app.main.event_manager") as mock_em, \
         patch("app.main.job_store") as mock_store, \
         patch("asyncio.sleep", fake_sleep):
        mock_em.emit_update = AsyncMock()
        mock_em.emit_global = AsyncMock()
        mock_store.list_active_jobs.return_value = []

        with pytest.raises(asyncio.CancelledError):
            await _poll_status_files()

    mock_em.emit_update.assert_not_called()
    mock_em.emit_global.assert_not_called()


# ---------------------------------------------------------------------------
# _cleanup_old_jobs
# ---------------------------------------------------------------------------

async def test_cleanup_deletes_expired_completed_job(tmp_path):
    completed_dir = tmp_path / "completed"
    status_dir = tmp_path / "status"
    completed_dir.mkdir()
    status_dir.mkdir()

    job_id = "old-completed"
    completed_file = completed_dir / f"{job_id}.json"
    status_file = status_dir / f"{job_id}.json"
    completed_file.write_text("{}")
    status_file.write_text("{}")

    # Make the file appear older than the 1-day TTL
    old_mtime = time.time() - 86401
    import os
    os.utime(completed_file, (old_mtime, old_mtime))

    sleep_calls = 0

    async def fake_sleep(_):
        nonlocal sleep_calls
        sleep_calls += 1
        if sleep_calls >= 2:
            raise asyncio.CancelledError()

    with patch("app.main.JOB_DATA_ROOT", tmp_path), \
         patch("asyncio.sleep", fake_sleep):
        with pytest.raises(asyncio.CancelledError):
            await _cleanup_old_jobs()

    assert not completed_file.exists()
    assert not status_file.exists()


async def test_cleanup_deletes_expired_failed_job(tmp_path):
    failed_dir = tmp_path / "failed"
    status_dir = tmp_path / "status"
    failed_dir.mkdir()
    status_dir.mkdir()

    job_id = "old-failed"
    failed_file = failed_dir / f"{job_id}.json"
    status_file = status_dir / f"{job_id}.json"
    failed_file.write_text("{}")
    status_file.write_text("{}")

    # Older than the 28-day TTL
    old_mtime = time.time() - (86400 * 28 + 1)
    import os
    os.utime(failed_file, (old_mtime, old_mtime))

    sleep_calls = 0

    async def fake_sleep(_):
        nonlocal sleep_calls
        sleep_calls += 1
        if sleep_calls >= 2:
            raise asyncio.CancelledError()

    with patch("app.main.JOB_DATA_ROOT", tmp_path), \
         patch("asyncio.sleep", fake_sleep):
        with pytest.raises(asyncio.CancelledError):
            await _cleanup_old_jobs()

    assert not failed_file.exists()
    assert not status_file.exists()


async def test_cleanup_keeps_recent_completed_job(tmp_path):
    completed_dir = tmp_path / "completed"
    status_dir = tmp_path / "status"
    completed_dir.mkdir()
    status_dir.mkdir()

    job_id = "recent-completed"
    completed_file = completed_dir / f"{job_id}.json"
    status_file = status_dir / f"{job_id}.json"
    completed_file.write_text("{}")
    status_file.write_text("{}")

    sleep_calls = 0

    async def fake_sleep(_):
        nonlocal sleep_calls
        sleep_calls += 1
        if sleep_calls >= 2:
            raise asyncio.CancelledError()

    with patch("app.main.JOB_DATA_ROOT", tmp_path), \
         patch("asyncio.sleep", fake_sleep):
        with pytest.raises(asyncio.CancelledError):
            await _cleanup_old_jobs()

    # File is new, should not be deleted
    assert completed_file.exists()
    assert status_file.exists()


async def test_cleanup_keeps_failed_job_within_ttl(tmp_path):
    failed_dir = tmp_path / "failed"
    status_dir = tmp_path / "status"
    failed_dir.mkdir()
    status_dir.mkdir()

    job_id = "recent-failed"
    failed_file = failed_dir / f"{job_id}.json"
    status_file = status_dir / f"{job_id}.json"
    failed_file.write_text("{}")
    status_file.write_text("{}")

    # 1 day old — within the 28-day TTL
    recent_mtime = time.time() - 86400
    import os
    os.utime(failed_file, (recent_mtime, recent_mtime))

    sleep_calls = 0

    async def fake_sleep(_):
        nonlocal sleep_calls
        sleep_calls += 1
        if sleep_calls >= 2:
            raise asyncio.CancelledError()

    with patch("app.main.JOB_DATA_ROOT", tmp_path), \
         patch("asyncio.sleep", fake_sleep):
        with pytest.raises(asyncio.CancelledError):
            await _cleanup_old_jobs()

    assert failed_file.exists()
    assert status_file.exists()


async def test_cleanup_handles_missing_subdirs_gracefully(tmp_path):
    # Neither completed/ nor failed/ exist

    sleep_calls = 0

    async def fake_sleep(_):
        nonlocal sleep_calls
        sleep_calls += 1
        if sleep_calls >= 2:
            raise asyncio.CancelledError()

    with patch("app.main.JOB_DATA_ROOT", tmp_path), \
         patch("asyncio.sleep", fake_sleep):
        with pytest.raises(asyncio.CancelledError):
            await _cleanup_old_jobs()
