from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import FlightResponse
from app.services.flight_search import search_flights

router = APIRouter(prefix="/api/flights", tags=["flights"])


@router.get("/search", response_model=list[FlightResponse])
async def search_flights_endpoint(
    origin: str = Query(..., min_length=3, max_length=3),
    destination: str = Query(..., min_length=3, max_length=3),
    departure_date: str = Query(...),
    passengers: int = Query(1, ge=1, le=9),
    seat_class: str = Query("economy"),
    sort_by: str = Query("price"),
    max_stops: Optional[int] = Query(None),
    max_price: Optional[float] = Query(None),
    airlines: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    try:
        dep_date = date.fromisoformat(departure_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid departure_date format. Use YYYY-MM-DD.")

    airline_list = [a.strip() for a in airlines.split(",")] if airlines else None

    results = await search_flights(
        db=db,
        origin=origin.upper(),
        destination=destination.upper(),
        departure_date=dep_date,
        seat_class=seat_class,
        max_stops=max_stops,
        max_price=max_price,
        airlines=airline_list,
        sort_by=sort_by,
    )
    return results
