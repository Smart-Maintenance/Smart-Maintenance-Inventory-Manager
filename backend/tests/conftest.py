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
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import User, UserRole  # noqa: E402


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def equipment(client):
    response = client.post("/equipment/", json={
        "name": "Compresor", "serial_number": "EQ-001", "location": "Atelier",
    })
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def part(client):
    response = client.post("/inventory/parts", json={
        "name": "Filtru", "sku": "FILTER-001", "quantity": 10,
        "min_stock": 5, "unit_price": 12.5,
    })
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def technician(client):
    with SessionLocal() as db:
        user = User(username="tech", email="tech@example.test",
                    hashed_password="test-fixture-only", role=UserRole.TEHNICIAN)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id


@pytest.fixture
def ticket(client, equipment, technician):
    response = client.post("/tickets/", json={
        "equipment_id": equipment["id"], "technician_id": technician,
        "description": "Schimbare filtru",
    })
    assert response.status_code == 200
    return response.json()


def pytest_sessionfinish(session, exitstatus):
    engine.dispose()
    database_directory.cleanup()
