"""Pydantic schemas for the flight price agent."""
from app.schemas.flight import FlightOffer, FlightSearchRequest, FlightSearchResponse, FlightSegment
from app.schemas.alert import AlertCreate, AlertResponse, AlertUpdate
from app.schemas.prediction import PredictionRequest, PredictionResponse

__all__ = [
    "FlightOffer", "FlightSearchRequest", "FlightSearchResponse", "FlightSegment",
    "AlertCreate", "AlertResponse", "AlertUpdate",
    "PredictionRequest", "PredictionResponse",
]
