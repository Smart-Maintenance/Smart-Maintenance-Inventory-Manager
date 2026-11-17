import pytest

from app.database import SessionLocal
from app.models import TicketPart


def test_create_ticket_sets_equipment_in_maintenance(client, ticket, equipment):
    assert ticket["status"] == "deschis"
    assert ticket["completed_at"] is None
    assert ticket["created_at"]
    assert client.get("/tickets/").json() == [ticket]
    assert client.get("/equipment/").json()[0]["status"] == "in_mentenanta"


def test_ticket_requires_existing_equipment(client, technician):
    response = client.post("/tickets/", json={
        "equipment_id": 999, "technician_id": technician, "description": "Service",
    })
    assert response.status_code == 404
    assert client.get("/tickets/").json() == []


def test_ticket_requires_equipment_field(client, technician):
    assert client.post("/tickets/", json={
        "technician_id": technician, "description": "Service",
    }).status_code == 422
    assert client.get("/tickets/").json() == []


@pytest.mark.parametrize("consumed,remaining,alert_count", [(3, 7, 0), (5, 5, 1), (10, 0, 1)])
def test_complete_ticket_updates_stock_equipment_and_alerts(
    client, ticket, part, consumed, remaining, alert_count,
):
    response = client.post(f"/tickets/{ticket['id']}/complete", json={
        "parts_used": [{"part_id": part["id"], "quantity_used": consumed}],
    })
    assert response.status_code == 200
    completed = response.json()
    assert completed["status"] == "finalizat"
    assert completed["completed_at"] is not None
    assert client.get("/tickets/").json() == [completed]
    assert client.get("/equipment/").json()[0]["status"] == "functional"
    assert client.get("/inventory/parts").json()[0]["quantity"] == remaining
    alerts = client.get("/inventory/notifications").json()
    assert len(alerts) == alert_count
    if alerts:
        assert alerts[0]["type"] == "stoc_minim"
        assert part["sku"] in alerts[0]["message"]
    with SessionLocal() as db:
        usage = db.query(TicketPart).one()
        assert (usage.ticket_id, usage.part_id, usage.quantity_used) == (
            ticket["id"], part["id"], consumed,
        )


def test_complete_without_parts(client, ticket):
    response = client.post(f"/tickets/{ticket['id']}/complete", json={})
    assert response.status_code == 200
    assert response.json()["status"] == "finalizat"
    assert client.get("/equipment/").json()[0]["status"] == "functional"
    with SessionLocal() as db:
        assert db.query(TicketPart).count() == 0


def test_complete_with_multiple_distinct_parts(client, ticket, part):
    response = client.post("/inventory/parts", json={
        "name": "Curea", "sku": "BELT-002", "quantity": 20, "min_stock": 2,
    })
    assert response.status_code == 200
    other_part = response.json()
    response = client.post(f"/tickets/{ticket['id']}/complete", json={
        "parts_used": [
            {"part_id": part["id"], "quantity_used": 3},
            {"part_id": other_part["id"], "quantity_used": 4},
        ],
    })
    assert response.status_code == 200
    quantities = {item["id"]: item["quantity"] for item in client.get("/inventory/parts").json()}
    assert quantities == {part["id"]: 7, other_part["id"]: 16}
    with SessionLocal() as db:
        usages = db.query(TicketPart).filter_by(ticket_id=ticket["id"]).all()
        assert {(usage.part_id, usage.quantity_used) for usage in usages} == {
            (part["id"], 3), (other_part["id"], 4),
        }


@pytest.mark.xfail(strict=True, reason="QA-001: consumul cumulat al aceleiași piese nu este validat")
def test_duplicate_part_cannot_exceed_available_stock(client, ticket, part):
    response = client.post(f"/tickets/{ticket['id']}/complete", json={
        "parts_used": [
            {"part_id": part["id"], "quantity_used": 6},
            {"part_id": part["id"], "quantity_used": 6},
        ],
    })
    assert response.status_code in (400, 422)
    assert client.get("/inventory/parts").json() == [part]
    assert client.get("/tickets/").json() == [ticket]
    assert client.get("/inventory/notifications").json() == []
    assert client.get("/equipment/").json()[0]["status"] == "in_mentenanta"
    with SessionLocal() as db:
        assert db.query(TicketPart).count() == 0


def test_completed_ticket_cannot_consume_stock_twice(client, ticket, part):
    payload = {"parts_used": [{"part_id": part["id"], "quantity_used": 3}]}
    first = client.post(f"/tickets/{ticket['id']}/complete", json=payload)
    assert first.status_code == 200
    second = client.post(f"/tickets/{ticket['id']}/complete", json=payload)
    assert second.status_code == 400
    assert client.get("/inventory/parts").json()[0]["quantity"] == 7
    assert client.get("/tickets/").json() == [first.json()]
    with SessionLocal() as db:
        assert db.query(TicketPart).count() == 1


def test_complete_missing_ticket(client):
    assert client.post("/tickets/999/complete", json={}).status_code == 404


@pytest.mark.parametrize("failure", ["insufficient_stock", "missing_part"])
def test_rejected_completion_changes_nothing(client, ticket, part, failure):
    # Prima piesă este validă; eroarea la a doua nu trebuie să consume prima piesă.
    invalid_item = {"part_id": part["id"], "quantity_used": 11} if failure == "insufficient_stock" else {
        "part_id": 999, "quantity_used": 1,
    }
    response = client.post(f"/tickets/{ticket['id']}/complete", json={
        "parts_used": [{"part_id": part["id"], "quantity_used": 2}, invalid_item],
    })
    assert response.status_code == (400 if failure == "insufficient_stock" else 404)
    assert client.get("/tickets/").json() == [ticket]
    assert client.get("/inventory/parts").json() == [part]
    assert client.get("/equipment/").json()[0]["status"] == "in_mentenanta"
    assert client.get("/inventory/notifications").json() == []
    with SessionLocal() as db:
        assert db.query(TicketPart).count() == 0


@pytest.mark.parametrize("quantity", [0, -1])
def test_nonpositive_consumption_is_rejected(client, ticket, part, quantity):
    response = client.post(f"/tickets/{ticket['id']}/complete", json={
        "parts_used": [{"part_id": part["id"], "quantity_used": quantity}],
    })
    assert response.status_code == 422
    assert client.get("/inventory/parts").json() == [part]
    assert client.get("/tickets/").json() == [ticket]
