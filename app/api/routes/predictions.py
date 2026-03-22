"""Flight price prediction API routes."""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_aggregator
from app.ml.feature_engineering import FeatureEngineer
from app.ml.price_predictor import PricePredictor
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.aggregator import FlightAggregator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/predict", tags=["predictions"])

_predictor = PricePredictor()
_engineer = FeatureEngineer()


@router.post("/", response_model=PredictionResponse, summary="Predict future flight price")
async def predict_price(
    request: PredictionRequest,
    aggregator: Annotated[FlightAggregator, Depends(get_aggregator)],
) -> PredictionResponse:
    """Predict whether flight prices will rise or fall and recommend buy/wait."""
    try:
        features = _engineer.extract_features(request)
        predicted_price, confidence = _predictor.predict(features)

        change_pct = (predicted_price - request.current_price) / request.current_price

        if change_pct <= -0.05:
            recommendation = "wait"
            trend = "falling"
        elif change_pct >= 0.05:
            recommendation = "buy_now"
            trend = "rising"
        else:
            recommendation = "good_deal" if request.current_price < predicted_price * 0.9 else "wait"
            trend = "stable"

        return PredictionResponse(
            origin=request.origin.upper(),
            destination=request.destination.upper(),
            departure_date=request.departure_date,
            current_price=request.current_price,
            predicted_price=round(predicted_price, 2),
            recommendation=recommendation,
            confidence=round(confidence, 4),
            price_trend=trend,
            days_until_departure=request.days_until_departure,
        )
    except Exception as exc:
        logger.exception("Prediction failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc
