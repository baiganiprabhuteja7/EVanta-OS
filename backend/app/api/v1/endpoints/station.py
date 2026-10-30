from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_admin, get_db
from app.models.user import User
from app.schemas.setting import StationSettingResponse, StationSettingUpdate
from app.schemas.station import StationSummaryResponse
from app.services.station_service import StationService

router = APIRouter(tags=["Station Profile & Operations"])


@router.get("/station", response_model=StationSummaryResponse)
def get_station_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve Evanta OS single-station profile, live electrical KPIs, and connector status."""
    return StationService.get_station_summary(db)


@router.get("/station/settings", response_model=StationSettingResponse)
def get_station_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve Evanta station configuration, tariff, address, and demo settings."""
    return StationService.get_settings(db)


@router.patch("/station/settings", response_model=StationSettingResponse)
def update_station_settings(
    update_data: StationSettingUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update station configurable address, tariff, or refresh preferences (Administrator only)."""
    return StationService.update_settings(db, update_data.model_dump(exclude_unset=True))

