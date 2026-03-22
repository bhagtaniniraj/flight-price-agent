from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Airport, Flight
from app.schemas import PredictionResponse
from app.services.prediction_engine import generate_prediction

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


@router.get("", response_model=PredictionResponse)
async def get_prediction(
    origin: str = Query(..., min_length=3, max_length=3),
    destination: str = Query(..., min_length=3, max_length=3),
    travel_date: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    orig_upper = origin.upper()
    dest_upper = destination.upper()

    origin_alias = Airport.__table__.alias("orig_pred")
    dest_alias = Airport.__table__.alias("dest_pred")

    stmt = (
        select(func.avg(Flight.price_economy))
        .join(origin_alias, Flight.origin_id == origin_alias.c.id)
        .join(dest_alias, Flight.destination_id == dest_alias.c.id)
        .where(origin_alias.c.iata_code == orig_upper)
        .where(dest_alias.c.iata_code == dest_upper)
    )
    result = await db.execute(stmt)
    avg_price = result.scalar()

    if avg_price is None:
        raise HTTPException(status_code=404, detail="No flights found for this route")

    return generate_prediction(orig_upper, dest_upper, travel_date, float(avg_price))
