from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Airport(Base):
    __tablename__ = "airports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    iata_code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False)

    origins: Mapped[list["Flight"]] = relationship("Flight", foreign_keys="Flight.origin_id", back_populates="origin")
    destinations: Mapped[list["Flight"]] = relationship("Flight", foreign_keys="Flight.destination_id", back_populates="destination")


class Airline(Base):
    __tablename__ = "airlines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    iata_code: Mapped[str] = mapped_column(String(2), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)

    flights: Mapped[list["Flight"]] = relationship("Flight", back_populates="airline")


class Flight(Base):
    __tablename__ = "flights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flight_number: Mapped[str] = mapped_column(String(10), nullable=False)
    airline_id: Mapped[int] = mapped_column(Integer, ForeignKey("airlines.id"), nullable=False)
    origin_id: Mapped[int] = mapped_column(Integer, ForeignKey("airports.id"), nullable=False)
    destination_id: Mapped[int] = mapped_column(Integer, ForeignKey("airports.id"), nullable=False)
    departure_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    arrival_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    price_economy: Mapped[float] = mapped_column(Float, nullable=False)
    price_business: Mapped[float] = mapped_column(Float, nullable=False)
    price_first: Mapped[float] = mapped_column(Float, nullable=False)
    stops: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    layover_airports: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    bags_included: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_deal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    seats_available: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow(), nullable=False)

    airline: Mapped["Airline"] = relationship("Airline", back_populates="flights")
    origin: Mapped["Airport"] = relationship("Airport", foreign_keys=[origin_id], back_populates="origins")
    destination: Mapped["Airport"] = relationship("Airport", foreign_keys=[destination_id], back_populates="destinations")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="flight")


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    booking_reference: Mapped[str] = mapped_column(String(6), unique=True, nullable=False)
    flight_id: Mapped[int] = mapped_column(Integer, ForeignKey("flights.id"), nullable=False)
    passenger_name: Mapped[str] = mapped_column(String(200), nullable=False)
    passenger_email: Mapped[str] = mapped_column(String(200), nullable=False)
    passenger_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    seat_class: Mapped[str] = mapped_column(String(20), nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="confirmed", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow(), nullable=False)

    flight: Mapped["Flight"] = relationship("Flight", back_populates="bookings")


class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    origin_iata: Mapped[str] = mapped_column(String(3), nullable=False)
    destination_iata: Mapped[str] = mapped_column(String(3), nullable=False)
    target_price: Mapped[float] = mapped_column(Float, nullable=False)
    user_email: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.utcnow(), nullable=False)
