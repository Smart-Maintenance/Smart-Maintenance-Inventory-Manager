import pytest


def test_equipment_create_and_list(client, equipment):
    assert equipment["status"] == "functional"
    assert equipment["next_maintenance"] is None
    assert client.get("/equipment/").json() == [equipment]


def test_equipment_duplicate_serial_is_rejected(client, equipment):
    response = client.post("/equipment/", json={
        "name": "Alt compresor", "serial_number": equipment["serial_number"],
        "location": "Depozit",
    })
    assert response.status_code == 400
    assert client.get("/equipment/").json() == [equipment]


@pytest.mark.parametrize("status", ["defect", "in_mentenanta", "functional"])
def test_equipment_status_is_persisted(client, equipment, status):
    response = client.patch(f"/equipment/{equipment['id']}/status", params={"status": status})
    assert response.status_code == 200
    assert response.json()["status"] == status
    assert client.get("/equipment/").json()[0]["status"] == status


def test_equipment_unknown_id(client):
    assert client.patch("/equipment/999/status", params={"status": "defect"}).status_code == 404


def test_equipment_invalid_status(client, equipment):
    response = client.patch(f"/equipment/{equipment['id']}/status", params={"status": "unknown"})
    assert response.status_code == 422
    assert client.get("/equipment/").json() == [equipment]


def test_equipment_missing_required_field(client):
    assert client.post("/equipment/", json={"name": "Compresor"}).status_code == 422
    assert client.get("/equipment/").json() == []
