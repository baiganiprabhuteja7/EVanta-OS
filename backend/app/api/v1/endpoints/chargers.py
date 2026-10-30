from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_admin, get_db
from app.models.user import User
from app.schemas.charger import ChargerCreate, ChargerResponse, ChargerUpdate
from app.services.charger_service import ChargerService

router = APIRouter(prefix="/chargers", tags=["Chargers"])


@router.get("", response_model=List[ChargerResponse])
def get_chargers(
    station_id: Optional[int] = Query(None, description="Filter by station ID"),
    type: Optional[str] = Query(None, description="Filter by AC or DC"),
    status: Optional[str] = Query(None, description="Filter by status (Available, Charging, Offline, Faulted)"),
    search: Optional[str] = Query(None, description="Search by code, connector type or location"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve all configured AC and DC chargers with live telemetry and revenue."""
    return ChargerService.get_chargers(
        db=db,
        station_id=station_id,
        charger_type=type,
        status_filter=status,
        search=search,
    )


@router.post("", response_model=ChargerResponse, status_code=status.HTTP_201_CREATED)
def create_charger(
    charger_in: ChargerCreate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Add a new configurable charger to a station (Administrator only)."""
    return ChargerService.create_charger(db=db, data=charger_in)


@router.get("/{charger_id}", response_model=ChargerResponse)
def get_charger(
    charger_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve details, live telemetry, and financial performance for a single charger."""
    charger = ChargerService.get_charger_by_id_or_code(db, charger_id)
    if not charger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Charger '{charger_id}' not found.",
        )
    return ChargerService._enrich_charger(charger, db)


@router.patch("/{charger_id}", response_model=ChargerResponse)
def update_charger(
    charger_id: str,
    charger_update: ChargerUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update charger power rating, connector type, location, or status (Administrator only)."""
    return ChargerService.update_charger(db=db, identifier=charger_id, data=charger_update)


@router.delete("/{charger_id}")
def delete_charger(
    charger_id: str,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Remove a charger from a station with ongoing session safeguards (Administrator only)."""
    return ChargerService.delete_charger(db=db, identifier=charger_id)
