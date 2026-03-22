"""Tests for the FlightAggregator service."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import pytest

from app.config import Settings
from app.schemas.flight import FlightOffer, FlightSearchRequest, FlightSegment
from app.services.aggregator import FlightAggregator


def _make_offer(source: str, price: float, dep_time: str = "2025-08-15T08:00:00") -> FlightOffer:
    return FlightOffer(
        id=f"{source}-{price}",
        source=source,
        price=price,
        currency="USD",
        airline_codes=["AA"],
        segments=[
            FlightSegment(
                departure_airport="JFK",
                arrival_airport="LAX",
                departure_time=dep_time,
                arrival_time="2025-08-15T11:30:00",
                carrier_code="AA",
                flight_number="100",
                duration="PT5H30M",
            )
        ],
        total_duration="PT5H30M",
    )


@pytest.fixture()
def settings() -> Settings:
    return Settings(amadeus_api_key="x", kiwi_api_key="y", duffel_api_token="z")


@pytest.mark.asyncio
async def test_parallel_search(settings: Settings) -> None:
    """Aggregator queries all providers and merges results."""
    amadeus_offers = [_make_offer("amadeus", 300.0)]
    kiwi_offers = [_make_offer("kiwi", 280.0)]
    duffel_offers = [_make_offer("duffel", 320.0)]

    aggregator = FlightAggregator(settings)
    aggregator.amadeus.search_flights = AsyncMock(return_value=amadeus_offers)
    aggregator.kiwi.search_flights = AsyncMock(return_value=kiwi_offers)
    aggregator.duffel.search_flights = AsyncMock(return_value=duffel_offers)

    request = FlightSearchRequest(origin="JFK", destination="LAX", departure_date="2025-08-15")
    response = await aggregator.search(request)

    assert response.total_results == 3
    assert response.cheapest_price == 280.0
    assert set(response.providers_queried) == {"amadeus", "kiwi", "duffel"}
    await aggregator.close()


@pytest.mark.asyncio
async def test_provider_failure_skipped(settings: Settings) -> None:
    """Failed provider is skipped, others still return results."""
    aggregator = FlightAggregator(settings)
    aggregator.amadeus.search_flights = AsyncMock(side_effect=Exception("API error"))
    aggregator.kiwi.search_flights = AsyncMock(return_value=[_make_offer("kiwi", 270.0)])
    aggregator.duffel.search_flights = AsyncMock(return_value=[])

    request = FlightSearchRequest(origin="JFK", destination="LAX", departure_date="2025-08-15")
    response = await aggregator.search(request)

    assert response.total_results == 1
    assert "amadeus" not in response.providers_queried
    assert "kiwi" in response.providers_queried
    await aggregator.close()


@pytest.mark.asyncio
async def test_deduplication(settings: Settings) -> None:
    """Duplicate offers (same airline, time, price) are removed."""
    offer_a = _make_offer("amadeus", 300.0)
    offer_b = _make_offer("kiwi", 300.0)  # same airline AA, same dep_time, same price → duplicate

    aggregator = FlightAggregator(settings)
    aggregator.amadeus.search_flights = AsyncMock(return_value=[offer_a])
    aggregator.kiwi.search_flights = AsyncMock(return_value=[offer_b])
    aggregator.duffel.search_flights = AsyncMock(return_value=[])

    request = FlightSearchRequest(origin="JFK", destination="LAX", departure_date="2025-08-15")
    response = await aggregator.search(request)

    assert response.total_results == 1
    await aggregator.close()


@pytest.mark.asyncio
async def test_deal_marking(settings: Settings) -> None:
    """Offers below 80% of median price are marked as deals."""
    offers = [
        _make_offer("amadeus", 100.0, "2025-08-15T06:00:00"),
        _make_offer("kiwi", 300.0, "2025-08-15T09:00:00"),
        _make_offer("duffel", 320.0, "2025-08-15T12:00:00"),
    ]
    aggregator = FlightAggregator(settings)
    aggregator.amadeus.search_flights = AsyncMock(return_value=[offers[0]])
    aggregator.kiwi.search_flights = AsyncMock(return_value=[offers[1]])
    aggregator.duffel.search_flights = AsyncMock(return_value=[offers[2]])

    request = FlightSearchRequest(origin="JFK", destination="LAX", departure_date="2025-08-15")
    response = await aggregator.search(request)

    # 100 < 300 * 0.8 = 240, so the 100 offer should be a deal
    deal_offers = [o for o in response.offers if o.is_deal]
    assert len(deal_offers) >= 1
    assert deal_offers[0].price == 100.0
    await aggregator.close()
