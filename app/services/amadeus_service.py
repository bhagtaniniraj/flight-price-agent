"""Amadeus flight search service."""
import logging
import time
import httpx
from app.config import Settings
from app.schemas.flight import FlightOffer, FlightSearchRequest, FlightSegment

logger = logging.getLogger(__name__)


class AmadeusService:
    """Service for searching flights via the Amadeus API."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def _get_access_token(self) -> str:
        """Obtain or return cached Amadeus OAuth2 access token."""
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        url = f"{self._settings.amadeus_base_url}/v1/security/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self._settings.amadeus_api_key,
            "client_secret": self._settings.amadeus_api_secret,
        }
        response = await self._client.post(url, data=data)
        response.raise_for_status()
        payload = response.json()
        self._access_token = payload["access_token"]
        self._token_expires_at = time.time() + payload.get("expires_in", 1799)
        return self._access_token  # type: ignore[return-value]

    async def search_flights(self, request: FlightSearchRequest) -> list[FlightOffer]:
        """Search for flight offers via Amadeus."""
        if not self._settings.amadeus_api_key:
            logger.warning("Amadeus API key not configured, skipping.")
            return []

        token = await self._get_access_token()
        url = f"{self._settings.amadeus_base_url}/v2/shopping/flight-offers"
        params: dict[str, str | int] = {
            "originLocationCode": request.origin.upper(),
            "destinationLocationCode": request.destination.upper(),
            "departureDate": request.departure_date,
            "adults": request.adults,
            "currencyCode": request.currency.upper(),
            "max": request.max_results,
        }
        headers = {"Authorization": f"Bearer {token}"}
        response = await self._client.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        return self._parse_offers(data.get("data", []), request.currency)

    def _parse_offers(self, raw_offers: list[dict], currency: str) -> list[FlightOffer]:
        """Parse raw Amadeus offers into FlightOffer objects."""
        offers: list[FlightOffer] = []
        for idx, item in enumerate(raw_offers):
            try:
                price = float(item["price"]["grandTotal"])
                airline_codes: list[str] = list(
                    {seg["carrierCode"] for itin in item.get("itineraries", []) for seg in itin.get("segments", [])}
                )
                segments: list[FlightSegment] = []
                first_itin = item.get("itineraries", [{}])[0]
                for seg in first_itin.get("segments", []):
                    segments.append(
                        FlightSegment(
                            departure_airport=seg["departure"]["iataCode"],
                            arrival_airport=seg["arrival"]["iataCode"],
                            departure_time=seg["departure"].get("at", ""),
                            arrival_time=seg["arrival"].get("at", ""),
                            carrier_code=seg["carrierCode"],
                            flight_number=seg["number"],
                            duration=seg.get("duration", ""),
                        )
                    )
                total_duration = first_itin.get("duration", "")
                offers.append(
                    FlightOffer(
                        id=f"amadeus-{item.get('id', idx)}",
                        source="amadeus",
                        price=price,
                        currency=currency,
                        airline_codes=airline_codes,
                        segments=segments,
                        total_duration=total_duration,
                        deep_link=None,
                    )
                )
            except (KeyError, ValueError, IndexError) as exc:
                logger.warning("Failed to parse Amadeus offer %d: %s", idx, exc)
        return offers
