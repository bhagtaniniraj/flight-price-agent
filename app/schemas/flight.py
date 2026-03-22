"""Flight-related Pydantic schemas."""
from datetime import datetime
from pydantic import BaseModel, Field


class FlightSearchRequest(BaseModel):
    origin: str = Field(..., min_length=3, max_length=3, description="IATA origin airport code")
    destination: str = Field(..., min_length=3, max_length=3, description="IATA destination airport code")
    departure_date: str = Field(..., description="Departure date in YYYY-MM-DD format")
    return_date: str | None = Field(None, description="Return date for round trips in YYYY-MM-DD format")
    adults: int = Field(1, ge=1, le=9)
    currency: str = Field("USD", min_length=3, max_length=3)
    max_results: int = Field(10, ge=1, le=50)


class FlightSegment(BaseModel):
    departure_airport: str
    arrival_airport: str
    departure_time: str
    arrival_time: str
    carrier_code: str
    flight_number: str
    duration: str


class FlightOffer(BaseModel):
    id: str
    source: str  # "amadeus", "kiwi", "duffel"
    price: float
    currency: str
    airline_codes: list[str]
    segments: list[FlightSegment]
    total_duration: str
    deep_link: str | None = None
    is_deal: bool = False
    bags_included: int = 0


class FlightSearchResponse(BaseModel):
    search_id: str
    origin: str
    destination: str
    departure_date: str
    offers: list[FlightOffer]
    cheapest_price: float | None
    total_results: int
    providers_queried: list[str]
    search_timestamp: datetime
