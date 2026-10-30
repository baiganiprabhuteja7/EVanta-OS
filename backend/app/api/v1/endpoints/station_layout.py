from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_admin
from app.models.user import User
from app.schemas.station_layout import StationLayoutResponse, StationLayoutUpdate
from app.services.station_layout_service import StationLayoutService
from app.services.station_service import StationService

router = APIRouter(prefix="/station/layout", tags=["Virtual Station Layout (Admin Only)"])


@router.get("", response_model=StationLayoutResponse)
def get_station_layout(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Retrieve the 2D/3D engineering station layout for the Hyderabad facility.
    Strictly restricted to authorized Station Administrators.
    """
    station = StationService.get_prabhus_grid_station(db)
    return StationLayoutService.get_or_create_layout(db, station.id, is_demo=False)


@router.put("", response_model=StationLayoutResponse)
def update_station_layout(
    payload: StationLayoutUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Save customized 2D/3D station floor plan with optimistic concurrency control.
    Strictly restricted to authorized Station Administrators.
    """
    station = StationService.get_prabhus_grid_station(db)
    return StationLayoutService.update_layout(
        db,
        station_id=station.id,
        payload=payload,
        user_id=current_admin.id,
        is_demo=False,
    )


@router.post("/reset", response_model=StationLayoutResponse)
def reset_station_layout(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Reset station floor plan back to the canonical illustrative sample layout.
    Strictly restricted to authorized Station Administrators.
    """
    station = StationService.get_prabhus_grid_station(db)
    return StationLayoutService.reset_layout(
        db,
        station_id=station.id,
        user_id=current_admin.id,
        is_demo=False,
    )
