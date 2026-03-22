"""Price alert management service."""
import logging
from datetime import datetime
from uuid import uuid4

from app.schemas.alert import AlertCreate, AlertResponse, AlertUpdate

logger = logging.getLogger(__name__)


class AlertService:
    """Manages flight price alerts using in-memory storage."""

    def __init__(self) -> None:
        self._alerts: dict[str, AlertResponse] = {}

    def create_alert(self, data: AlertCreate) -> AlertResponse:
        """Create a new price alert."""
        alert_id = str(uuid4())
        alert = AlertResponse(
            id=alert_id,
            origin=data.origin.upper(),
            destination=data.destination.upper(),
            departure_date=data.departure_date,
            target_price=data.target_price,
            currency=data.currency.upper(),
            email=data.email,
            is_active=True,
            created_at=datetime.utcnow(),
            triggered_at=None,
        )
        self._alerts[alert_id] = alert
        logger.info("Created alert %s for %s -> %s at %.2f", alert_id, data.origin, data.destination, data.target_price)
        return alert

    def get_alert(self, alert_id: str) -> AlertResponse | None:
        """Retrieve an alert by ID."""
        return self._alerts.get(alert_id)

    def list_alerts(self) -> list[AlertResponse]:
        """Return all stored alerts."""
        return list(self._alerts.values())

    def update_alert(self, alert_id: str, data: AlertUpdate) -> AlertResponse | None:
        """Update an existing alert."""
        alert = self._alerts.get(alert_id)
        if alert is None:
            return None
        updated = alert.model_copy(
            update={
                k: v for k, v in data.model_dump(exclude_none=True).items()
            }
        )
        self._alerts[alert_id] = updated
        return updated

    def delete_alert(self, alert_id: str) -> bool:
        """Delete an alert. Returns True if it existed."""
        if alert_id in self._alerts:
            del self._alerts[alert_id]
            return True
        return False

    def check_alerts(self, origin: str, destination: str, current_price: float, currency: str) -> list[AlertResponse]:
        """Check if any active alerts are triggered by the given price."""
        triggered: list[AlertResponse] = []
        for alert in self._alerts.values():
            if (
                alert.is_active
                and alert.origin == origin.upper()
                and alert.destination == destination.upper()
                and alert.currency == currency.upper()
                and current_price <= alert.target_price
            ):
                alert_copy = alert.model_copy(update={"triggered_at": datetime.utcnow()})
                self._alerts[alert.id] = alert_copy
                triggered.append(alert_copy)
                logger.info("Alert %s triggered! Price %.2f <= target %.2f", alert.id, current_price, alert.target_price)
        return triggered
