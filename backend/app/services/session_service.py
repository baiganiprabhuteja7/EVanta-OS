from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
import uuid
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.charger import Charger
from app.models.charging_session import ChargingSession
from app.models.payment import Payment
from app.models.station import Station
from app.models.user import User
from app.schemas.charging_session import SessionComplete, SessionCreate


class SessionService:
    @staticmethod
    def _enrich_session(session: ChargingSession, db: Session) -> dict:
        charger = db.scalar(select(Charger).where(Charger.id == session.charger_id))
        station = None
        if charger:
            station = db.scalar(select(Station).where(Station.id == charger.station_id))

        duration_min = round(session.duration_seconds / 60)

        return {
            "id": session.id,
            "session_code": session.session_code or f"SES-{session.id:04d}",
            "charger_id": session.charger_id,
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
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "station_code": station.station_code if station else "Unknown",
            "station_name": station.station_name if station else "Unknown Station",
            "charger_code": charger.charger_code if charger else "Unknown",
            "charger_type": charger.charger_type if charger else "AC",
        }

    @staticmethod
    def get_sessions(
        db: Session,
        station_id: Optional[str] = None,
        charger_type: Optional[str] = None,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[dict]:
        query = select(ChargingSession).order_by(ChargingSession.start_time.desc())

        if status_filter and status_filter != "All statuses":
            query = query.where(ChargingSession.status.ilike(status_filter))

        sessions = db.scalars(query).all()
        enriched = [SessionService._enrich_session(s, db) for s in sessions]

        if station_id and station_id != "All stations":
            enriched = [
                s for s in enriched
                if s["station_code"].lower() == station_id.lower() or s["station_name"].lower() == station_id.lower()
            ]

        if charger_type and charger_type != "All types":
            enriched = [s for s in enriched if s["charger_type"].lower() == charger_type.lower()]

        if search:
            s_low = search.strip().lower()
            enriched = [
                s for s in enriched
                if s_low in s["session_code"].lower()
                or s_low in s["station_name"].lower()
                or s_low in s["charger_code"].lower()
            ]

        if from_date:
            try:
                from_dt = datetime.fromisoformat(from_date).replace(tzinfo=timezone.utc)
                enriched = [s for s in enriched if s["start_time"] >= from_dt]
            except Exception:
                pass

        if to_date:
            try:
                to_dt = datetime.fromisoformat(to_date).replace(tzinfo=timezone.utc)
                enriched = [s for s in enriched if s["start_time"] <= to_dt]
            except Exception:
                pass

        return enriched[skip : skip + limit]

    @staticmethod
    def get_session_by_id_or_code(db: Session, identifier: str) -> Optional[ChargingSession]:
        if identifier.isdigit():
            session = db.scalar(select(ChargingSession).where(ChargingSession.id == int(identifier)))
            if session:
                return session
        return db.scalar(select(ChargingSession).where(ChargingSession.session_code == identifier.strip()))

    @staticmethod
    def start_session(
        db: Session,
        charger_identifier: str,
        user: Optional[User] = None,
        unit_price: Decimal = Decimal("22.0"),
    ) -> dict:
        # Find charger by integer ID or charger_code
        charger = None
        if charger_identifier.isdigit():
            charger = db.scalar(select(Charger).where(Charger.id == int(charger_identifier)))
        if not charger:
            charger = db.scalar(select(Charger).where(Charger.charger_code == charger_identifier.strip()))

        if not charger:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Charger '{charger_identifier}' not found.",
            )

        if charger.status.lower() != "available":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Charger '{charger.charger_code}' is currently {charger.status} and cannot start a session.",
            )

        station = db.scalar(select(Station).where(Station.id == charger.station_id))
        if station and station.status.lower() != "online":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Station '{station.station_name}' is currently {station.status}. Only Online stations can initiate sessions.",
            )

        # Generate unique session code
        session_code = f"SES-{charger.charger_code[-6:]}-{uuid.uuid4().hex[:4].upper()}"

        # Transition charger to Charging
        charger.status = "Charging"
        # Set realistic current based on rated power
        if charger.charger_type == "DC":
            charger.current_amp = Decimal(str(min(200.0, float(charger.rated_power_kw) * 2.0)))
        else:
            charger.current_amp = Decimal("32.0")

        new_session = ChargingSession(
            session_code=session_code,
            charger_id=charger.id,
            user_id=user.id if user else None,
            start_time=datetime.now(timezone.utc),
            status="Ongoing",
            unit_price=unit_price,
            energy_delivered_kwh=Decimal("0.0"),
            total_amount=Decimal("0.0"),
            duration_seconds=0,
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
                detail=f"Charging session '{identifier}' not found.",
            )

        if session.status.lower() == "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This charging session is already completed and cannot be completed again.",
            )

        end_time = datetime.now(timezone.utc)
        duration_sec = max(60, int((end_time - session.start_time).total_seconds()))

        # Determine energy delivered
        energy = Decimal("0.0")
        peak_power = None
        if complete_data:
            energy = complete_data.energy_delivered_kwh
            peak_power = complete_data.peak_power_kw
        else:
            # Default calculated simulation based on charger power and elapsed time
            charger = db.scalar(select(Charger).where(Charger.id == session.charger_id))
            if charger:
                hours = duration_sec / 3600.0
                energy = Decimal(str(round(float(charger.rated_power_kw) * hours * 0.85, 2)))
                peak_power = charger.rated_power_kw

        total_amt = round(energy * session.unit_price, 2)

        session.end_time = end_time
        session.duration_seconds = duration_sec
        session.energy_delivered_kwh = energy
        session.peak_power_kw = peak_power
        session.total_amount = total_amt
        session.status = "Completed"

        # Transition charger back to Available
        charger = db.scalar(select(Charger).where(Charger.id == session.charger_id))
        if charger:
            charger.status = "Available"
            charger.current_amp = Decimal("0.0")

        # Create simulated payment record
        payment = Payment(
            charging_session_id=session.id,
            amount=total_amt,
            currency="INR",
            payment_method="simulated_card",
            status="completed",
            transaction_reference=f"TXN-{uuid.uuid4().hex[:12].upper()}",
        )
        db.add(payment)

        db.commit()
        db.refresh(session)

        return SessionService._enrich_session(session, db)
