from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict


class AirportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    iata_code: str
    name: str
    city: str
    country: str
    latitude: float
    longitude: float


class AirlineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    iata_code: str
    name: str
    color: str
    country: str


class AirlineInfo(BaseModel):
    """Lightweight airline info for external API results."""
    iata_code: str
    name: str
    color: str = "#666666"


class AirportInfo(BaseModel):
    """Lightweight airport info for external API results."""
    iata_code: str
    name: str
    city: str


class FlightSearchRequest(BaseModel):
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str] = None
    passengers: int = 1
    seat_class: str = "economy"


class FlightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    flight_number: str
    airline: Union[AirlineResponse, AirlineInfo]
    origin: Union[AirportResponse, AirportInfo]
    destination: Union[AirportResponse, AirportInfo]
    departure_time: datetime
    arrival_time: datetime
    duration_minutes: int
    price: float
    stops: int
    layover_airports: list[str]
    bags_included: int
    is_deal: bool
    seats_available: int
    source: str = "seed"
    booking_link: str = ""


class BookingCreate(BaseModel):
    flight_id: int
    passenger_name: str
    passenger_email: str
    passenger_count: int = 1
    seat_class: str = "economy"


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    booking_reference: str
    flight: FlightResponse
    passenger_name: str
    passenger_email: str
    passenger_count: int
    seat_class: str
    total_price: float
    status: str
    payment_status: str
    created_at: datetime


class AlertCreate(BaseModel):
    origin_iata: str
    destination_iata: str
    target_price: float
    user_email: str


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    origin_iata: str
    destination_iata: str
    target_price: float
    user_email: str
    is_active: bool
    created_at: datetime


class PricePoint(BaseModel):
    date: str
    price: float


class PredictionResponse(BaseModel):
    origin: str
    destination: str
    travel_date: str
    current_avg_price: float
    predicted_price: float
    trend: str
    recommendation: str
    confidence: float
    price_history: list[PricePoint]


class CheckoutRequest(BaseModel):
    booking_id: int
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class PaymentStatusResponse(BaseModel):
    booking_id: int
    status: str
    amount: float
