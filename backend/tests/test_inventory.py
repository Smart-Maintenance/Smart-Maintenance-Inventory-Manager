import pytest


def test_create_and_list_parts_without_alert(client, part):
    assert client.get("/inventory/parts").json() == [part]
    assert client.get("/inventory/notifications").json() == []


def test_duplicate_sku_is_rejected(client, part):
    response = client.post("/inventory/parts", json={
        "name": "Alt filtru", "sku": part["sku"], "quantity": 0,
    })
    assert response.status_code == 400
    assert client.get("/inventory/parts").json() == [part]
    assert client.get("/inventory/notifications").json() == []


@pytest.mark.parametrize("quantity", [0, 4, 5, 6])
def test_initial_stock_alert_threshold(client, quantity):
    response = client.post("/inventory/parts", json={
        "name": "Curea", "sku": "BELT-001", "quantity": quantity, "min_stock": 5,
    })
    assert response.status_code == 200
    alerts = client.get("/inventory/notifications").json()
    assert len(alerts) == (1 if quantity <= 5 else 0)
    if alerts:
        assert alerts[0]["type"] == "stoc_minim"
        assert alerts[0]["is_read"] is False
        assert "BELT-001" in alerts[0]["message"]


def test_partial_update_preserves_fields_and_creates_alert(client, part):
    response = client.patch(f"/inventory/parts/{part['id']}", json={"quantity": 3})
    assert response.status_code == 200
    expected = {**part, "quantity": 3}
    assert response.json() == expected
    assert client.get("/inventory/parts").json() == [expected]
    alerts = client.get("/inventory/notifications").json()
    assert len(alerts) == 1
    assert "3 buc." in alerts[0]["message"]


def test_update_price_and_threshold(client, part):
    response = client.patch(f"/inventory/parts/{part['id']}", json={
        "unit_price": 20, "min_stock": 10,
    })
    assert response.status_code == 200
    assert response.json() == {**part, "unit_price": 20, "min_stock": 10}
    assert len(client.get("/inventory/notifications").json()) == 1


def test_notification_can_be_marked_read(client, part):
    client.patch(f"/inventory/parts/{part['id']}", json={"quantity": 5})
    alert = client.get("/inventory/notifications").json()[0]
    response = client.patch(f"/inventory/notifications/{alert['id']}/read")
    assert response.status_code == 200
    assert response.json() == {**alert, "is_read": True}
    assert client.get("/inventory/notifications").json()[0]["is_read"] is True


def test_missing_part_and_notification(client):
    assert client.patch("/inventory/parts/999", json={"quantity": 1}).status_code == 404
    assert client.patch("/inventory/notifications/999/read").status_code == 404


@pytest.mark.parametrize("field", ["quantity", "min_stock", "unit_price"])
def test_negative_values_are_rejected_on_create_and_update(client, part, field):
    response = client.post("/inventory/parts", json={
        "name": "Invalid", "sku": "INVALID", "quantity": 10, field: -1,
    })
    assert response.status_code == 422
    assert client.patch(f"/inventory/parts/{part['id']}", json={field: -1}).status_code == 422
    assert client.get("/inventory/parts").json() == [part]
