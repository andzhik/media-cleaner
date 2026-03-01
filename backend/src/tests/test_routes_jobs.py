import asyncio
import json
from unittest.mock import patch, AsyncMock, MagicMock

from app.core.models import JobStatus


def _make_job(job_id="job-1", status="pending"):
    return JobStatus(job_id=job_id, status=status, overall_percent=0.0)


# --- GET /api/jobs/{job_id} ---

def test_get_job_status_not_found(app_client):
    with patch("app.api.routes_jobs.job_store") as mock_store:
        mock_store.get_job.return_value = None
        response = app_client.get("/api/jobs/no-such-job")
    assert response.status_code == 404


# --- DELETE /api/jobs/{job_id} ---

def test_cancel_job_not_found(app_client):
    with patch("app.api.routes_jobs.job_store") as mock_store:
        mock_store.get_job.return_value = None
        response = app_client.delete("/api/jobs/no-such-job")
    assert response.status_code == 404


def test_cancel_job_not_pending_returns_409(app_client):
    with patch("app.api.routes_jobs.job_store") as mock_store:
        mock_store.get_job.return_value = _make_job("j1", "processing")
        response = app_client.delete("/api/jobs/j1")
    assert response.status_code == 409


def test_cancel_job_completed_returns_409(app_client):
    with patch("app.api.routes_jobs.job_store") as mock_store:
        mock_store.get_job.return_value = _make_job("j1", "completed")
        response = app_client.delete("/api/jobs/j1")
    assert response.status_code == 409


def test_cancel_job_success_returns_ok(app_client, tmp_media):
    job_id = "cancel-test"
    pending_file = tmp_media / "job-data" / "pending" / f"{job_id}.json"
    pending_file.write_text("{}")

    with patch("app.api.routes_jobs.job_store") as mock_store, \
         patch("app.api.routes_jobs.event_manager") as mock_em:
        mock_store.get_job.return_value = _make_job(job_id, "pending")
        mock_store.list_active_jobs.return_value = []
        mock_em.emit_global = AsyncMock()

        response = app_client.delete(f"/api/jobs/{job_id}")

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_cancel_job_deletes_pending_file(app_client, tmp_media):
    job_id = "cancel-file-test"
    job_data_root = tmp_media / "job-data"
    pending_file = job_data_root / "pending" / f"{job_id}.json"
    pending_file.write_text("{}")

    with patch("app.api.routes_jobs.job_store") as mock_store, \
         patch("app.api.routes_jobs.event_manager") as mock_em, \
         patch("app.api.routes_jobs.JOB_DATA_ROOT", job_data_root):
        mock_store.get_job.return_value = _make_job(job_id, "pending")
        mock_store.list_active_jobs.return_value = []
        mock_em.emit_global = AsyncMock()

        app_client.delete(f"/api/jobs/{job_id}")

    assert not pending_file.exists()


def test_cancel_job_deletes_status_file(app_client, tmp_media):
    job_id = "cancel-status-test"
    job_data_root = tmp_media / "job-data"
    status_file = job_data_root / "status" / f"{job_id}.json"
    status_file.write_text("{}")

    with patch("app.api.routes_jobs.job_store") as mock_store, \
         patch("app.api.routes_jobs.event_manager") as mock_em, \
         patch("app.api.routes_jobs.JOB_DATA_ROOT", job_data_root):
        mock_store.get_job.return_value = _make_job(job_id, "pending")
        mock_store.list_active_jobs.return_value = []
        mock_em.emit_global = AsyncMock()

        app_client.delete(f"/api/jobs/{job_id}")

    assert not status_file.exists()


def test_cancel_job_emits_global_event(app_client, tmp_media):
    job_id = "cancel-emit-test"

    with patch("app.api.routes_jobs.job_store") as mock_store, \
         patch("app.api.routes_jobs.event_manager") as mock_em:
        active_jobs = [_make_job("other-job", "processing")]
        mock_store.get_job.return_value = _make_job(job_id, "pending")
        mock_store.list_active_jobs.return_value = active_jobs
        mock_em.emit_global = AsyncMock()

        app_client.delete(f"/api/jobs/{job_id}")

        mock_em.emit_global.assert_called_once_with(active_jobs)


