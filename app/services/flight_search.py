from datetime import date, datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Airport, Flight
from app.schemas import FlightResponse
from app.services.price_engine import compute_price


def _flight_to_response(flight: Flight, seat_class: str) -> FlightResponse:
    if seat_class == "business":
        base = flight.price_business
    elif seat_class == "first":
        base = flight.price_first
    else:
        base = flight.price_economy

    price = compute_price(base, seat_class, flight.departure_time)
    layovers = [c.strip() for c in flight.layover_airports.split(",") if c.strip()]

    return FlightResponse(
        id=flight.id,
        flight_number=flight.flight_number,
        airline=flight.airline,
        origin=flight.origin,
        destination=flight.destination,
        departure_time=flight.departure_time,
        arrival_time=flight.arrival_time,
        duration_minutes=flight.duration_minutes,
        price=price,
        stops=flight.stops,
        layover_airports=layovers,
        bags_included=flight.bags_included,
        is_deal=flight.is_deal,
        seats_available=flight.seats_available,
    )


async def search_flights(
    db: AsyncSession,
    origin: str,
    destination: str,
    departure_date: date,
    seat_class: str = "economy",
    max_stops: int | None = None,
    max_price: float | None = None,
    airlines: list[str] | None = None,
    sort_by: str = "price",
) -> list[FlightResponse]:
    origin_alias = Airport.__table__.alias("origin_ap")
    dest_alias = Airport.__table__.alias("dest_ap")
    day_start = datetime(departure_date.year, departure_date.month, departure_date.day, 0, 0, 0)

    stmt = (
        select(Flight)
        .options(
            selectinload(Flight.airline),
            selectinload(Flight.origin),
            selectinload(Flight.destination),
        )
        .join(origin_alias, Flight.origin_id == origin_alias.c.id)
        .join(dest_alias, Flight.destination_id == dest_alias.c.id)
        .where(origin_alias.c.iata_code == origin.upper())
        .where(dest_alias.c.iata_code == destination.upper())
        .where(Flight.departure_time >= day_start)
        .where(Flight.departure_time < day_start + timedelta(days=1))
    )

    if max_stops is not None:
        stmt = stmt.where(Flight.stops <= max_stops)

    result = await db.execute(stmt)
    flights = result.scalars().all()

    responses = [_flight_to_response(f, seat_class) for f in flights]

    if max_price is not None:
        responses = [r for r in responses if r.price <= max_price]

    if airlines:
        airline_upper = [a.upper() for a in airlines]
        responses = [r for r in responses if r.airline.iata_code in airline_upper]

    if sort_by == "duration":
        responses.sort(key=lambda r: r.duration_minutes)
    elif sort_by == "departure":
        responses.sort(key=lambda r: r.departure_time)
    elif sort_by == "stops":
        responses.sort(key=lambda r: r.stops)
    else:
        responses.sort(key=lambda r: r.price)

    return responses
