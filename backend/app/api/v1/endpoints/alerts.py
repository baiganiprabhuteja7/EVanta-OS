from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_manager_or_admin, get_db
from app.models.user import User
from app.schemas.alert import AlertResponse
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["Station Alerts"])


@router.get("", response_model=List[AlertResponse])
def get_alerts(
    active_only: bool = Query(False, description="Filter for active alerts only"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve operational alerts and safety notices for the station."""
    return AlertService.get_alerts(db, active_only=active_only)


@router.post("/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    current_operator: User = Depends(require_manager_or_admin),
    db: Session = Depends(get_db),
):
    """Acknowledge and mark an operational alert as resolved (Station Manager or Administrator)."""
    return AlertService.resolve_alert(db, alert_id)
