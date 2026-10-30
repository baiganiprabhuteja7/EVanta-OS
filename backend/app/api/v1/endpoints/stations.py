from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_admin, get_db
from app.models.user import User
from app.schemas.station import StationCreate, StationSummaryResponse, StationUpdate
from app.services.station_service import StationService

router = APIRouter(prefix="/stations", tags=["Stations"])


@router.get("", response_model=List[StationSummaryResponse])
def get_stations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve full station registry with real-time operational and financial KPIs."""
    return StationService.get_all_stations(db)


@router.post("", response_model=StationSummaryResponse, status_code=status.HTTP_201_CREATED)
def create_station(
    station_in: StationCreate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Register a new EV charging station site (Administrator only)."""
    return StationService.create_station(db=db, data=station_in, user_id=current_admin.id)


@router.get("/{station_id}", response_model=StationSummaryResponse)
def get_station(
    station_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve station details and live performance metrics."""
    return StationService.get_station_summary(db, station_id)


@router.patch("/{station_id}", response_model=StationSummaryResponse)
def update_station(
    station_id: str,
    station_update: StationUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update station configuration, address, or investment amounts (Administrator only)."""
    return StationService.update_station(db=db, identifier=station_id, data=station_update)


@router.delete("/{station_id}")
def delete_station(
    station_id: str,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete a station with relationship and ongoing session safeguards (Administrator only)."""
    return StationService.delete_station(db=db, identifier=station_id)
