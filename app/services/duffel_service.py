"""Duffel flight search service."""
import logging
import httpx
from app.config import Settings
from app.schemas.flight import FlightOffer, FlightSearchRequest, FlightSegment

logger = logging.getLogger(__name__)


class DuffelService:
    """Service for searching flights via the Duffel API."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(timeout=60.0)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def search_flights(self, request: FlightSearchRequest) -> list[FlightOffer]:
        """Search for flight offers via Duffel."""
        if not self._settings.duffel_api_token:
            logger.warning("Duffel API token not configured, skipping.")
            return []

        url = f"{self._settings.duffel_base_url}/air/offer_requests"
        passengers = [{"type": "adult"} for _ in range(request.adults)]
        body = {
            "data": {
                "slices": [
                    {
                        "origin": request.origin.upper(),
                        "destination": request.destination.upper(),
                        "departure_date": request.departure_date,
                    }
                ],
                "passengers": passengers,
                "cabin_class": "economy",
            }
        }
        headers = {
            "Authorization": f"Bearer {self._settings.duffel_api_token}",
            "Duffel-Version": "v1",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        response = await self._client.post(url, json=body, headers=headers)
        response.raise_for_status()
        data = response.json()
        offers_raw = data.get("data", {}).get("offers", [])
        return self._parse_offers(offers_raw, request.currency)

    def _parse_offers(self, raw_offers: list[dict], currency: str) -> list[FlightOffer]:
        """Parse raw Duffel offers into FlightOffer objects."""
        offers: list[FlightOffer] = []
        for idx, item in enumerate(raw_offers):
            try:
                price = float(item.get("total_amount", 0))
                offer_currency = item.get("total_currency", currency)
                slices = item.get("slices", [])
                segments: list[FlightSegment] = []
                airline_codes: set[str] = set()
                first_slice = slices[0] if slices else {}
                for seg in first_slice.get("segments", []):
                    carrier = seg.get("marketing_carrier", {}).get("iata_code", "")
                    airline_codes.add(carrier)
                    segments.append(
                        FlightSegment(
                            departure_airport=seg.get("origin", {}).get("iata_code", ""),
                            arrival_airport=seg.get("destination", {}).get("iata_code", ""),
                            departure_time=seg.get("departing_at", ""),
                            arrival_time=seg.get("arriving_at", ""),
                            carrier_code=carrier,
                            flight_number=seg.get("marketing_carrier_flight_number", ""),
                            duration=seg.get("duration", ""),
                        )
                    )
                total_duration = first_slice.get("duration", "")
                offers.append(
                    FlightOffer(
                        id=f"duffel-{item.get('id', idx)}",
                        source="duffel",
                        price=price,
                        currency=offer_currency,
                        airline_codes=list(airline_codes),
                        segments=segments,
                        total_duration=total_duration,
                        deep_link=None,
                    )
                )
            except (KeyError, ValueError, IndexError) as exc:
                logger.warning("Failed to parse Duffel offer %d: %s", idx, exc)
        return offers
