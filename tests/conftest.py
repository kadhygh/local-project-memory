import shutil
import sys
from pathlib import Path
from uuid import uuid4

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
WORKSPACE_TMP_ROOT = ROOT / "tests_workspace_tmp"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from local_project_memory.services.store import REPOSITORY


@pytest.fixture(autouse=True)
def clear_repository() -> None:
    REPOSITORY.clear()


@pytest.fixture()
def workspace_tmp_path() -> Path:
    WORKSPACE_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    case_dir = WORKSPACE_TMP_ROOT / f"case_{uuid4().hex}"
    case_dir.mkdir(parents=True, exist_ok=False)
    try:
        yield case_dir
    finally:
        shutil.rmtree(case_dir, ignore_errors=True)


def pytest_sessionfinish() -> None:
    shutil.rmtree(WORKSPACE_TMP_ROOT, ignore_errors=True)

