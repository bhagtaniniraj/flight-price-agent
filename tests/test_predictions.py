"""Tests for the price prediction API endpoint."""
import pytest
from fastapi.testclient import TestClient


def test_predict_price(client: TestClient) -> None:
    """POST /api/v1/predict/ returns a prediction response."""
    payload = {
        "origin": "JFK",
        "destination": "LAX",
        "departure_date": "2025-08-15",
        "days_until_departure": 30,
        "current_price": 350.0,
        "adults": 1,
    }
    response = client.post("/api/v1/predict/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["origin"] == "JFK"
    assert data["destination"] == "LAX"
    assert data["current_price"] == 350.0
    assert "predicted_price" in data
    assert data["recommendation"] in ("buy_now", "wait", "good_deal")
    assert data["price_trend"] in ("rising", "falling", "stable")
    assert 0.0 <= data["confidence"] <= 1.0


def test_predict_price_missing_fields(client: TestClient) -> None:
    """POST /api/v1/predict/ with missing fields returns 422."""
    response = client.post("/api/v1/predict/", json={"origin": "JFK"})
    assert response.status_code == 422


def test_predict_imminent_departure(client: TestClient) -> None:
    """Prediction with 0 days until departure should still work."""
    payload = {
        "origin": "LAX",
        "destination": "JFK",
        "departure_date": "2025-08-01",
        "days_until_departure": 0,
        "current_price": 599.0,
        "adults": 2,
    }
    response = client.post("/api/v1/predict/", json=payload)
    assert response.status_code == 200
