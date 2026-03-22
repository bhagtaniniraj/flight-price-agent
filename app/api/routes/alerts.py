"""Price alert API routes."""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_alert_service
from app.schemas.alert import AlertCreate, AlertResponse, AlertUpdate
from app.services.alert_service import AlertService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/", response_model=AlertResponse, status_code=201, summary="Create a price alert")
async def create_alert(
    data: AlertCreate,
    service: Annotated[AlertService, Depends(get_alert_service)],
) -> AlertResponse:
    """Create a new price alert for a given route and target price."""
    return service.create_alert(data)


@router.get("/", response_model=list[AlertResponse], summary="List all alerts")
async def list_alerts(
    service: Annotated[AlertService, Depends(get_alert_service)],
) -> list[AlertResponse]:
    """Return all stored price alerts."""
    return service.list_alerts()


@router.get("/{alert_id}", response_model=AlertResponse, summary="Get an alert by ID")
async def get_alert(
    alert_id: str,
    service: Annotated[AlertService, Depends(get_alert_service)],
) -> AlertResponse:
    """Return a single alert by its ID."""
    alert = service.get_alert(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return alert


@router.patch("/{alert_id}", response_model=AlertResponse, summary="Update an alert")
async def update_alert(
    alert_id: str,
    data: AlertUpdate,
    service: Annotated[AlertService, Depends(get_alert_service)],
) -> AlertResponse:
    """Update target price or active status of an alert."""
    updated = service.update_alert(alert_id, data)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return updated


@router.delete("/{alert_id}", status_code=204, summary="Delete an alert")
async def delete_alert(
    alert_id: str,
    service: Annotated[AlertService, Depends(get_alert_service)],
) -> None:
    """Delete a price alert by ID."""
    if not service.delete_alert(alert_id):
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
