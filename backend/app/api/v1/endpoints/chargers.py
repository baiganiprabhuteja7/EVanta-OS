from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models.charger import Charger
from app.models.charging_session import ChargingSession
from app.models.station import Station
from app.schemas.charger import ChargerCreate, ChargerResponse, ChargerUpdate
from app.services.station_service import StationService

router = APIRouter(tags=["Chargers"])


def _charger_to_response(charger: Charger, db: Session) -> ChargerResponse:
    station = db.scalar(select(Station).where(Station.id == charger.station_id))

    # Check active session if any
    active_session = db.scalar(
        select(ChargingSession)
        .where(ChargingSession.charger_id == charger.id, ChargingSession.status == "Ongoing")
        .order_by(ChargingSession.id.desc())
    )

    return ChargerResponse(
        id=charger.id,
        station_id=charger.station_id,
        charger_code=charger.charger_code,
        charger_type=charger.charger_type,
        connector_type=charger.connector_type,
        rated_power_kw=float(charger.rated_power_kw),
        voltage=float(charger.voltage) if charger.voltage is not None else 230.0,
        current_amp=float(charger.current_amp) if charger.current_amp is not None else 0.0,
        power_factor=float(charger.power_factor) if charger.power_factor is not None else 0.94,
        status=charger.status,
        created_at=charger.created_at,
        updated_at=charger.updated_at,
        station_code=station.station_code if station else "Unknown",
        current_session=active_session.session_code if active_session else None,
    )


@router.get("/chargers", response_model=List[ChargerResponse])
def list_chargers(
    station_id: Optional[str] = Query(None, description="Station ID or Station Code"),
    charger_type: Optional[str] = Query(None, description="Charger type: AC or DC"),
    status: Optional[str] = Query(None, description="Operational status"),
    search: Optional[str] = Query(None, description="Search by charger code"),
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """List all chargers with optional filtering."""
    query = select(Charger)

    if station_id and station_id != "All stations":
        st = StationService.get_station_by_id_or_code(db, station_id)
        if st:
            query = query.where(Charger.station_id == st.id)

    if charger_type and charger_type != "All types":
        query = query.where(Charger.charger_type.ilike(charger_type))

    if status and status != "All statuses":
        query = query.where(Charger.status.ilike(status))

    if search:
        query = query.where(Charger.charger_code.ilike(f"%{search.strip()}%"))

    chargers = db.scalars(query.order_by(Charger.id).offset(skip).limit(limit)).all()
    return [_charger_to_response(ch, db) for ch in chargers]


@router.post("/stations/{station_id}/chargers", response_model=ChargerResponse, status_code=status.HTTP_201_CREATED)
def create_charger_for_station(
    station_id: str,
    charger_in: ChargerCreate,
    db: Session = Depends(get_db),
):
    """Add a new charger to a specific station."""
    station = StationService.get_station_by_id_or_code(db, station_id)
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station '{station_id}' not found.",
        )

    # Check for duplicate charger_code in this station
    existing = db.scalar(
        select(Charger).where(
            Charger.station_id == station.id,
            Charger.charger_code == charger_in.charger_code.strip(),
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A charger with code '{charger_in.charger_code}' already exists in this station.",
        )

    charger = Charger(
        station_id=station.id,
        charger_code=charger_in.charger_code.strip(),
        charger_type=charger_in.charger_type,
        connector_type=charger_in.connector_type,
        rated_power_kw=charger_in.rated_power_kw,
        voltage=charger_in.voltage or Decimal("230.0"),
        current_amp=charger_in.current_amp or Decimal("0.0"),
        power_factor=charger_in.power_factor or Decimal("0.94"),
        status=charger_in.status or "Available",
    )
    db.add(charger)
    db.commit()
    db.refresh(charger)
    return _charger_to_response(charger, db)


@router.get("/stations/{station_id}/chargers", response_model=List[ChargerResponse])
def get_chargers_for_station(station_id: str, db: Session = Depends(get_db)):
    """Retrieve all chargers for a specific station."""
    station = StationService.get_station_by_id_or_code(db, station_id)
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station '{station_id}' not found.",
        )

    chargers = db.scalars(
        select(Charger).where(Charger.station_id == station.id).order_by(Charger.id)
    ).all()
    return [_charger_to_response(ch, db) for ch in chargers]


@router.get("/chargers/{charger_id}", response_model=ChargerResponse)
def get_charger(charger_id: str, db: Session = Depends(get_db)):
    """Retrieve a charger by numeric ID or charger code."""
    charger = None
    if charger_id.isdigit():
        charger = db.scalar(select(Charger).where(Charger.id == int(charger_id)))
    if not charger:
        charger = db.scalar(select(Charger).where(Charger.charger_code == charger_id.strip()))

    if not charger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Charger '{charger_id}' not found.",
        )
    return _charger_to_response(charger, db)


@router.patch("/chargers/{charger_id}", response_model=ChargerResponse)
def update_charger(
    charger_id: str,
    update_in: ChargerUpdate,
    db: Session = Depends(get_db),
):
    """Update charger electrical parameters or operational status."""
    charger = None
    if charger_id.isdigit():
        charger = db.scalar(select(Charger).where(Charger.id == int(charger_id)))
    if not charger:
        charger = db.scalar(select(Charger).where(Charger.charger_code == charger_id.strip()))

    if not charger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Charger '{charger_id}' not found.",
        )

    if update_in.charger_code is not None:
        charger.charger_code = update_in.charger_code.strip()
    if update_in.charger_type is not None:
        charger.charger_type = update_in.charger_type
    if update_in.connector_type is not None:
        charger.connector_type = update_in.connector_type
    if update_in.rated_power_kw is not None:
        charger.rated_power_kw = update_in.rated_power_kw
    if update_in.voltage is not None:
        charger.voltage = update_in.voltage
    if update_in.current_amp is not None:
        charger.current_amp = update_in.current_amp
    if update_in.power_factor is not None:
        charger.power_factor = update_in.power_factor
    if update_in.status is not None:
        charger.status = update_in.status
        if update_in.status.lower() != "charging":
            charger.current_amp = Decimal("0.0")

    db.commit()
    db.refresh(charger)
    return _charger_to_response(charger, db)


@router.delete("/chargers/{charger_id}")
def delete_charger(charger_id: str, db: Session = Depends(get_db)):
    """Delete a charger."""
    charger = None
    if charger_id.isdigit():
        charger = db.scalar(select(Charger).where(Charger.id == int(charger_id)))
    if not charger:
        charger = db.scalar(select(Charger).where(Charger.charger_code == charger_id.strip()))

    if not charger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Charger '{charger_id}' not found.",
        )

    if charger.status.lower() == "charging":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete an actively charging charger.",
        )

    db.delete(charger)
    db.commit()
    return {"message": f"Charger '{charger_id}' successfully deleted.", "status": "ok"}
