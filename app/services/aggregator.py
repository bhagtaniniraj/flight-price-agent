"""Flight offer aggregator that queries multiple providers in parallel."""
import asyncio
import logging
from datetime import datetime, timezone
from uuid import uuid4
import statistics

from app.config import Settings
from app.schemas.flight import FlightOffer, FlightSearchRequest, FlightSearchResponse
from app.services.amadeus_service import AmadeusService
from app.services.duffel_service import DuffelService
from app.services.kiwi_service import KiwiService

logger = logging.getLogger(__name__)


class FlightAggregator:
    """Aggregates flight search results from multiple providers."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.amadeus = AmadeusService(settings)
        self.kiwi = KiwiService(settings)
        self.duffel = DuffelService(settings)

    async def close(self) -> None:
        """Close all underlying HTTP clients."""
        await asyncio.gather(
            self.amadeus.close(),
            self.kiwi.close(),
            self.duffel.close(),
            return_exceptions=True,
        )

    async def search(self, request: FlightSearchRequest) -> FlightSearchResponse:
        """Search all providers in parallel, deduplicate, and return results."""
        providers = [
            ("amadeus", self.amadeus.search_flights(request)),
            ("kiwi", self.kiwi.search_flights(request)),
            ("duffel", self.duffel.search_flights(request)),
        ]
        tasks = [task for _, task in providers]
        provider_names = [name for name, _ in providers]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_offers: list[FlightOffer] = []
        queried: list[str] = []
        for name, result in zip(provider_names, results):
            if isinstance(result, Exception):
                logger.warning("Provider %s failed: %s", name, result)
            else:
                queried.append(name)
                all_offers.extend(result)

        deduped = self._deduplicate(all_offers)
        deduped.sort(key=lambda o: o.price)
        marked = self._mark_deals(deduped)

        cheapest = marked[0].price if marked else None

        return FlightSearchResponse(
            search_id=str(uuid4()),
            origin=request.origin.upper(),
            destination=request.destination.upper(),
            departure_date=request.departure_date,
            offers=marked,
            cheapest_price=cheapest,
            total_results=len(marked),
            providers_queried=queried,
            search_timestamp=datetime.now(timezone.utc),
        )

    def _deduplicate(self, offers: list[FlightOffer]) -> list[FlightOffer]:
        """Remove duplicate offers based on airlines, first departure time, and price."""
        seen: set[tuple] = set()
        unique: list[FlightOffer] = []
        for offer in offers:
            dep_time = offer.segments[0].departure_time if offer.segments else ""
            key = (frozenset(offer.airline_codes), dep_time, round(offer.price, 2))
            if key not in seen:
                seen.add(key)
                unique.append(offer)
        return unique

    def _mark_deals(self, offers: list[FlightOffer]) -> list[FlightOffer]:
        """Mark offers as deals if price is below 80% of the median price."""
        if len(offers) < 2:
            return offers
        prices = [o.price for o in offers]
        med = statistics.median(prices)
        threshold = med * 0.8
        for offer in offers:
            offer.is_deal = offer.price < threshold
        return offers
