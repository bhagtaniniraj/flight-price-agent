"""Tests for the price alert API endpoints."""
import pytest
from fastapi.testclient import TestClient


def test_create_alert(client: TestClient) -> None:
    """POST /api/v1/alerts/ creates a new alert."""
    payload = {
        "origin": "JFK",
        "destination": "LAX",
        "departure_date": "2025-08-15",
        "target_price": 250.0,
        "currency": "USD",
        "email": "test@example.com",
    }
    response = client.post("/api/v1/alerts/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["origin"] == "JFK"
    assert data["destination"] == "LAX"
    assert data["target_price"] == 250.0
    assert data["is_active"] is True
    assert "id" in data


def test_list_alerts(client: TestClient) -> None:
    """GET /api/v1/alerts/ returns list of alerts."""
    # Create one alert first
    client.post("/api/v1/alerts/", json={
        "origin": "BOS", "destination": "MIA", "departure_date": "2025-09-01",
        "target_price": 199.0, "currency": "USD",
    })
    response = client.get("/api/v1/alerts/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_alert_not_found(client: TestClient) -> None:
    """GET /api/v1/alerts/{id} returns 404 for unknown ID."""
    response = client.get("/api/v1/alerts/nonexistent-id")
    assert response.status_code == 404


def test_update_alert(client: TestClient) -> None:
    """PATCH /api/v1/alerts/{id} updates target price."""
    create_resp = client.post("/api/v1/alerts/", json={
        "origin": "ORD", "destination": "DFW", "departure_date": "2025-10-01",
        "target_price": 150.0, "currency": "USD",
    })
    alert_id = create_resp.json()["id"]

    update_resp = client.patch(f"/api/v1/alerts/{alert_id}", json={"target_price": 120.0})
    assert update_resp.status_code == 200
    assert update_resp.json()["target_price"] == 120.0


def test_delete_alert(client: TestClient) -> None:
    """DELETE /api/v1/alerts/{id} removes the alert."""
    create_resp = client.post("/api/v1/alerts/", json={
        "origin": "DEN", "destination": "SFO", "departure_date": "2025-11-01",
        "target_price": 200.0, "currency": "USD",
    })
    alert_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/alerts/{alert_id}")
    assert del_resp.status_code == 204

    get_resp = client.get(f"/api/v1/alerts/{alert_id}")
    assert get_resp.status_code == 404
