import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _make_ffprobe_result(streams, returncode=0):
    result = MagicMock()
    result.returncode = returncode
    result.stdout = json.dumps({"streams": streams})
    result.stderr = "some error" if returncode != 0 else ""
    return result


async def test_probe_file_returns_audio_and_subtitle_streams(tmp_path):
    from app.core.ffprobe import probe_file

    streams = [
        {"codec_type": "video", "index": 0, "tags": {}},
        {"codec_type": "audio", "index": 1, "tags": {"language": "eng", "title": "Stereo"}},
        {"codec_type": "subtitle", "index": 2, "tags": {"language": "fra", "title": "French"}},
    ]

    with patch("app.core.ffprobe.subprocess.run", return_value=_make_ffprobe_result(streams)):
        result = await probe_file(tmp_path / "test.mkv")

    assert len(result["audio"]) == 1
    assert result["audio"][0].id == 1
    assert result["audio"][0].language == "eng"
    assert result["audio"][0].title == "Stereo"
    assert result["audio"][0].codec_type == "audio"

    assert len(result["subtitle"]) == 1
    assert result["subtitle"][0].id == 2
    assert result["subtitle"][0].language == "fra"
    assert result["subtitle"][0].codec_type == "subtitle"


async def test_probe_file_ignores_non_audio_subtitle_streams(tmp_path):
    from app.core.ffprobe import probe_file

    streams = [
        {"codec_type": "video", "index": 0, "tags": {}},
        {"codec_type": "data", "index": 3, "tags": {}},
    ]

    with patch("app.core.ffprobe.subprocess.run", return_value=_make_ffprobe_result(streams)):
        result = await probe_file(tmp_path / "test.mkv")

    assert result["audio"] == []
    assert result["subtitle"] == []


async def test_probe_file_nonzero_returncode_returns_empty(tmp_path):
    from app.core.ffprobe import probe_file

    with patch("app.core.ffprobe.subprocess.run", return_value=_make_ffprobe_result([], returncode=1)):
        result = await probe_file(tmp_path / "fail.mkv")

    assert result == {"audio": [], "subtitle": []}


async def test_probe_file_skips_stream_missing_index(tmp_path):
    from app.core.ffprobe import probe_file

    streams = [
        # no "index" key — should be skipped
        {"codec_type": "audio", "tags": {"language": "eng", "title": "English"}},
    ]

    with patch("app.core.ffprobe.subprocess.run", return_value=_make_ffprobe_result(streams)):
        result = await probe_file(tmp_path / "test.mkv")

    assert result["audio"] == []


async def test_probe_file_language_defaults_to_unknown(tmp_path):
    from app.core.ffprobe import probe_file

    streams = [
        {"codec_type": "audio", "index": 1, "tags": {}},  # no "language" tag
    ]

    with patch("app.core.ffprobe.subprocess.run", return_value=_make_ffprobe_result(streams)):
        result = await probe_file(tmp_path / "test.mkv")

    assert len(result["audio"]) == 1
    assert result["audio"][0].language == "unknown"
