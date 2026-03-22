import random
import string
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Booking, Flight
from app.schemas import BookingCreate, BookingResponse, FlightResponse
from app.services.price_engine import compute_price

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


def _generate_reference() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def _booking_flight_response(flight: Flight, seat_class: str) -> FlightResponse:
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


@router.post("", response_model=BookingResponse, status_code=201)
async def create_booking(data: BookingCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Flight)
        .options(selectinload(Flight.airline), selectinload(Flight.origin), selectinload(Flight.destination))
        .where(Flight.id == data.flight_id)
    )
    flight = result.scalars().first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    if flight.seats_available < data.passenger_count:
        raise HTTPException(status_code=400, detail="Not enough seats available")

    if data.seat_class == "business":
        base = flight.price_business
    elif data.seat_class == "first":
        base = flight.price_first
    else:
        base = flight.price_economy

    unit_price = compute_price(base, data.seat_class, flight.departure_time)
    total = round(unit_price * data.passenger_count, 2)

    ref = _generate_reference()
    while True:
        existing = await db.execute(select(Booking).where(Booking.booking_reference == ref))
        if not existing.scalars().first():
            break
        ref = _generate_reference()

    booking = Booking(
        booking_reference=ref,
        flight_id=data.flight_id,
        passenger_name=data.passenger_name,
        passenger_email=data.passenger_email,
        passenger_count=data.passenger_count,
        seat_class=data.seat_class,
        total_price=total,
        status="confirmed",
    )
    db.add(booking)
    flight.seats_available = max(0, flight.seats_available - data.passenger_count)
    await db.commit()
    await db.refresh(booking)

    flight_resp = _booking_flight_response(flight, data.seat_class)
    return BookingResponse(
        id=booking.id,
        booking_reference=booking.booking_reference,
        flight=flight_resp,
        passenger_name=booking.passenger_name,
        passenger_email=booking.passenger_email,
        passenger_count=booking.passenger_count,
        seat_class=booking.seat_class,
        total_price=booking.total_price,
        status=booking.status,
        payment_status=booking.payment_status,
        created_at=booking.created_at,
    )


@router.get("", response_model=list[BookingResponse])
async def list_bookings(email: str = Query(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Booking)
        .options(
            selectinload(Booking.flight).options(
                selectinload(Flight.airline),
                selectinload(Flight.origin),
                selectinload(Flight.destination),
            )
        )
        .where(Booking.passenger_email == email)
        .order_by(Booking.created_at.desc())
    )
    bookings = result.scalars().all()
    out = []
    for b in bookings:
        fr = _booking_flight_response(b.flight, b.seat_class)
        out.append(BookingResponse(
            id=b.id,
            booking_reference=b.booking_reference,
            flight=fr,
            passenger_name=b.passenger_name,
            passenger_email=b.passenger_email,
            passenger_count=b.passenger_count,
            seat_class=b.seat_class,
            total_price=b.total_price,
            status=b.status,
            payment_status=b.payment_status,
            created_at=b.created_at,
        ))
    return out


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Booking)
        .options(
            selectinload(Booking.flight).options(
                selectinload(Flight.airline),
                selectinload(Flight.origin),
                selectinload(Flight.destination),
            )
        )
        .where(Booking.id == booking_id)
    )
    booking = result.scalars().first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    fr = _booking_flight_response(booking.flight, booking.seat_class)
    return BookingResponse(
        id=booking.id,
        booking_reference=booking.booking_reference,
        flight=fr,
        passenger_name=booking.passenger_name,
        passenger_email=booking.passenger_email,
        passenger_count=booking.passenger_count,
        seat_class=booking.seat_class,
        total_price=booking.total_price,
        status=booking.status,
        payment_status=booking.payment_status,
        created_at=booking.created_at,
    )


@router.delete("/{booking_id}", status_code=204)
async def cancel_booking(booking_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalars().first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking.status = "cancelled"
    await db.commit()
