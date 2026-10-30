from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_admin, require_manager_or_admin, get_db
from app.models.user import User
from app.schemas.maintenance import MaintenanceRecordCreate, MaintenanceRecordResponse, MaintenanceRecordUpdate
from app.services.maintenance_service import MaintenanceService

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])


@router.get("", response_model=List[MaintenanceRecordResponse])
def get_maintenance_records(
    station_id: Optional[int] = Query(None, description="Filter by station ID"),
    charger_id: Optional[int] = Query(None, description="Filter by charger ID"),
    status: Optional[str] = Query(None, description="Filter by status (Reported, In Progress, Completed, etc.)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve equipment servicing and issue maintenance records."""
    return MaintenanceService.get_records(
        db=db,
        station_id=station_id,
        charger_id=charger_id,
        status_filter=status,
    )


@router.post("", response_model=MaintenanceRecordResponse, status_code=status.HTTP_201_CREATED)
def create_maintenance_record(
    record_in: MaintenanceRecordCreate,
    current_operator: User = Depends(require_manager_or_admin),
    db: Session = Depends(get_db),
):
    """Log an equipment maintenance issue or service task (Station Manager or Administrator)."""
    return MaintenanceService.create_record(
        db=db,
        data=record_in,
        user_id=current_operator.id,
    )


@router.get("/{record_id}", response_model=MaintenanceRecordResponse)
def get_maintenance_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve details for a single maintenance record."""
    return MaintenanceService.get_record(db=db, record_id=record_id)


@router.patch("/{record_id}", response_model=MaintenanceRecordResponse)
def update_maintenance_record(
    record_id: int,
    record_update: MaintenanceRecordUpdate,
    current_operator: User = Depends(require_manager_or_admin),
    db: Session = Depends(get_db),
):
    """Update maintenance task progress, technician notes, or mark as completed (Station Manager or Administrator)."""
    return MaintenanceService.update_record(db=db, record_id=record_id, data=record_update)


@router.delete("/{record_id}")
def delete_maintenance_record(
    record_id: int,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete a maintenance record (Administrator only)."""
    return MaintenanceService.delete_record(db=db, record_id=record_id)
