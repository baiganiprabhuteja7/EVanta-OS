from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_admin, get_db
from app.models.user import User
from app.schemas.setting import StationSettingResponse, StationSettingUpdate
from app.services.station_service import StationService

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=StationSettingResponse)
def get_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve station settings, tariff, address, and demo configuration."""
    return StationService.get_settings(db)


@router.put("", response_model=StationSettingResponse)
@router.patch("", response_model=StationSettingResponse)
def update_settings(
    update_in: StationSettingUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update station settings, tariff, and address (Administrator only)."""
    return StationService.update_settings(db, update_in.model_dump(exclude_unset=True))
