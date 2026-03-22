"""Flight search API routes."""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_aggregator
from app.schemas.flight import FlightSearchRequest, FlightSearchResponse
from app.services.aggregator import FlightAggregator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=FlightSearchResponse, summary="Search flights across all providers")
async def search_flights(
    request: FlightSearchRequest,
    aggregator: Annotated[FlightAggregator, Depends(get_aggregator)],
) -> FlightSearchResponse:
    """Search for flights across Amadeus, Kiwi, and Duffel simultaneously."""
    try:
        return await aggregator.search(request)
    except Exception as exc:
        logger.exception("Search failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Flight search failed: {exc}") from exc


@router.get("/compare", response_model=FlightSearchResponse, summary="Compare prices for a route")
async def compare_prices(
    origin: Annotated[str, Query(min_length=3, max_length=3, description="IATA origin code")],
    destination: Annotated[str, Query(min_length=3, max_length=3, description="IATA destination code")],
    departure_date: Annotated[str, Query(description="Date in YYYY-MM-DD format")],
    adults: Annotated[int, Query(ge=1, le=9)] = 1,
    currency: Annotated[str, Query(min_length=3, max_length=3)] = "USD",
    aggregator: FlightAggregator = Depends(get_aggregator),
) -> FlightSearchResponse:
    """Compare prices across all providers for a given route via query params."""
    request = FlightSearchRequest(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        adults=adults,
        currency=currency,
    )
    try:
        return await aggregator.search(request)
    except Exception as exc:
        logger.exception("Compare failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Price comparison failed: {exc}") from exc
