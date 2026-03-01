import pytest


@pytest.fixture
def tmp_job_dir(tmp_path):
    (tmp_path / "status").mkdir()
    (tmp_path / "pending").mkdir()
    return tmp_path
