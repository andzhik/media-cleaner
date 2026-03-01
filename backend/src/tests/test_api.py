import pytest
from unittest.mock import patch, AsyncMock

from app.core.models import StreamInfo, JobStatus


@pytest.fixture(scope="session", autouse=True)
def setup_movies_dir(tmp_media):
    movie_dir = tmp_media / "input" / "Movies"
    movie_dir.mkdir(exist_ok=True)
    (movie_dir / "test_movie.mkv").touch()


def test_root(app_client):
    response = app_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Video Cleaner API is running"}


def test_get_tree(app_client):
    response = app_client.get("/api/tree")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "/"
    assert data["children"] is not None
    assert any(child["name"] == "Movies" for child in data["children"]), \
        "Movies directory not found in tree"


@patch("app.api.routes_list.probe_file", new_callable=AsyncMock)
def test_list_directory(mock_probe, app_client):
    mock_probe.return_value = {
        "audio": [StreamInfo(id=0, language="eng", title="Stereo", codec_type="audio")],
        "subtitle": [StreamInfo(id=0, language="eng", title="English", codec_type="subtitle")],
    }

    response = app_client.get("/api/list?dir=Movies")
    assert response.status_code == 200
    data = response.json()

    assert data["dir"] == "Movies"
    assert len(data["files"]) == 1
    assert data["files"][0]["name"] == "test_movie.mkv"
    assert "eng" in data["languages"]

    mock_probe.assert_called_once()


@patch("app.api.routes_process.job_queue")
def test_start_process(mock_job_queue, app_client):
    mock_job_queue.enqueue = AsyncMock(return_value="test-job-id")

    payload = {
        "dir": "Movies",
        "files": ["Movies/test_movie.mkv"],
        "output_dir": "Output",
        "audio_languages": ["eng"],
        "subtitle_languages": ["eng"],
    }

    response = app_client.post("/api/process", json=payload)
    assert response.status_code == 200
    assert response.json() == {"jobId": "test-job-id"}

    mock_job_queue.enqueue.assert_called_once()


@patch("app.api.routes_jobs.job_store")
def test_get_job_status(mock_job_store, app_client):
    mock_job = JobStatus(
        job_id="test-job-id",
        status="processing",
        overall_percent=50.0,
        current_file="test.mkv",
        logs=[],
    )

    mock_job_store.get_job.return_value = mock_job

    response = app_client.get("/api/jobs/test-job-id")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "test-job-id"
    assert data["status"] == "processing"


def test_list_directory_invalid_path(app_client):
    response = app_client.get("/api/list?dir=InvalidPath")
    assert response.status_code == 400
