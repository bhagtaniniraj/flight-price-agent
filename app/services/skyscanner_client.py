import httpx
import logging
import os
from datetime import date

logger = logging.getLogger(__name__)


class SkyscannerClient:
    """Client for Skyscanner Partners/Flights API."""

    BASE_URL = "https://partners.api.skyscanner.net/apiservices"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=15.0)

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        currency: str = "USD",
        locale: str = "en-US",
        market: str = "US",
    ) -> list[dict]:
        """
        Search flights using Skyscanner's browse quotes endpoint.
        This returns indicative prices (cached quotes), not live prices.
        """
        try:
            # Use the Browse Quotes endpoint for fast cached results
            url = (
                f"{self.BASE_URL}/browsequotes/v1.0"
                f"/{market}/{currency}/{locale}"
                f"/{origin.upper()}/{destination.upper()}"
                f"/{departure_date.strftime('%Y-%m-%d')}"
            )
            headers = {
                "x-rapidapi-key": self.api_key,
                "x-rapidapi-host": "skyscanner-skyscanner-flight-search-v1.p.rapidapi.com",
            }

            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return self._parse_response(data, origin, destination, departure_date)

        except Exception as e:
            logger.warning("Skyscanner search failed: %s", e)
            return []

    def _parse_response(self, data: dict, origin: str, destination: str, departure_date: date) -> list[dict]:
        """Parse Skyscanner browse quotes response."""
        results = []

        # Build carrier lookup
        carriers = {c["CarrierId"]: c for c in data.get("Carriers", [])}
        # Build place lookup
        places = {p["PlaceId"]: p for p in data.get("Places", [])}

        for quote in data.get("Quotes", []):
            outbound = quote.get("OutboundLeg", {})
            carrier_ids = outbound.get("CarrierIds", [])
            carrier = carriers.get(carrier_ids[0], {}) if carrier_ids else {}

            origin_place = places.get(outbound.get("OriginId"), {})
            dest_place = places.get(outbound.get("DestinationId"), {})

            results.append({
                "source": "skyscanner",
                "origin": origin_place.get("IataCode", origin.upper()),
                "destination": dest_place.get("IataCode", destination.upper()),
                "price": float(quote.get("MinPrice", 0)),
                "airline_iata": carrier.get("CarrierId", ""),
                "airline_name": carrier.get("Name", "Unknown Airline"),
                "flight_number": None,
                "departure_at": outbound.get("DepartureDate", ""),
                "is_direct": quote.get("Direct", False),
                "transfers": 0 if quote.get("Direct", False) else 1,
                "booking_link": self._build_booking_link(origin, destination, departure_date),
            })

        return results

    def _build_booking_link(self, origin: str, destination: str, departure_date: date) -> str:
        """Build Skyscanner redirect link."""
        return (
            f"https://www.skyscanner.com/transport/flights"
            f"/{origin.lower()}/{destination.lower()}"
            f"/{departure_date.strftime('%y%m%d')}/"
        )

    async def close(self):
        await self.client.aclose()


# Module-level singleton
_client: SkyscannerClient | None = None


def init_skyscanner_client():
    global _client
    api_key = os.getenv("SKYSCANNER_API_KEY")
    if api_key:
        _client = SkyscannerClient(api_key)
        logger.info("Skyscanner client initialized")
    else:
        logger.warning("SKYSCANNER_API_KEY not set. Skyscanner search disabled.")


def get_skyscanner_client() -> SkyscannerClient | None:
    return _client
