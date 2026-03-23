import httpx
import logging
import os
from datetime import date

logger = logging.getLogger(__name__)


class TravelpayoutsClient:
    """Client for Travelpayouts/Aviasales flight search API."""

    BASE_URL = "https://api.travelpayouts.com"

    def __init__(self, api_token: str, marker: str):
        self.api_token = api_token
        self.marker = marker  # affiliate marker for earning commissions
        self.client = httpx.AsyncClient(timeout=15.0)

    async def search_prices(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        currency: str = "USD",
    ) -> list[dict]:
        """
        Search for cheapest flight prices.
        Uses the /v1/prices/cheap endpoint for price data.
        Falls back to /v2/prices/latest if cheap endpoint fails.
        """
        try:
            # Try the prices/cheap endpoint first
            params = {
                "origin": origin.upper(),
                "destination": destination.upper(),
                "depart_date": departure_date.strftime("%Y-%m"),
                "currency": currency.lower(),
                "token": self.api_token,
            }
            response = await self.client.get(
                f"{self.BASE_URL}/v1/prices/cheap",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("success") and data.get("data"):
                return self._parse_cheap_response(data, origin, destination, departure_date)

            # Fallback: try latest prices
            return await self._search_latest(origin, destination, departure_date, currency)

        except Exception as e:
            logger.warning("Travelpayouts search failed: %s", e)
            return []

    async def _search_latest(self, origin, destination, departure_date, currency):
        """Fallback search using /v2/prices/latest endpoint."""
        try:
            params = {
                "origin": origin.upper(),
                "destination": destination.upper(),
                "period_type": "month",
                "beginning_of_period": departure_date.strftime("%Y-%m-01"),
                "currency": currency.lower(),
                "token": self.api_token,
                "limit": 30,
                "sorting": "price",
            }
            response = await self.client.get(
                f"{self.BASE_URL}/v2/prices/latest",
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            if data.get("success") and data.get("data"):
                return self._parse_latest_response(data, origin, destination, departure_date)
            return []
        except Exception as e:
            logger.warning("Travelpayouts latest search failed: %s", e)
            return []

    def _parse_cheap_response(self, data, origin, destination, departure_date) -> list[dict]:
        """Parse the /v1/prices/cheap response format."""
        results = []
        dest_data = data.get("data", {}).get(destination.upper(), {})
        for key, flight_info in dest_data.items():
            results.append({
                "source": "travelpayouts",
                "origin": origin.upper(),
                "destination": destination.upper(),
                "price": float(flight_info.get("price", 0)),
                "airline_iata": flight_info.get("airline", ""),
                "flight_number": flight_info.get("flight_number", None),
                "departure_at": flight_info.get("departure_at", ""),
                "return_at": flight_info.get("return_at", ""),
                "transfers": int(flight_info.get("transfers", 0)),
                "expires_at": flight_info.get("expires_at", ""),
                "booking_link": self._build_booking_link(origin, destination, departure_date),
            })
        return results

    def _parse_latest_response(self, data, origin, destination, departure_date) -> list[dict]:
        """Parse the /v2/prices/latest response format."""
        results = []
        for flight_info in data.get("data", []):
            results.append({
                "source": "travelpayouts",
                "origin": flight_info.get("origin", origin.upper()),
                "destination": flight_info.get("destination", destination.upper()),
                "price": float(flight_info.get("value", 0)),
                "airline_iata": flight_info.get("gate", ""),
                "flight_number": None,
                "departure_at": flight_info.get("depart_date", ""),
                "return_at": flight_info.get("return_date", ""),
                "transfers": int(flight_info.get("number_of_changes", 0)),
                "expires_at": "",
                "booking_link": self._build_booking_link(origin, destination, departure_date),
            })
        return results

    def _build_booking_link(self, origin: str, destination: str, departure_date: date) -> str:
        """Build Aviasales affiliate deep link."""
        return (
            f"https://www.aviasales.com/search/"
            f"{origin.upper()}{departure_date.strftime('%d%m')}"
            f"{destination.upper()}1"
            f"?marker={self.marker}"
        )

    async def close(self):
        await self.client.aclose()


# Module-level singleton
_client: TravelpayoutsClient | None = None


def init_travelpayouts_client():
    global _client
    token = os.getenv("TRAVELPAYOUTS_API_TOKEN")
    marker = os.getenv("TRAVELPAYOUTS_MARKER", "direct")
    if token:
        _client = TravelpayoutsClient(token, marker)
        logger.info("Travelpayouts client initialized")
    else:
        logger.warning("TRAVELPAYOUTS_API_TOKEN not set. Travelpayouts search disabled.")


def get_travelpayouts_client() -> TravelpayoutsClient | None:
    return _client
