from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from worker.ffmpeg_runner import FfmpegRunner


@pytest.fixture
def runner():
    return FfmpegRunner()


# ---------------------------------------------------------------------------
# _map_streams — explicit stream ID paths
# ---------------------------------------------------------------------------

def test_map_streams_audio_ids_adds_map_entries(runner):
    cmd = []
    runner._map_streams(
        input_path=Path("dummy.mkv"),
        cmd=cmd,
        audio_languages=["eng"],
        subtitle_languages=["eng"],
        audio_stream_ids=[1, 3],
        subtitle_stream_ids=None,
    )

    assert "-map" in cmd
    assert "0:1" in cmd
    assert "0:3" in cmd
    assert "-disposition:a:0" in cmd
    assert "default" in cmd


def test_map_streams_subtitle_ids_adds_correct_disposition(runner):
    cmd = []
    runner._map_streams(
        input_path=Path("dummy.mkv"),
        cmd=cmd,
        audio_languages=["eng"],
        subtitle_languages=["eng"],
        audio_stream_ids=[],
        subtitle_stream_ids=[2],
    )

    assert "0:2" in cmd
    assert "-disposition:s:0" in cmd
    assert "default" in cmd


def test_map_streams_both_audio_and_subtitle_ids(runner):
    cmd = []
    runner._map_streams(
        input_path=Path("dummy.mkv"),
        cmd=cmd,
        audio_languages=["eng"],
        subtitle_languages=["eng"],
        audio_stream_ids=[1],
        subtitle_stream_ids=[3],
    )

    assert "0:1" in cmd
    assert "0:3" in cmd
    assert "-disposition:a:0" in cmd
    assert "-disposition:s:0" in cmd


# ---------------------------------------------------------------------------
# _map_streams — language-based fallback (no explicit IDs)
# ---------------------------------------------------------------------------

def test_map_streams_language_based_includes_matching_languages(runner):
    cmd = []
    mock_streams = {
        "audio": [
            {"index": 1, "tags": {"language": "eng"}},
            {"index": 2, "tags": {"language": "fra"}},
        ],
        "subtitle": [
            {"index": 3, "tags": {"language": "eng"}},
        ],
        "video": {},
    }

    with patch.object(runner, "_probe_streams", return_value=mock_streams):
        runner._map_streams(
            input_path=Path("dummy.mkv"),
            cmd=cmd,
            audio_languages=["eng"],
            subtitle_languages=["eng"],
            audio_stream_ids=None,
            subtitle_stream_ids=None,
        )

    assert "0:1" in cmd   # eng audio — included
    assert "0:2" not in cmd  # fra audio — excluded
    assert "0:3" in cmd   # eng subtitle — included


def test_map_streams_language_based_excludes_all_when_no_match(runner):
    cmd = []
    mock_streams = {
        "audio": [{"index": 1, "tags": {"language": "fra"}}],
        "subtitle": [],
        "video": {},
    }

    with patch.object(runner, "_probe_streams", return_value=mock_streams):
        runner._map_streams(
            input_path=Path("dummy.mkv"),
            cmd=cmd,
            audio_languages=["eng"],
            subtitle_languages=["eng"],
            audio_stream_ids=None,
            subtitle_stream_ids=None,
        )

    assert "-map" not in cmd


# ---------------------------------------------------------------------------
# Progress parsing
# ---------------------------------------------------------------------------

def test_progress_callback_called_with_correct_percentages(runner, tmp_path):
    lines = [
        "  Duration: 00:01:00.00, start: 0.000000, bitrate: 5000 kb/s\n",
        "frame=  100 fps= 25 q=28.0 size=   1024kB time=00:00:30.00 bitrate= 279.6kbits/s\n",
        "frame=  200 fps= 25 q=28.0 size=   2048kB time=00:01:00.00 bitrate= 279.6kbits/s\n",
        "",
    ]

    mock_process = MagicMock()
    mock_process.stdout.readline.side_effect = lines
    mock_process.returncode = 0

    progress_values = []

    # Patch _probe_streams so it doesn't call ffprobe on a non-existent file
    mock_probe = {"audio": [], "subtitle": [], "video": {}}
    with patch("worker.ffmpeg_runner.subprocess.Popen", return_value=mock_process), \
         patch.object(runner, "_probe_streams", return_value=mock_probe):
        runner.run_ffmpeg(
            input_path=tmp_path / "input.mkv",
            output_path=tmp_path / "output.mkv",
            audio_languages=["eng"],
            subtitle_languages=["eng"],
            progress_callback=lambda p: progress_values.append(p),
            audio_stream_ids=[1],
            subtitle_stream_ids=None,
        )

    assert len(progress_values) == 2
    assert abs(progress_values[0]["percent"] - 50.0) < 0.1
    assert abs(progress_values[1]["percent"] - 100.0) < 0.1


def test_progress_not_called_before_duration_parsed(runner, tmp_path):
    """time= lines before Duration: should not trigger progress_callback."""
    lines = [
        "frame=  100 fps= 25 q=28.0 size=   1024kB time=00:00:30.00 bitrate= 279.6kbits/s\n",
        "  Duration: 00:01:00.00, start: 0.000000, bitrate: 5000 kb/s\n",
        "",
    ]

    mock_process = MagicMock()
    mock_process.stdout.readline.side_effect = lines
    mock_process.returncode = 0

    progress_values = []

    mock_probe = {"audio": [], "subtitle": [], "video": {}}
    with patch("worker.ffmpeg_runner.subprocess.Popen", return_value=mock_process), \
         patch.object(runner, "_probe_streams", return_value=mock_probe):
        runner.run_ffmpeg(
            input_path=tmp_path / "input.mkv",
            output_path=tmp_path / "output.mkv",
            audio_languages=["eng"],
            subtitle_languages=["eng"],
            progress_callback=lambda p: progress_values.append(p),
            audio_stream_ids=[1],
            subtitle_stream_ids=None,
        )

    assert progress_values == []


