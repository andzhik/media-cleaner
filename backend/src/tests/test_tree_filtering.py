import pytest
from pathlib import Path
import tempfile
import shutil
import os
from fastapi.testclient import TestClient

# Create a temporary directory for tests
temp_test_dir = tempfile.mkdtemp()
input_root = Path(temp_test_dir) / "input"
input_root.mkdir()

os.environ["INPUT_ROOT"] = str(input_root)
os.environ["OUTPUT_ROOT"] = str(temp_test_dir) # Not really used for tree test

# Import app AFTER setting env vars
from ..app.main import app
from ..app.core.config import settings

# Force override settings
settings.INPUT_ROOT = input_root
settings.VIDEO_EXTENSIONS = {".mkv", ".mp4"}

client = TestClient(app)

@pytest.fixture
def setup_tree():
    # Structure:
    # /input
    #   /Movies (has video)
    #     movie1.mkv
    #   /Shows (has subdir with video)
    #     /S1
    #       ep1.mp4
    #   /Empty (truly empty)
    #   /NoVideos (has subdirs, but no videos anywhere)
    #     /SubEmpty
    #   /OnlyDocs (has files, but no videos)
    #     readme.txt
    
    (input_root / "Movies").mkdir()
    (input_root / "Movies" / "movie1.mkv").touch()
    
    (input_root / "Shows").mkdir()
    (input_root / "Shows" / "S1").mkdir()
    (input_root / "Shows" / "S1" / "ep1.mp4").touch()
    
    (input_root / "Empty").mkdir()
    
    (input_root / "NoVideos").mkdir()
    (input_root / "NoVideos" / "SubEmpty").mkdir()
    
    (input_root / "OnlyDocs").mkdir()
    (input_root / "OnlyDocs" / "readme.txt").touch()
    
    yield
    
    # Cleanup
    for item in input_root.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

def test_tree_filtering(setup_tree):
    response = client.get("/api/tree")
    assert response.status_code == 200
    data = response.json()
    
    # Root should be there
    assert data["name"] == "/"
    
    # Check children
    child_names = [child["name"] for child in data["children"]]
    
    # Movies should be there (contains video)
    assert "Movies" in child_names
    
    # Shows should be there (contains subdir with video)
    assert "Shows" in child_names
    
    # Empty should NOT be there
    assert "Empty" not in child_names
    
    # NoVideos should NOT be there
    assert "NoVideos" not in child_names
    
    # OnlyDocs should NOT be there
    assert "OnlyDocs" not in child_names
    
    # Check nested
    shows_node = next(child for child in data["children"] if child["name"] == "Shows")
    assert any(c["name"] == "S1" for c in shows_node["children"])

def teardown_module(module):
    shutil.rmtree(temp_test_dir)
