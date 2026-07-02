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

    with open(pending_file, encoding="utf-8") as f:
        payload = json.load(f)

    assert payload["job_id"] == job_id
    assert payload["output_dir"] == "Output"
    assert payload["audio_languages"] == ["eng"]


async def test_enqueue_preserves_unicode_selection_path(queue, mock_job_store, tmp_media):
    path = "/Silo.S01.720p.WEBRip.Невафильм/Silo.S01E01.720p.NF.mkv"
    request = ProcessRequest(
        output_dir="Output",
        audio_languages=["eng"],
        subtitle_languages=["eng"],
        selections=[
            {
                "rel_path": path,
                "audio_stream_ids": [1],
                "subtitle_stream_ids": [2],
            }
        ],
    )

    job_id = await queue.enqueue(request)

    saved_job = mock_job_store.save_job.call_args[0][0]
    assert saved_job.first_file == path

    pending_file = tmp_media / "job-data" / "pending" / f"{job_id}.json"
    with open(pending_file, encoding="utf-8") as f:
        payload = json.load(f)

    assert payload["selections"][0]["rel_path"] == path


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
