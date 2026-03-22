"""Pytest fixtures for the flight price agent test suite."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.api.dependencies import get_aggregator, get_alert_service
from app.schemas.flight import FlightOffer, FlightSearchResponse, FlightSegment
from app.services.aggregator import FlightAggregator
from app.services.alert_service import AlertService
from datetime import datetime


def _make_mock_offer(source: str = "amadeus", price: float = 299.99) -> FlightOffer:
    return FlightOffer(
        id=f"{source}-test-1",
        source=source,
        price=price,
        currency="USD",
        airline_codes=["AA"],
        segments=[
            FlightSegment(
                departure_airport="JFK",
                arrival_airport="LAX",
                departure_time="2025-08-15T08:00:00",
                arrival_time="2025-08-15T11:30:00",
                carrier_code="AA",
                flight_number="100",
                duration="PT5H30M",
            )
        ],
        total_duration="PT5H30M",
        deep_link=None,
        is_deal=False,
    )


@pytest.fixture()
def mock_search_response() -> FlightSearchResponse:
    """A pre-built mock FlightSearchResponse."""
    return FlightSearchResponse(
        search_id="test-search-id",
        origin="JFK",
        destination="LAX",
        departure_date="2025-08-15",
        offers=[_make_mock_offer("amadeus", 299.99), _make_mock_offer("kiwi", 289.99)],
        cheapest_price=289.99,
        total_results=2,
        providers_queried=["amadeus", "kiwi"],
        search_timestamp=datetime(2025, 1, 1, 0, 0, 0),
    )


@pytest.fixture()
def mock_aggregator(mock_search_response: FlightSearchResponse) -> FlightAggregator:
    """Mock FlightAggregator that returns a fixed response."""
    aggregator = MagicMock(spec=FlightAggregator)
    aggregator.search = AsyncMock(return_value=mock_search_response)
    return aggregator


@pytest.fixture()
def alert_service() -> AlertService:
    """Fresh AlertService instance for each test."""
    return AlertService()


@pytest.fixture()
def client(mock_aggregator: FlightAggregator, alert_service: AlertService) -> TestClient:
    """FastAPI test client with mocked dependencies."""
    app.dependency_overrides[get_aggregator] = lambda: mock_aggregator
    app.dependency_overrides[get_alert_service] = lambda: alert_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
