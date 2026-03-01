import os
import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def tmp_media(tmp_path_factory):
    base = tmp_path_factory.mktemp("media")
    (base / "input").mkdir()
    (base / "output").mkdir()
    (base / "job-data" / "status").mkdir(parents=True)
    (base / "job-data" / "pending").mkdir()
    return base


@pytest.fixture(autouse=True, scope="session")
def patch_env(tmp_media):
    os.environ["INPUT_ROOT"] = str(tmp_media / "input")
    os.environ["OUTPUT_ROOT"] = str(tmp_media / "output")
    os.environ["JOB_DATA_ROOT"] = str(tmp_media / "job-data")


@pytest.fixture(scope="session")
def app_client(patch_env):
    from app.main import app
    from app.core import config

    config.settings.INPUT_ROOT = Path(os.environ["INPUT_ROOT"])
    config.settings.OUTPUT_ROOT = Path(os.environ["OUTPUT_ROOT"])

    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        yield client
