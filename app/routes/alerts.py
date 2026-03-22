from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import PriceAlert
from app.schemas import AlertCreate, AlertResponse

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.post("", response_model=AlertResponse, status_code=201)
async def create_alert(data: AlertCreate, db: AsyncSession = Depends(get_db)):
    alert = PriceAlert(
        origin_iata=data.origin_iata.upper(),
        destination_iata=data.destination_iata.upper(),
        target_price=data.target_price,
        user_email=data.user_email,
        is_active=True,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.get("", response_model=list[AlertResponse])
async def list_alerts(email: str = Query(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PriceAlert)
        .where(PriceAlert.user_email == email, PriceAlert.is_active)  # noqa: E712
        .order_by(PriceAlert.created_at.desc())
    )
    return result.scalars().all()


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PriceAlert).where(PriceAlert.id == alert_id))
    alert = result.scalars().first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.delete(alert)
    await db.commit()
