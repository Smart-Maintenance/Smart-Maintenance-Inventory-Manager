from unittest.mock import patch

from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError

from app.database import engine, get_db


def test_root_and_liveness(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "online", "project": "SmartMIM Backend"}
    assert client.get("/health/live").json() == {"status": "alive"}


def test_readiness_and_schema(client):
    assert client.get("/health/ready").status_code == 200
    assert set(inspect(engine).get_table_names()) == {
        "users", "equipment", "spare_parts", "maintenance_tickets",
        "ticket_parts", "notifications",
    }


def test_readiness_failure_keeps_liveness(client):
    with patch("app.main.engine.connect", side_effect=OperationalError(
        "SELECT 1", {}, Exception("private connection details")
    )):
        response = client.get("/health/ready")
        assert response.status_code == 503
        assert response.json() == {"detail": "Database unavailable"}
        assert client.get("/health/live").status_code == 200


def test_cors_allows_frontend_only(client):
    for origin, allowed in [("http://localhost:5173", True), ("https://unknown.example", False)]:
        response = client.options("/", headers={
            "Origin": origin, "Access-Control-Request-Method": "GET"
        })
        assert response.status_code == (200 if allowed else 400)
        assert response.headers.get("access-control-allow-origin") == (origin if allowed else None)


def test_openapi(client):
    schema = client.get("/openapi.json").json()
    assert schema["info"]["title"] == "SmartMIM API"
    assert "/health/ready" in schema["paths"]


def test_database_session_closes():
    with patch("app.database.SessionLocal") as factory:
        dependency = get_db()
        assert next(dependency) is factory.return_value
        dependency.close()
        factory.return_value.close.assert_called_once()
