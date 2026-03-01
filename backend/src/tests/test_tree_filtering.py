import shutil

import pytest


@pytest.fixture
def setup_tree(tmp_media):
    input_root = tmp_media / "input"

    (input_root / "Movies").mkdir(exist_ok=True)
    (input_root / "Movies" / "movie1.mkv").touch()

    (input_root / "Shows").mkdir(exist_ok=True)
    (input_root / "Shows" / "S1").mkdir(parents=True, exist_ok=True)
    (input_root / "Shows" / "S1" / "ep1.mp4").touch()

    (input_root / "Empty").mkdir(exist_ok=True)

    (input_root / "NoVideos").mkdir(exist_ok=True)
    (input_root / "NoVideos" / "SubEmpty").mkdir(parents=True, exist_ok=True)

    (input_root / "OnlyDocs").mkdir(exist_ok=True)
    (input_root / "OnlyDocs" / "readme.txt").touch()

    yield

    # Only remove what this fixture created; preserve pre-existing dirs (e.g. Movies
    # may have been seeded by test_api.py's session-scoped setup_movies_dir).
    (input_root / "Movies" / "movie1.mkv").unlink(missing_ok=True)
    for d in ["Shows", "Empty", "NoVideos", "OnlyDocs"]:
        shutil.rmtree(input_root / d, ignore_errors=True)


def test_tree_filtering(setup_tree, app_client):
    response = app_client.get("/api/tree")
    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "/"

    child_names = [child["name"] for child in data["children"]]

    assert "Movies" in child_names
    assert "Shows" in child_names
    assert "Empty" not in child_names
    assert "NoVideos" not in child_names
    assert "OnlyDocs" not in child_names

    shows_node = next(child for child in data["children"] if child["name"] == "Shows")
    assert any(c["name"] == "S1" for c in shows_node["children"])