def test_cancel_job_missing_files_does_not_raise(app_client, tmp_media):
    """cancel_job uses unlink(missing_ok=True) so absent files are fine."""
    job_id = "cancel-no-files"

    with patch("app.api.routes_jobs.job_store") as mock_store, \
         patch("app.api.routes_jobs.event_manager") as mock_em:
        mock_store.get_job.return_value = _make_job(job_id, "pending")
        mock_store.list_active_jobs.return_value = []
        mock_em.emit_global = AsyncMock()

        response = app_client.delete(f"/api/jobs/{job_id}")

    assert response.status_code == 200


# --- GET /api/jobs/{job_id}/events ---

def test_job_events_not_found(app_client):
    with patch("app.api.routes_jobs.job_store") as mock_store:
        mock_store.get_job.return_value = None
        response = app_client.get("/api/jobs/no-such-job/events")
    assert response.status_code == 404


# --- GET /api/jobs/{job_id}/events  SSE generator ---
#
# Strategy: patch EventSourceResponse in routes_jobs so we capture the raw
# async generator before it is wrapped.  We then consume the generator
# directly in the same event loop as the test, which lets us assert on the
# exact dicts that the generator yields and on cleanup calls.

def _fake_esr(captured: dict):
    """Return a replacement for EventSourceResponse that saves the generator."""
    def _inner(gen):
        captured["gen"] = gen
        return MagicMock()
    return _inner


async def _drain(gen) -> list:
    events = []
    async for event in gen:
        events.append(event)
    return events


async def test_job_events_generator_yields_initial_then_terminates_on_completed():
    from app.api.routes_jobs import job_events

    processing = _make_job("j1", "processing")
    completed = _make_job("j1", "completed")

    q = asyncio.Queue()
    await q.put(completed)

    captured = {}
    with patch("app.api.routes_jobs.EventSourceResponse", _fake_esr(captured)), \
         patch("app.api.routes_jobs.job_store") as mock_store, \
         patch("app.api.routes_jobs.event_manager") as mock_em:
        mock_store.get_job.return_value = processing
        mock_em.subscribe = AsyncMock(return_value=q)
        mock_em.unsubscribe = AsyncMock()

        await job_events("j1")
        events = await _drain(captured["gen"])

    assert len(events) == 2
    assert events[0] == {"event": "status", "data": processing.model_dump_json()}
    assert events[1] == {"event": "status", "data": completed.model_dump_json()}
    # finally block calls unsubscribe once (no CancelledError)
    mock_em.unsubscribe.assert_called_once_with("j1", q)


async def test_job_events_generator_terminates_on_failed_status():
    from app.api.routes_jobs import job_events

    job = _make_job("j1", "processing")
    failed = _make_job("j1", "failed")

    q = asyncio.Queue()
    await q.put(failed)

    captured = {}
    with patch("app.api.routes_jobs.EventSourceResponse", _fake_esr(captured)), \
         patch("app.api.routes_jobs.job_store") as mock_store, \
         patch("app.api.routes_jobs.event_manager") as mock_em:
        mock_store.get_job.return_value = job
        mock_em.subscribe = AsyncMock(return_value=q)
        mock_em.unsubscribe = AsyncMock()

        await job_events("j1")
        events = await _drain(captured["gen"])

    assert len(events) == 2
    assert "failed" in events[1]["data"]
    mock_em.unsubscribe.assert_called_once_with("j1", q)


