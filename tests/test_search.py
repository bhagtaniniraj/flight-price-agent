"""Tests for the flight search API endpoints."""
import pytest
from fastapi.testclient import TestClient


def test_search_flights_success(client: TestClient) -> None:
    """POST /api/v1/search returns 200 with offer list."""
    payload = {
        "origin": "JFK",
        "destination": "LAX",
        "departure_date": "2025-08-15",
        "adults": 1,
        "currency": "USD",
    }
    response = client.post("/api/v1/search/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["origin"] == "JFK"
    assert data["destination"] == "LAX"
    assert isinstance(data["offers"], list)
    assert data["total_results"] == 2
    assert data["cheapest_price"] == 289.99


def test_search_flights_missing_fields(client: TestClient) -> None:
    """POST /api/v1/search with missing required fields returns 422."""
    response = client.post("/api/v1/search/", json={"origin": "JFK"})
    assert response.status_code == 422


def test_compare_prices(client: TestClient) -> None:
    """GET /api/v1/search/compare returns 200 with query params."""
    response = client.get(
        "/api/v1/search/compare",
        params={
            "origin": "JFK",
            "destination": "LAX",
            "departure_date": "2025-08-15",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["origin"] == "JFK"
    assert data["total_results"] == 2


def test_health_endpoint(client: TestClient) -> None:
    """GET /health returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_root_endpoint(client: TestClient) -> None:
    """GET / serves the frontend HTML page."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
