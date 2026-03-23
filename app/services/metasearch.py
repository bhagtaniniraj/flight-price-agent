import asyncio
import logging
from datetime import date, datetime, timedelta

from app.schemas import FlightResponse, AirlineInfo, AirportInfo
from app.services.travelpayouts_client import get_travelpayouts_client
from app.services.skyscanner_client import get_skyscanner_client

logger = logging.getLogger(__name__)

# Common airline names lookup (for when APIs only return IATA codes)
AIRLINE_NAMES = {
    "6E": "IndiGo", "AI": "Air India", "SG": "SpiceJet", "UK": "Vistara",
    "QP": "Akasa Air", "IX": "Air India Express", "AA": "American Airlines",
    "UA": "United Airlines", "DL": "Delta Air Lines", "BA": "British Airways",
    "EK": "Emirates", "SQ": "Singapore Airlines", "LH": "Lufthansa",
    "AF": "Air France", "QR": "Qatar Airways", "TK": "Turkish Airlines",
    "CX": "Cathay Pacific", "NH": "All Nippon Airways", "QF": "Qantas",
    "AC": "Air Canada", "WN": "Southwest Airlines", "B6": "JetBlue Airways",
    "AS": "Alaska Airlines", "KE": "Korean Air", "JL": "Japan Airlines",
    "EY": "Etihad Airways", "KL": "KLM", "IB": "Iberia",
}


def _make_airline_info(iata_code: str, name: str = "") -> AirlineInfo:
    """Create AirlineInfo from IATA code."""
    if not name:
        name = AIRLINE_NAMES.get(iata_code.upper(), iata_code or "Unknown")
    return AirlineInfo(iata_code=iata_code.upper() if iata_code else "??", name=name, color="#666666")


def _make_airport_info(iata_code: str) -> AirportInfo:
    """Create minimal AirportInfo from IATA code."""
    return AirportInfo(iata_code=iata_code.upper(), name=iata_code.upper(), city=iata_code.upper())


def _parse_datetime(dt_str: str) -> datetime | None:
    """Try to parse various datetime formats."""
    if not dt_str:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    return None


def _travelpayouts_to_response(item: dict, departure_date: date | None = None) -> FlightResponse | None:
    """Convert a Travelpayouts result dict to FlightResponse."""
    try:
        dep_time = _parse_datetime(item.get("departure_at", ""))
        if not dep_time:
            # Use the requested departure date as fallback
            if departure_date:
                dep_time = datetime(departure_date.year, departure_date.month, departure_date.day, 0, 0, 0)
            else:
                dep_time = datetime.now()

        # Estimate arrival using 2 hours; actual duration is unavailable from this API
        arr_time = dep_time + timedelta(hours=2)
        duration = 120  # estimated — Travelpayouts API does not return flight duration

        return FlightResponse(
            id=0,  # not from DB
            flight_number=item.get("flight_number") or f"{item.get('airline_iata', '??')}---",
            airline=_make_airline_info(item.get("airline_iata", "")),
            origin=_make_airport_info(item.get("origin", "")),
            destination=_make_airport_info(item.get("destination", "")),
            departure_time=dep_time,
            arrival_time=arr_time,
            duration_minutes=duration,
            price=item.get("price", 0),
            stops=item.get("transfers", 0),
            layover_airports=[],
            bags_included=1,
            is_deal=False,
            seats_available=9,
            source="travelpayouts",
            booking_link=item.get("booking_link", ""),
        )
    except Exception as e:
        logger.warning("Failed to map Travelpayouts result: %s", e)
        return None


def _skyscanner_to_response(item: dict, departure_date: date | None = None) -> FlightResponse | None:
    """Convert a Skyscanner result dict to FlightResponse."""
    try:
        dep_time = _parse_datetime(item.get("departure_at", ""))
        if not dep_time:
            # Use the requested departure date as fallback
            if departure_date:
                dep_time = datetime(departure_date.year, departure_date.month, departure_date.day, 0, 0, 0)
            else:
                dep_time = datetime.now()

        # Estimate arrival using 2 hours; actual duration is unavailable from this API
        arr_time = dep_time + timedelta(hours=2)
        duration = 120  # estimated — Skyscanner browse-quotes does not return flight duration

        return FlightResponse(
            id=0,
            flight_number=f"{item.get('airline_iata', '??')}---",
            airline=_make_airline_info(
                item.get("airline_iata", ""),
                item.get("airline_name", ""),
            ),
            origin=_make_airport_info(item.get("origin", "")),
            destination=_make_airport_info(item.get("destination", "")),
            departure_time=dep_time,
            arrival_time=arr_time,
            duration_minutes=duration,
            price=item.get("price", 0),
            stops=item.get("transfers", 0),
            layover_airports=[],
            bags_included=1,
            is_deal=False,
            seats_available=9,
            source="skyscanner",
            booking_link=item.get("booking_link", ""),
        )
    except Exception as e:
        logger.warning("Failed to map Skyscanner result: %s", e)
        return None


async def metasearch_flights(
    origin: str,
    destination: str,
    departure_date: date,
    passengers: int = 1,
) -> list[FlightResponse]:
    """
    Fan out search to all configured external APIs.
    Returns merged list of FlightResponse from external sources.
    """
    tasks = []
    source_names = []

    # Travelpayouts
    tp_client = get_travelpayouts_client()
    if tp_client:
        tasks.append(tp_client.search_prices(origin, destination, departure_date))
        source_names.append("travelpayouts")

    # Skyscanner
    sk_client = get_skyscanner_client()
    if sk_client:
        tasks.append(sk_client.search_flights(origin, destination, departure_date))
        source_names.append("skyscanner")

    if not tasks:
        logger.info("No external search APIs configured")
        return []

    # Run all searches concurrently with timeout
    try:
        raw_results = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=20.0,
        )
    except asyncio.TimeoutError:
        logger.warning("Metasearch timed out")
        return []

    # Map results to FlightResponse
    all_responses = []
    for i, result in enumerate(raw_results):
        if isinstance(result, Exception):
            logger.warning("Search source %s failed: %s", source_names[i], result)
            continue
        if not isinstance(result, list):
            continue

        source = source_names[i]
        for item in result:
            if source == "travelpayouts":
                resp = _travelpayouts_to_response(item, departure_date)
            elif source == "skyscanner":
                resp = _skyscanner_to_response(item, departure_date)
            else:
                continue
            if resp:
                all_responses.append(resp)

    logger.info("Metasearch returned %d results from %d sources", len(all_responses), len(source_names))
    return all_responses
