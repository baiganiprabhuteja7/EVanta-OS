from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.charger import Charger
from app.models.charging_session import ChargingSession
from app.models.meter_reading import MeterReading
from app.models.payment import Payment
from app.models.setting import StationSetting
from app.models.station import Station
from app.schemas.charging_session import SessionComplete, SessionCreate


class SessionService:
    @staticmethod
    def _enrich_session(session: ChargingSession, db: Session) -> dict:
        charger = db.scalar(select(Charger).where(Charger.id == session.charger_id))
        station = db.scalar(select(Station).where(Station.id == charger.station_id)) if charger else None
        duration_min = max(1, round(session.duration_seconds / 60))

        return {
            "id": session.id,
            "session_code": session.session_code or f"SES-PG-{session.id:04d}",
            "station_id": station.id if station else None,
            "station_name": station.station_name if station else "Evanta Station",
            "charger_id": session.charger_id,
            "charger_code": charger.charger_code if charger else "Unknown",
            "charger_type": charger.charger_type if charger else "AC",
            "connector_type": charger.connector_type if charger else "Type 2",
            "user_id": session.user_id,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "energy_delivered_kwh": float(session.energy_delivered_kwh),
            "peak_power_kw": float(session.peak_power_kw) if session.peak_power_kw is not None else None,
            "duration_seconds": session.duration_seconds,
            "duration_minutes": duration_min,
            "status": session.status,
            "unit_price": float(session.unit_price),
            "total_amount": float(session.total_amount),
            "data_source": settings.DATA_SOURCE_LABEL,
            "disclaimer": "SIMULATED SESSION RECORD",
            "created_at": session.created_at,
            "updated_at": session.updated_at,
        }

    @staticmethod
    def get_sessions(
        db: Session,
        station_id: Optional[int] = None,
        charger_type: Optional[str] = None,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[dict]:
        query = select(ChargingSession).join(Charger, ChargingSession.charger_id == Charger.id).order_by(ChargingSession.start_time.desc())

        if station_id:
            query = query.where(Charger.station_id == station_id)

        if status_filter and status_filter.lower() not in ["all statuses", "all"]:
            query = query.where(ChargingSession.status.ilike(status_filter))

        sessions = db.scalars(query).all()
        enriched = [SessionService._enrich_session(s, db) for s in sessions]

        if charger_type and charger_type.lower() not in ["all types", "all"]:
            enriched = [s for s in enriched if s["charger_type"].lower() == charger_type.lower()]

        if search:
            s_low = search.strip().lower()
            enriched = [
                s for s in enriched
                if s_low in s["session_code"].lower()
                or s_low in s["charger_code"].lower()
                or (s.get("station_name") and s_low in s["station_name"].lower())
            ]

        return enriched[skip : skip + limit]

    @staticmethod
    def get_session_by_id_or_code(db: Session, identifier: str) -> Optional[ChargingSession]:
        query = select(ChargingSession)
        if str(identifier).isdigit():
            session = db.scalar(query.where(ChargingSession.id == int(identifier)))
            if session:
                return session

        return db.scalar(query.where(ChargingSession.session_code == str(identifier).strip()))

    @staticmethod
    def start_session(
        db: Session,
        charger_id_or_code: str,
        unit_price: Optional[Decimal] = None,
        user_id: Optional[int] = None,
    ) -> dict:
        # Find charger across stations or by ID
        charger = None
        if str(charger_id_or_code).isdigit():
            charger = db.scalar(select(Charger).where(Charger.id == int(charger_id_or_code)))
        if not charger:
            charger = db.scalar(select(Charger).where(Charger.charger_code == str(charger_id_or_code).strip()))

        if not charger:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Charger '{charger_id_or_code}' not found.",
            )

        if charger.status.lower() != "available":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Charger '{charger.charger_code}' is currently '{charger.status}'. Only Available chargers can start sessions.",
            )

        # Get station tariff if not passed
        station = db.scalar(select(Station).where(Station.id == charger.station_id))
        if unit_price is None or float(unit_price) <= 0:
            setting = db.scalar(select(StationSetting).where(StationSetting.station_id == charger.station_id)) if station else None
            unit_price = setting.tariff_per_kwh if setting else Decimal(str(settings.DEFAULT_TARIFF))

        # Transition charger to Charging
        charger.status = "Charging"
        if charger.charger_type == "DC":
            charger.current_amp = Decimal(str(min(180.0, float(charger.rated_power_kw) * 1.8)))
        else:
            charger.current_amp = Decimal("32.0")

        now = datetime.now(timezone.utc)
        clean_code = charger.charger_code[-3:].replace("-", "")
        session_code = f"SES-{clean_code}-{uuid.uuid4().hex[:4].upper()}"

        new_session = ChargingSession(
            session_code=session_code,
            charger_id=charger.id,
            user_id=user_id,
            start_time=now,
            status="Ongoing",
            unit_price=unit_price,
            energy_delivered_kwh=Decimal("0.0"),
            total_amount=Decimal("0.0"),
            duration_seconds=0,
            data_source=settings.DATA_SOURCE_LABEL,
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)

        return SessionService._enrich_session(new_session, db)

    @staticmethod
    def complete_session(
        db: Session,
        identifier: str,
        complete_data: Optional[SessionComplete] = None,
    ) -> dict:
        session = SessionService.get_session_by_id_or_code(db, identifier)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{identifier}' not found.",
            )

        if session.status.lower() == "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Charging session is already completed.",
            )

        now = datetime.now(timezone.utc)
        duration_sec = max(60, int((now - session.start_time).total_seconds()))

        charger = db.scalar(select(Charger).where(Charger.id == session.charger_id))
        energy = Decimal("0.0")
        peak_power = None

        if complete_data and complete_data.energy_delivered_kwh is not None and float(complete_data.energy_delivered_kwh) > 0:
            energy = complete_data.energy_delivered_kwh
            peak_power = complete_data.peak_power_kw or (charger.rated_power_kw if charger else Decimal("22.0"))
        else:
            if charger:
                hours = duration_sec / 3600.0
                power_eff = float(charger.rated_power_kw) * 0.85
                energy = Decimal(str(round(power_eff * max(0.25, hours), 2)))
                peak_power = charger.rated_power_kw
            else:
                energy = Decimal("14.5")
                peak_power = Decimal("22.0")

        # Business calculation: Charging revenue = Energy delivered × Applicable charging tariff
        total_amt = round(energy * Decimal(str(session.unit_price)), 2)

        session.end_time = now
        session.duration_seconds = duration_sec
        session.energy_delivered_kwh = energy
        session.peak_power_kw = peak_power
        session.total_amount = total_amt
        session.status = "Completed"

        # Update charger total energy and return to Available
        if charger:
            charger.status = "Available"
            charger.current_amp = Decimal("0.0")
            charger.energy_delivered_kwh = Decimal(str(round(float(charger.energy_delivered_kwh or 0) + float(energy), 2)))

        # Create meter reading record
        meter_reading = MeterReading(
            charger_id=session.charger_id,
            timestamp=now,
            power_kw=Decimal(str(float(peak_power or 0))),
            energy_kwh=energy,
            voltage_v=charger.voltage if charger else Decimal("230.0"),
            current_a=charger.current_amp if charger else Decimal("0.0"),
            power_factor=charger.power_factor if charger else Decimal("0.94"),
            data_source=settings.DATA_SOURCE_LABEL,
        )
        db.add(meter_reading)

        # Record payment
        payment = Payment(
            charging_session_id=session.id,
            amount=total_amt,
            currency="INR",
            payment_method="simulated_upi",
            status="completed",
            transaction_reference=f"TXN-EV-{uuid.uuid4().hex[:8].upper()}",
            created_at=now,
        )
        db.add(payment)

        db.commit()
        db.refresh(session)
        return SessionService._enrich_session(session, db)
