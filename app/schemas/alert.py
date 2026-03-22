"""Price alert Pydantic schemas."""
from datetime import datetime
from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    origin: str = Field(..., min_length=3, max_length=3)
    destination: str = Field(..., min_length=3, max_length=3)
    departure_date: str
    target_price: float = Field(..., gt=0)
    currency: str = Field("USD", min_length=3, max_length=3)
    email: str | None = None


class AlertUpdate(BaseModel):
    target_price: float | None = Field(None, gt=0)
    is_active: bool | None = None


class AlertResponse(BaseModel):
    id: str
    origin: str
    destination: str
    departure_date: str
    target_price: float
    currency: str
    email: str | None
    is_active: bool
    created_at: datetime
    triggered_at: datetime | None = None
