import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from worker.processor import JobProcessor


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def job_dirs(tmp_path):
    """Return (job_data_root, input_root, output_root) backed by tmp dirs."""
    job_data = tmp_path / "job-data"
    input_root = tmp_path / "input"
    output_root = tmp_path / "output"
    input_root.mkdir()
    output_root.mkdir()
    return job_data, input_root, output_root


@pytest.fixture
def processor(job_dirs, monkeypatch):
    job_data, input_root, output_root = job_dirs
    monkeypatch.setattr("worker.processor.JOB_DATA_ROOT", job_data)
    monkeypatch.setattr("worker.processor.INPUT_ROOT", input_root)
    monkeypatch.setattr("worker.processor.OUTPUT_ROOT", output_root)
    return JobProcessor()


def _write_job(pending_dir: Path, job_id: str, extra: dict = None) -> Path:
    """Write a minimal job JSON to pending_dir and return its path."""
    data = {
        "job_id": job_id,
        "files": [],
        "audio_languages": ["eng"],
        "subtitle_languages": ["eng"],
        "output_dir": "",
        **(extra or {}),
    }
    p = pending_dir / f"{job_id}.json"
    p.write_text(json.dumps(data))
    return p


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


def test_init_creates_all_directories(processor):
    assert processor.pending_dir.is_dir()
    assert processor.processing_dir.is_dir()
    assert processor.completed_dir.is_dir()
    assert processor.failed_dir.is_dir()


# ---------------------------------------------------------------------------
# process_jobs
# ---------------------------------------------------------------------------


def test_process_jobs_sleeps_when_no_pending(processor):
    with patch("worker.processor.time.sleep", side_effect=StopIteration):
        with pytest.raises(StopIteration):
            processor.process_jobs()


def test_process_jobs_calls_process_job_for_first_pending_file(processor):
    job_file = _write_job(processor.pending_dir, "abc")

    with patch.object(processor, "process_job", side_effect=StopIteration) as mock_pj:
        with pytest.raises(StopIteration):
            processor.process_jobs()

    mock_pj.assert_called_once_with(job_file)


# ---------------------------------------------------------------------------
# process_job — happy paths
# ---------------------------------------------------------------------------


def test_process_job_completes_with_empty_files(processor):
    job_file = _write_job(processor.pending_dir, "job1")

    with patch("worker.processor.FfmpegRunner"):
        processor.process_job(job_file)

    assert (processor.completed_dir / "job1.json").exists()
    assert not (processor.processing_dir / "job1.json").exists()


def test_process_job_processes_files_list(processor, job_dirs):
    _, input_root, _ = job_dirs
    (input_root / "video.mkv").touch()

    job_file = _write_job(processor.pending_dir, "job2", {"files": ["/video.mkv"]})

    with patch("worker.processor.FfmpegRunner") as MockRunner:
        processor.process_job(job_file)

    MockRunner.return_value.run_ffmpeg.assert_called_once()
    assert (processor.completed_dir / "job2.json").exists()


def test_process_job_processes_selections_with_stream_ids(processor, job_dirs):
    _, input_root, _ = job_dirs
    (input_root / "movie.mkv").touch()

    selections = [
        {"rel_path": "/movie.mkv", "audio_stream_ids": [1, 2], "subtitle_stream_ids": [3]},
    ]
    job_file = _write_job(processor.pending_dir, "job3", {"selections": selections})

    with patch("worker.processor.FfmpegRunner") as MockRunner:
        processor.process_job(job_file)

    mock_run = MockRunner.return_value.run_ffmpeg
    mock_run.assert_called_once()
    kwargs = mock_run.call_args.kwargs
    assert kwargs["audio_stream_ids"] == [1, 2]
    assert kwargs["subtitle_stream_ids"] == [3]
    assert (processor.completed_dir / "job3.json").exists()


def test_process_job_scans_dir_when_files_empty(processor, job_dirs):
    _, input_root, _ = job_dirs
    sub = input_root / "movies"
    sub.mkdir()
    (sub / "a.mkv").touch()
    (sub / "b.mp4").touch()
    (sub / "ignore.txt").touch()

    job_file = _write_job(processor.pending_dir, "job4", {"dir": "/movies", "files": []})

    ffmpeg_calls = []
    with patch("worker.processor.FfmpegRunner") as MockRunner:
        MockRunner.return_value.run_ffmpeg.side_effect = lambda *a, **kw: ffmpeg_calls.append(a)
        processor.process_job(job_file)

    assert len(ffmpeg_calls) == 2  # .mkv and .mp4 only; .txt excluded
    assert (processor.completed_dir / "job4.json").exists()


def test_process_job_skips_missing_input_file(processor):
    job_file = _write_job(processor.pending_dir, "job5", {"files": ["/missing.mkv"]})

    with patch("worker.processor.FfmpegRunner") as MockRunner:
        processor.process_job(job_file)

    MockRunner.return_value.run_ffmpeg.assert_not_called()
    assert (processor.completed_dir / "job5.json").exists()


# ---------------------------------------------------------------------------
# process_job — error path
# ---------------------------------------------------------------------------


def test_process_job_moves_to_failed_on_exception(processor, job_dirs):
    _, input_root, _ = job_dirs
    (input_root / "vid.mkv").touch()

    job_file = _write_job(processor.pending_dir, "job6", {"files": ["/vid.mkv"]})

    with patch("worker.processor.FfmpegRunner") as MockRunner:
        MockRunner.return_value.run_ffmpeg.side_effect = RuntimeError("ffmpeg failed")
        processor.process_job(job_file)

    assert (processor.failed_dir / "job6.json").exists()
    assert not (processor.completed_dir / "job6.json").exists()


def test_process_job_writes_failed_status_on_exception(processor, job_dirs):
    job_data_root, input_root, _ = job_dirs
    (input_root / "vid.mkv").touch()

    job_file = _write_job(processor.pending_dir, "job7", {"files": ["/vid.mkv"]})

    with patch("worker.processor.FfmpegRunner") as MockRunner:
        MockRunner.return_value.run_ffmpeg.side_effect = RuntimeError("boom")
        processor.process_job(job_file)

    status_file = job_data_root / "status" / "job7.json"
    data = json.loads(status_file.read_text())
    assert data["status"] == "failed"
    assert "boom" in data["logs"][0]


# ---------------------------------------------------------------------------
# update_status
# ---------------------------------------------------------------------------


def test_update_status_writes_correct_json(processor, job_dirs):
    job_data_root, *_ = job_dirs
    processor.update_status("j1", "processing", 42.5, current_file="/foo.mkv", logs=["line1"])

    status_file = job_data_root / "status" / "j1.json"
    assert status_file.exists()
    data = json.loads(status_file.read_text())
    assert data == {
        "job_id": "j1",
        "status": "processing",
        "overall_percent": 42.5,
        "current_file": "/foo.mkv",
        "logs": ["line1"],
    }


def test_update_status_defaults_logs_and_current_file(processor, job_dirs):
    job_data_root, *_ = job_dirs
    processor.update_status("j2", "completed", 100.0)

    data = json.loads((job_data_root / "status" / "j2.json").read_text())
    assert data["logs"] == []
    assert data["current_file"] is None


def test_update_status_retries_os_replace_on_error(processor):
    call_count = {"n": 0}
    real_replace = os.replace

    def flaky_replace(src, dst):
        call_count["n"] += 1
        if call_count["n"] < 3:
            raise OSError("locked")
        real_replace(src, dst)

    with patch("os.replace", side_effect=flaky_replace), patch("time.sleep"):
        processor.update_status("j3", "completed", 100.0)

    assert call_count["n"] == 3
