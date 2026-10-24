from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.charger import Charger
from app.models.charging_session import ChargingSession
from app.models.station import Station
from app.models.user import User
from app.schemas.station import StationCreate, StationResponse, StationUpdate

CHARGER_PROFILES = [
    {"type": "AC", "connector": "Type 2", "power": 7.4, "voltage": 230.0, "current": 32.0},
    {"type": "AC", "connector": "Type 2", "power": 22.0, "voltage": 400.0, "current": 34.0},
    {"type": "DC", "connector": "CCS2", "power": 60.0, "voltage": 500.0, "current": 120.0},
    {"type": "DC", "connector": "CCS2", "power": 120.0, "voltage": 650.0, "current": 185.0},
    {"type": "DC", "connector": "CHAdeMO", "power": 50.0, "voltage": 400.0, "current": 125.0},
]


class StationService:
    @staticmethod
    def _enrich_station(station: Station, db: Session) -> dict:
        """Calculate live aggregated metrics for a station."""
        chargers = db.scalars(select(Charger).where(Charger.station_id == station.id)).all()
        total_chargers = len(chargers)
        active_chargers = sum(1 for c in chargers if c.status.lower() == "charging")

        # Sum energy delivered and today's revenue from charging sessions
        charger_ids = [c.id for c in chargers]
        energy_delivered = 0.0
        todays_revenue = 0.0

        if charger_ids:
            now = datetime.now(timezone.utc)
            start_of_day = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

            energy_sum = db.scalar(
                select(func.sum(ChargingSession.energy_delivered_kwh)).where(
                    ChargingSession.charger_id.in_(charger_ids)
                )
            )
            if energy_sum:
                energy_delivered = float(energy_sum)

            rev_sum = db.scalar(
                select(func.sum(ChargingSession.total_amount)).where(
                    ChargingSession.charger_id.in_(charger_ids),
                    ChargingSession.start_time >= start_of_day,
                )
            )
            if rev_sum:
                todays_revenue = float(rev_sum)

        utilization = 0
        if total_chargers > 0:
            utilization = round((active_chargers / total_chargers) * 100)
            if station.status.lower() != "online" and active_chargers == 0:
                utilization = 0

        location_str = ""
        if station.city and station.state:
            location_str = f"{station.city}, {station.state}"
        elif station.city:
            location_str = station.city
        elif station.address:
            location_str = station.address

        return {
            "id": station.id,
            "station_code": station.station_code,
            "station_name": station.station_name,
            "description": station.description,
            "address": station.address,
            "city": station.city,
            "state": station.state,
            "postal_code": station.postal_code,
            "latitude": float(station.latitude) if station.latitude is not None else None,
            "longitude": float(station.longitude) if station.longitude is not None else None,
            "status": station.status,
            "created_by": station.created_by,
            "created_at": station.created_at,
            "updated_at": station.updated_at,
            "location": location_str,
            "chargers": total_chargers,
            "active_chargers": active_chargers,
            "energy_delivered": energy_delivered,
            "todays_revenue": todays_revenue,
            "utilization": utilization,
        }

    @staticmethod
    def get_stations(
        db: Session,
        search: Optional[str] = None,
        status_filter: Optional[str] = None,
        sort_by: str = "name",
        direction: str = "asc",
        skip: int = 0,
        limit: int = 100,
    ) -> List[dict]:
        query = select(Station)

        if search:
            search_term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Station.station_name.ilike(search_term),
                    Station.station_code.ilike(search_term),
                    Station.city.ilike(search_term),
                    Station.state.ilike(search_term),
                    Station.address.ilike(search_term),
                )
            )

        if status_filter and status_filter != "All statuses":
            query = query.where(Station.status.ilike(status_filter))

        stations = db.scalars(query).all()
        enriched = [StationService._enrich_station(s, db) for s in stations]

        # In-memory sorting for computed properties
        reverse = direction.lower() == "desc"
        if sort_by == "energyDelivered" or sort_by == "energy_delivered":
            enriched.sort(key=lambda s: s["energy_delivered"], reverse=reverse)
        elif sort_by == "todaysRevenue" or sort_by == "todays_revenue":
            enriched.sort(key=lambda s: s["todays_revenue"], reverse=reverse)
        elif sort_by == "utilization":
            enriched.sort(key=lambda s: s["utilization"], reverse=reverse)
        else:
            enriched.sort(key=lambda s: s["station_name"].lower(), reverse=reverse)

        return enriched[skip : skip + limit]

    @staticmethod
    def get_station_by_id_or_code(db: Session, identifier: str) -> Optional[Station]:
        if identifier.isdigit():
            station = db.scalar(select(Station).where(Station.id == int(identifier)))
            if station:
                return station
        return db.scalar(select(Station).where(Station.station_code == identifier.strip()))

    @staticmethod
    def create_station(
        db: Session, data: StationCreate, current_user: Optional[User] = None
    ) -> dict:
        code = data.station_code.strip().upper()
        existing = db.scalar(select(Station).where(Station.station_code == code))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A station with code '{code}' already exists.",
            )

        city = data.city
        state = data.state
        if not city and data.address and "," in data.address:
            parts = [p.strip() for p in data.address.split(",")]
            if len(parts) >= 2:
                city = parts[-2]
                state = parts[-1]

        station = Station(
            station_code=code,
            station_name=data.station_name.strip(),
            description=data.description,
            address=data.address,
            city=city,
            state=state,
            postal_code=data.postal_code,
            latitude=data.latitude,
            longitude=data.longitude,
            status=data.status or "Online",
            created_by=current_user.id if current_user else None,
        )
        db.add(station)
        db.flush()

        # Generate initial chargers if requested
        chargers_to_add = data.chargers_count or 0
        prefix = code.replace("EV-", "CH-")
        for i in range(1, chargers_to_add + 1):
            profile = CHARGER_PROFILES[(i - 1 + len(code)) % len(CHARGER_PROFILES)]
            status_val = "Available" if station.status == "Online" else "Offline"
            charger = Charger(
                station_id=station.id,
                charger_code=f"{prefix}-{str(i).zfill(2)}",
                charger_type=profile["type"],
                connector_type=profile["connector"],
                rated_power_kw=Decimal(str(profile["power"])),
                voltage=Decimal(str(profile["voltage"])),
                current_amp=Decimal("0.0"),
                power_factor=Decimal("0.94"),
                status=status_val,
            )
            db.add(charger)

        db.commit()
        db.refresh(station)
        return StationService._enrich_station(station, db)

    @staticmethod
    def update_station(
        db: Session, identifier: str, data: StationUpdate
    ) -> dict:
        station = StationService.get_station_by_id_or_code(db, identifier)
        if not station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Station '{identifier}' not found.",
            )

        if data.station_name is not None:
            station.station_name = data.station_name.strip()
        if data.description is not None:
            station.description = data.description
        if data.address is not None:
            station.address = data.address
        if data.city is not None:
            station.city = data.city
        if data.state is not None:
            station.state = data.state
        if data.postal_code is not None:
            station.postal_code = data.postal_code
        if data.latitude is not None:
            station.latitude = data.latitude
        if data.longitude is not None:
            station.longitude = data.longitude
        if data.status is not None:
            station.status = data.status

        # Synchronize charger statuses if station goes offline or faulted
        if data.status in ["Offline", "offline"]:
            chargers = db.scalars(select(Charger).where(Charger.station_id == station.id)).all()
            for ch in chargers:
                ch.status = "Offline"
                ch.current_amp = Decimal("0.0")

        # Handle chargers count expansion or reduction if specified
        if data.chargers_count is not None:
            current_chargers = db.scalars(
                select(Charger).where(Charger.station_id == station.id).order_by(Charger.id)
            ).all()
            diff = data.chargers_count - len(current_chargers)
            if diff > 0:
                prefix = station.station_code.replace("EV-", "CH-")
                start_idx = len(current_chargers) + 1
                for i in range(start_idx, start_idx + diff):
                    profile = CHARGER_PROFILES[(i - 1 + len(station.station_code)) % len(CHARGER_PROFILES)]
                    charger = Charger(
                        station_id=station.id,
                        charger_code=f"{prefix}-{str(i).zfill(2)}",
                        charger_type=profile["type"],
                        connector_type=profile["connector"],
                        rated_power_kw=Decimal(str(profile["power"])),
                        voltage=Decimal(str(profile["voltage"])),
                        current_amp=Decimal("0.0"),
                        power_factor=Decimal("0.94"),
                        status="Available" if station.status == "Online" else "Offline",
                    )
                    db.add(charger)
            elif diff < 0:
                # Remove from the end, ensuring not charging
                for ch in reversed(current_chargers[data.chargers_count:]):
                    if ch.status.lower() == "charging":
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Charger '{ch.charger_code}' is actively charging and cannot be removed.",
                        )
                    db.delete(ch)

        db.commit()
        db.refresh(station)
        return StationService._enrich_station(station, db)

    @staticmethod
    def delete_station(db: Session, identifier: str) -> bool:
        station = StationService.get_station_by_id_or_code(db, identifier)
        if not station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Station '{identifier}' not found.",
            )
        db.delete(station)
        db.commit()
        return True
