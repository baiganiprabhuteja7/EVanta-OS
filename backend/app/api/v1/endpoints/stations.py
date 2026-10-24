from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user_optional, get_db
from app.models.charger import Charger
from app.models.user import User
from app.schemas.charger import ChargerResponse
from app.schemas.station import StationCreate, StationDetailResponse, StationResponse, StationUpdate
from app.services.station_service import StationService

router = APIRouter(prefix="/stations", tags=["Stations"])


@router.get("", response_model=List[StationResponse])
def get_stations(
    search: Optional[str] = Query(None, description="Search term for name, code, or location"),
    status: Optional[str] = Query(None, description="Filter by operational status"),
    sort: str = Query("name", description="Field to sort by: name, energyDelivered, todaysRevenue, utilization"),
    direction: str = Query("asc", description="Sort direction: asc or desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Retrieve charging stations with searching, filtering, and live computed KPIs."""
    return StationService.get_stations(
        db=db,
        search=search,
        status_filter=status,
        sort_by=sort,
        direction=direction,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=StationResponse, status_code=status.HTTP_201_CREATED)
def create_station(
    station_in: StationCreate,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Create a new charging station with optional initial chargers."""
    return StationService.create_station(db=db, data=station_in, current_user=current_user)


@router.get("/{station_id}", response_model=StationDetailResponse)
def get_station(station_id: str, db: Session = Depends(get_db)):
    """Retrieve station details by numeric ID or station code (e.g., 'EV-BLR-001')."""
    station = StationService.get_station_by_id_or_code(db, station_id)
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station '{station_id}' not found.",
        )

    enriched = StationService._enrich_station(station, db)
    chargers = db.scalars(
        select(Charger).where(Charger.station_id == station.id).order_by(Charger.id)
    ).all()

    charger_responses = []
    for ch in chargers:
        charger_responses.append(
            ChargerResponse(
                id=ch.id,
                station_id=ch.station_id,
                charger_code=ch.charger_code,
                charger_type=ch.charger_type,
                connector_type=ch.connector_type,
                rated_power_kw=float(ch.rated_power_kw),
                voltage=float(ch.voltage) if ch.voltage is not None else 230.0,
                current_amp=float(ch.current_amp) if ch.current_amp is not None else 0.0,
                power_factor=float(ch.power_factor) if ch.power_factor is not None else 0.94,
                status=ch.status,
                created_at=ch.created_at,
                updated_at=ch.updated_at,
                station_code=station.station_code,
            )
        )

    return StationDetailResponse(**enriched, charger_list=charger_responses)


@router.patch("/{station_id}", response_model=StationResponse)
def update_station(
    station_id: str,
    station_update: StationUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing charging station's attributes and status."""
    return StationService.update_station(db=db, identifier=station_id, data=station_update)


@router.delete("/{station_id}")
def delete_station(
    station_id: str,
    db: Session = Depends(get_db),
):
    """Delete a station and its assigned equipment."""
    StationService.delete_station(db=db, identifier=station_id)
    return {"message": f"Station '{station_id}' successfully deleted.", "status": "ok"}
