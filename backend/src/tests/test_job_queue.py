import json
import uuid
from unittest.mock import patch

import pytest

from app.core.jobs.queue import JobQueue
from app.core.models import ProcessRequest


@pytest.fixture
def queue(tmp_media):
    q = JobQueue.__new__(JobQueue)
    q.pending_dir = tmp_media / "job-data" / "pending"
    return q


@pytest.fixture
def mock_job_store():
    with patch("app.core.jobs.queue.job_store") as mock:
        yield mock


async def test_enqueue_returns_valid_uuid(queue, mock_job_store):
    request = ProcessRequest(
        dir="Movies",
        output_dir="Output",
        audio_languages=["eng"],
        subtitle_languages=["eng"],
    )

    job_id = await queue.enqueue(request)

    uuid.UUID(job_id)  # raises ValueError if not a valid UUID


async def test_enqueue_creates_pending_file(queue, mock_job_store, tmp_media):
    request = ProcessRequest(
        dir="Movies",
        output_dir="Output",
        audio_languages=["eng"],
        subtitle_languages=["eng"],
    )

    job_id = await queue.enqueue(request)

    pending_file = tmp_media / "job-data" / "pending" / f"{job_id}.json"
    assert pending_file.exists()

    with open(pending_file) as f:
        payload = json.load(f)

    assert payload["job_id"] == job_id
    assert payload["output_dir"] == "Output"
    assert payload["audio_languages"] == ["eng"]


async def test_enqueue_saves_job_with_pending_status(queue, mock_job_store):
    request = ProcessRequest(
        dir="Movies",
        output_dir="Output",
        audio_languages=["eng"],
        subtitle_languages=["eng"],
    )

    await queue.enqueue(request)

    mock_job_store.save_job.assert_called_once()
    saved_job = mock_job_store.save_job.call_args[0][0]
    assert saved_job.status == "pending"
    assert saved_job.overall_percent == 0.0
