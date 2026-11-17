import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Bază izolată: testele nu deschid niciodată baza din proiect.
database_directory = tempfile.TemporaryDirectory(prefix="smartmim-tests-")
os.environ["DATABASE_URL"] = "sqlite:///" + (
    Path(database_directory.name) / "test.db"
).as_posix()
os.environ["CORS_ORIGINS"] = "http://localhost:5173"

from app.main import app  # noqa: E402
from app.database import engine  # noqa: E402


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def pytest_sessionfinish(session, exitstatus):
    engine.dispose()
    database_directory.cleanup()