def test_progress_callback_receives_full_dict_when_all_fields_present(runner, tmp_path):
    """When line matches PROGRESS_RE, callback gets full dict with all metrics."""
    lines = [
        "  Duration: 00:01:00.00, start: 0.000000, bitrate: 5000 kb/s\n",
        "frame=  100 fps=25.0 q=-1.0 size=   1024KiB time=00:00:30.00 bitrate=4563.5kbits/s speed=6.2x\n",
        "",
    ]

    mock_process = MagicMock()
    mock_process.stdout.readline.side_effect = lines
    mock_process.returncode = 0

    progress_values = []

    mock_probe = {"audio": [], "subtitle": [], "video": {"total_frames": 1800, "total_duration": "00:01:00"}}
    with patch("worker.ffmpeg_runner.subprocess.Popen", return_value=mock_process), \
         patch.object(runner, "_probe_streams", return_value=mock_probe):
        runner.run_ffmpeg(
            input_path=tmp_path / "input.mkv",
            output_path=tmp_path / "output.mkv",
            audio_languages=["eng"],
            subtitle_languages=["eng"],
            progress_callback=lambda p: progress_values.append(p),
            audio_stream_ids=[1],
            subtitle_stream_ids=None,
        )

    assert len(progress_values) == 1
    p = progress_values[0]
    assert abs(p["percent"] - 50.0) < 0.1
    assert p["frame"] == 100
    assert p["fps"] == 25.0
    assert p["q"] == -1.0
    assert p["size_bytes"] == 1024 * 1024  # 1024 KiB
    assert p["time"] == "00:00:30"
    assert p["total_frames"] == 1800
    assert p["total_time"] == "00:01:00"
    assert p["bitrate"] == "4563.5kbits/s"
    assert p["speed"] == 6.2


# ---------------------------------------------------------------------------
# run_ffmpeg — cmd_callback
# ---------------------------------------------------------------------------

def test_run_ffmpeg_calls_cmd_callback_with_command_string(runner, tmp_path):
    mock_process = MagicMock()
    mock_process.stdout.readline.side_effect = [""]
    mock_process.returncode = 0

    cmd_values = []

    mock_probe = {"audio": [], "subtitle": [], "video": {}}
    with patch("worker.ffmpeg_runner.subprocess.Popen", return_value=mock_process), \
         patch.object(runner, "_probe_streams", return_value=mock_probe):
        runner.run_ffmpeg(
            input_path=tmp_path / "input.mkv",
            output_path=tmp_path / "output.mkv",
            audio_languages=["eng"],
            subtitle_languages=["eng"],
            progress_callback=lambda p: None,
            audio_stream_ids=[1],
            subtitle_stream_ids=None,
            cmd_callback=lambda c: cmd_values.append(c),
        )

    assert len(cmd_values) == 1
    assert "ffmpeg" in cmd_values[0]
    assert str(tmp_path / "input.mkv") in cmd_values[0]
    assert str(tmp_path / "output.mkv") in cmd_values[0]


def test_run_ffmpeg_cmd_callback_called_before_process_starts(runner, tmp_path):
    """cmd_callback must be invoked before Popen is called."""
    call_order = []

    mock_process = MagicMock()
    mock_process.stdout.readline.side_effect = [""]
    mock_process.returncode = 0

    def fake_popen(*args, **kwargs):
        call_order.append("popen")
        return mock_process

    mock_probe = {"audio": [], "subtitle": [], "video": {}}
    with patch("worker.ffmpeg_runner.subprocess.Popen", side_effect=fake_popen), \
         patch.object(runner, "_probe_streams", return_value=mock_probe):
        runner.run_ffmpeg(
            input_path=tmp_path / "input.mkv",
            output_path=tmp_path / "output.mkv",
            audio_languages=["eng"],
            subtitle_languages=["eng"],
            progress_callback=lambda p: None,
            audio_stream_ids=[1],
            subtitle_stream_ids=None,
            cmd_callback=lambda c: call_order.append("cmd"),
        )

    assert call_order == ["cmd", "popen"]


# ---------------------------------------------------------------------------
# run_ffmpeg — error handling
# ---------------------------------------------------------------------------

def test_run_ffmpeg_raises_on_nonzero_returncode(runner, tmp_path):
    mock_process = MagicMock()
    mock_process.stdout.readline.side_effect = [""]
    mock_process.returncode = 1

    mock_probe = {"audio": [], "subtitle": [], "video": {}}
    with patch("worker.ffmpeg_runner.subprocess.Popen", return_value=mock_process), \
         patch.object(runner, "_probe_streams", return_value=mock_probe):
        with pytest.raises(Exception, match="ffmpeg failed"):
            runner.run_ffmpeg(
                input_path=tmp_path / "input.mkv",
                output_path=tmp_path / "output.mkv",
                audio_languages=["eng"],
                subtitle_languages=["eng"],
                progress_callback=lambda p: None,
                audio_stream_ids=[1],
                subtitle_stream_ids=None,
            )
