import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import tempfile
import shutil
import os

# Set environment variables for testing BEFORE importing the app
# Use a temporary directory for INPUT_ROOT and OUTPUT_ROOT
temp_test_dir = tempfile.mkdtemp()
input_root = Path(temp_test_dir) / "input"
output_root = Path(temp_test_dir) / "output"
input_root.mkdir()
output_root.mkdir()

os.environ["INPUT_ROOT"] = str(input_root)
os.environ["OUTPUT_ROOT"] = str(output_root)

# Import the app after setting environment variables
from ..app.main import app
from ..app.core.config import settings

# Override settings just in case
settings.INPUT_ROOT = input_root
settings.OUTPUT_ROOT = output_root

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    # Setup: Create dummy files
    movie_dir = input_root / "Movies"
    movie_dir.mkdir()
    (movie_dir / "test_movie.mkv").touch()
    
    yield
    
    # Teardown: Remove temporary directory
    shutil.rmtree(temp_test_dir)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Video Cleaner API is running"}

def test_get_tree():
    response = client.get("/api/tree")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "ROOT"
    assert data["is_dir"] is True
    # Should see "Movies" directory
    assert any(child["name"] == "Movies" for child in data["children"]), "Movies directory not found in tree"

from ..app.core.models import StreamInfo, JobStatus

@patch("src.app.api.routes_list.probe_file")
def test_list_directory(mock_probe):
    # Mock the probe_file result with StreamInfo objects
    mock_probe.return_value = {
        "audio": [StreamInfo(id=0, language="eng", title="Stereo", codec_type="audio")],
        "subtitle": [StreamInfo(id=0, language="eng", title="English", codec_type="subtitle")]
    }

    # Test listing the 'Movies' directory
    response = client.get("/api/list?dir=Movies")
    assert response.status_code == 200
    data = response.json()
    
    assert data["dir"] == "Movies"
    assert len(data["files"]) == 1
    assert data["files"][0]["name"] == "test_movie.mkv"
    assert "eng" in data["languages"]
    
    # Verify probe_file was called
    mock_probe.assert_called_once()

@patch("src.app.api.routes_process.job_queue")
def test_start_process(mock_job_queue):
    # Mock the enqueue method
    mock_job_queue.enqueue = AsyncMock(return_value="test-job-id")
    
    payload = {
        "dir": "Movies",
        "files": ["Movies/test_movie.mkv"],
        "output_dir": "Output",
        "audio_languages": ["eng"],
        "subtitle_languages": ["eng"]
    }
    
    response = client.post("/api/process", json=payload)
    assert response.status_code == 200
    assert response.json() == {"jobId": "test-job-id"}
    
    mock_job_queue.enqueue.assert_called_once()

@patch("src.app.api.routes_jobs.job_store")
def test_get_job_status(mock_job_store):
    # Mock get_job to return a JobStatus instance
    mock_job = JobStatus(
        job_id="test-job-id",
        status="processing",
        overall_percent=50.0,
        current_file="test.mkv",
        logs=[]
    )
    
    mock_job_store.get_job.return_value = mock_job
    
    response = client.get("/api/jobs/test-job-id")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "test-job-id"
    assert data["status"] == "processing"

def test_list_directory_invalid_path():
    response = client.get("/api/list?dir=InvalidPath")
    # Depending on implementation, might return 400 or empty list if handled gracefully
    # Based on code: raise HTTPException(status_code=400, detail="Path is not a directory")
    # But wait, get_input_path might raise or return path. Then check .is_dir()
    # If path doesn't exist, is_dir() is False? 
    # Let's see route code:
    # dir_path = get_input_path(dir) -> if throws, 400.
    # if not dir_path.is_dir() -> 400.
    
    # We should expect 400
    assert response.status_code == 400
