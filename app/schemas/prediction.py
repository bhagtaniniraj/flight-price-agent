"""Price prediction Pydantic schemas."""
from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    origin: str = Field(..., min_length=3, max_length=3)
    destination: str = Field(..., min_length=3, max_length=3)
    departure_date: str
    days_until_departure: int = Field(..., ge=0)
    current_price: float = Field(..., gt=0)
    adults: int = Field(1, ge=1, le=9)


class PredictionResponse(BaseModel):
    origin: str
    destination: str
    departure_date: str
    current_price: float
    predicted_price: float
    recommendation: str  # "buy_now", "wait", "good_deal"
    confidence: float  # 0.0 to 1.0
    price_trend: str  # "rising", "falling", "stable"
    days_until_departure: int