async def test_job_events_generator_yields_multiple_updates_before_completed():
    from app.api.routes_jobs import job_events

    job = _make_job("j1", "processing")
    mid = JobStatus(job_id="j1", status="processing", overall_percent=50.0)
    completed = _make_job("j1", "completed")

    q = asyncio.Queue()
    await q.put(mid)
    await q.put(completed)

    captured = {}
    with patch("app.api.routes_jobs.EventSourceResponse", _fake_esr(captured)), \
         patch("app.api.routes_jobs.job_store") as mock_store, \
         patch("app.api.routes_jobs.event_manager") as mock_em:
        mock_store.get_job.return_value = job
        mock_em.subscribe = AsyncMock(return_value=q)
        mock_em.unsubscribe = AsyncMock()

        await job_events("j1")
        events = await _drain(captured["gen"])

    assert len(events) == 3  # initial + mid-update + completed
    assert "50" in events[1]["data"]
    assert "completed" in events[2]["data"]


async def test_job_events_generator_handles_cancelled_error():
    from app.api.routes_jobs import job_events

    job = _make_job("j1", "processing")

    async def raise_cancelled():
        raise asyncio.CancelledError()

    q = asyncio.Queue()
    q.get = raise_cancelled

    captured = {}
    with patch("app.api.routes_jobs.EventSourceResponse", _fake_esr(captured)), \
         patch("app.api.routes_jobs.job_store") as mock_store, \
         patch("app.api.routes_jobs.event_manager") as mock_em:
        mock_store.get_job.return_value = job
        mock_em.subscribe = AsyncMock(return_value=q)
        mock_em.unsubscribe = AsyncMock()

        await job_events("j1")
        events = await _drain(captured["gen"])

    # Only the initial status yielded before CancelledError
    assert len(events) == 1
    assert events[0]["event"] == "status"
    # unsubscribe called from both the except block and the finally block
    assert mock_em.unsubscribe.call_count == 2


# --- GET /api/jobs/events  SSE generator ---

async def test_jobs_list_events_yields_initial_snapshot():
    from app.api.routes_jobs import jobs_list_events

    active = [_make_job("j1", "pending")]

    async def raise_cancelled():
        raise asyncio.CancelledError()

    q = asyncio.Queue()
    q.get = raise_cancelled  # terminate after the initial yield

    captured = {}
    with patch("app.api.routes_jobs.EventSourceResponse", _fake_esr(captured)), \
         patch("app.api.routes_jobs.job_store") as mock_store, \
         patch("app.api.routes_jobs.event_manager") as mock_em:
        mock_store.list_active_jobs.return_value = active
        mock_em.subscribe_global = AsyncMock(return_value=q)
        mock_em.unsubscribe_global = AsyncMock()

        await jobs_list_events()
        events = await _drain(captured["gen"])

    assert len(events) == 1
    assert events[0]["event"] == "jobs_list"
    data = json.loads(events[0]["data"])
    assert data[0]["job_id"] == "j1"
    mock_em.unsubscribe_global.assert_called_once_with(q)


async def test_jobs_list_events_yields_updates_from_queue():
    from app.api.routes_jobs import jobs_list_events

    initial = [_make_job("j1", "pending")]
    updated = [_make_job("j1", "processing")]

    get_count = 0

    async def patched_get():
        nonlocal get_count
        get_count += 1
        if get_count == 1:
            return updated
        raise asyncio.CancelledError()

    q = asyncio.Queue()
    q.get = patched_get

    captured = {}
    with patch("app.api.routes_jobs.EventSourceResponse", _fake_esr(captured)), \
         patch("app.api.routes_jobs.job_store") as mock_store, \
         patch("app.api.routes_jobs.event_manager") as mock_em:
        mock_store.list_active_jobs.return_value = initial
        mock_em.subscribe_global = AsyncMock(return_value=q)
        mock_em.unsubscribe_global = AsyncMock()

        await jobs_list_events()
        events = await _drain(captured["gen"])

    assert len(events) == 2
    assert events[0]["event"] == "jobs_list"
    assert events[1]["event"] == "jobs_list"
    assert json.loads(events[0]["data"])[0]["status"] == "pending"
    assert json.loads(events[1]["data"])[0]["status"] == "processing"
    mock_em.unsubscribe_global.assert_called_once_with(q)
