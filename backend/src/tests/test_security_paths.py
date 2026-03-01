import pytest
from fastapi import HTTPException

from app.core.security_paths import validate_path


def test_validate_path_valid(tmp_path):
    result = validate_path("Movies/film.mkv", tmp_path)
    assert result == (tmp_path / "Movies" / "film.mkv").resolve()


def test_validate_path_traversal_raises_403(tmp_path):
    with pytest.raises(HTTPException) as exc_info:
        validate_path("../../etc/passwd", tmp_path)
    assert exc_info.value.status_code == 403


def test_validate_path_empty_returns_root(tmp_path):
    result = validate_path("", tmp_path)
    assert result == tmp_path


def test_validate_path_absolute_treated_as_relative(tmp_path):
    result = validate_path("/Movies/film.mkv", tmp_path)
    assert result == (tmp_path / "Movies" / "film.mkv").resolve()


def test_validate_path_nested(tmp_path):
    result = validate_path("Shows/S1/ep1.mkv", tmp_path)
    assert result == (tmp_path / "Shows" / "S1" / "ep1.mkv").resolve()
    assert str(result).startswith(str(tmp_path))
