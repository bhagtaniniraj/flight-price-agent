"""Kiwi/Tequila flight search service."""
import logging
from datetime import datetime, timezone
import httpx
from app.config import Settings
from app.schemas.flight import FlightOffer, FlightSearchRequest, FlightSegment

logger = logging.getLogger(__name__)


class KiwiService:
    """Service for searching flights via the Kiwi/Tequila API."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def search_flights(self, request: FlightSearchRequest) -> list[FlightOffer]:
        """Search for flight offers via Kiwi/Tequila."""
        if not self._settings.kiwi_api_key:
            logger.warning("Kiwi API key not configured, skipping.")
            return []

        dep_dt = datetime.strptime(request.departure_date, "%Y-%m-%d")
        date_str = dep_dt.strftime("%d/%m/%Y")

        url = f"{self._settings.kiwi_base_url}/v2/search"
        params: dict[str, str | int] = {
            "fly_from": request.origin.upper(),
            "fly_to": request.destination.upper(),
            "date_from": date_str,
            "date_to": date_str,
            "curr": request.currency.upper(),
            "limit": request.max_results,
            "adults": request.adults,
        }
        headers = {"apikey": self._settings.kiwi_api_key}
        response = await self._client.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        return self._parse_offers(data.get("data", []), request.currency)

    def _parse_offers(self, raw_offers: list[dict], currency: str) -> list[FlightOffer]:
        """Parse raw Kiwi offers into FlightOffer objects."""
        offers: list[FlightOffer] = []
        for idx, item in enumerate(raw_offers):
            try:
                price = float(item["price"])
                airline_codes: list[str] = list({a for a in item.get("airlines", [])})
                segments: list[FlightSegment] = []
                for route in item.get("route", []):
                    dep_ts = route.get("dTimeUTC", 0)
                    arr_ts = route.get("aTimeUTC", 0)
                    dep_time = datetime.fromtimestamp(dep_ts, tz=timezone.utc).isoformat() if dep_ts else ""
                    arr_time = datetime.fromtimestamp(arr_ts, tz=timezone.utc).isoformat() if arr_ts else ""
                    segments.append(
                        FlightSegment(
                            departure_airport=route.get("flyFrom", ""),
                            arrival_airport=route.get("flyTo", ""),
                            departure_time=dep_time,
                            arrival_time=arr_time,
                            carrier_code=route.get("airline", ""),
                            flight_number=route.get("flight_no", ""),
                            duration=str(route.get("flight_duration", "")),
                        )
                    )
                total_secs = item.get("duration", {}).get("total", 0)
                total_duration = f"PT{total_secs // 3600}H{(total_secs % 3600) // 60}M"
                offers.append(
                    FlightOffer(
                        id=f"kiwi-{item.get('id', idx)}",
                        source="kiwi",
                        price=price,
                        currency=currency,
                        airline_codes=airline_codes,
                        segments=segments,
                        total_duration=total_duration,
                        deep_link=item.get("deep_link"),
                    )
                )
            except (KeyError, ValueError, TypeError) as exc:
                logger.warning("Failed to parse Kiwi offer %d: %s", idx, exc)
        return offers
