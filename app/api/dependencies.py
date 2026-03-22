"""FastAPI dependency injection functions."""
from functools import lru_cache

from app.config import Settings, get_settings
from app.services.aggregator import FlightAggregator
from app.services.alert_service import AlertService


@lru_cache(maxsize=1)
def _get_aggregator_instance() -> FlightAggregator:
    settings = get_settings()
    return FlightAggregator(settings)


@lru_cache(maxsize=1)
def _get_alert_service_instance() -> AlertService:
    return AlertService()


def get_aggregator() -> FlightAggregator:
    """Return the shared FlightAggregator instance."""
    return _get_aggregator_instance()


def get_alert_service() -> AlertService:
    """Return the shared AlertService instance."""
    return _get_alert_service_instance()


def get_app_settings() -> Settings:
    """Return the application Settings instance."""
    return get_settings()
