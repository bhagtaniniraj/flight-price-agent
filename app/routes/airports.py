from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Airport
from app.schemas import AirportResponse

router = APIRouter(prefix="/api/airports", tags=["airports"])


@router.get("", response_model=list[AirportResponse])
async def search_airports(
    q: str = Query("", min_length=0),
    db: AsyncSession = Depends(get_db),
):
    if not q:
        result = await db.execute(select(Airport).limit(10))
        return result.scalars().all()

    pattern = f"%{q}%"
    stmt = (
        select(Airport)
        .where(
            or_(
                Airport.iata_code.ilike(pattern),
                Airport.city.ilike(pattern),
                Airport.name.ilike(pattern),
            )
        )
        .limit(10)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{code}", response_model=AirportResponse)
async def get_airport(code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Airport).where(Airport.iata_code == code.upper())
    )
    airport = result.scalars().first()
    if not airport:
        raise HTTPException(status_code=404, detail="Airport not found")
    return airport
