from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.charger import Charger
from app.models.charging_session import ChargingSession
from app.models.meter_reading import MeterReading
from app.models.setting import StationSetting
from app.models.station import Station
from app.schemas.charger import ChargerCreate, ChargerUpdate


class ChargerService:
    @staticmethod
    def _enrich_charger(charger: Charger, db: Session) -> dict:
        # Check active session
        active_sess = db.scalar(
            select(ChargingSession)
            .where(ChargingSession.charger_id == charger.id)
            .where(ChargingSession.status == "Ongoing")
            .order_by(ChargingSession.start_time.desc())
        )

        # Get station for electricity rate and tariff
        station = db.scalar(select(Station).where(Station.id == charger.station_id))
        station_name = station.station_name if station else "Evanta Station"
        setting = db.scalar(select(StationSetting).where(StationSetting.station_id == charger.station_id)) if station else None
        elec_rate = float(setting.electricity_cost_per_kwh) if setting else 8.5
        tariff = float(setting.tariff_per_kwh) if setting else 18.5

        # Calculate current power in kW
        current_power_kw = 0.0
        if charger.status.lower() == "charging":
            if charger.charger_type == "DC":
                calc_kw = (float(charger.voltage or 500) * float(charger.current_amp or 0)) / 1000.0
            else:
                calc_kw = (
                    float(charger.voltage or 230)
                    * float(charger.current_amp or 0)
                    * float(charger.power_factor or 0.94)
                ) / 1000.0
            current_power_kw = min(float(charger.rated_power_kw), max(0.0, calc_kw))

        # Latest telemetry reading timestamp
        latest_reading = db.scalar(
            select(MeterReading.timestamp)
            .where(MeterReading.charger_id == charger.id)
            .order_by(MeterReading.timestamp.desc())
            .limit(1)
        )

        # Charger-level historical sessions & revenue calculations
        sessions = db.scalars(
            select(ChargingSession).where(ChargingSession.charger_id == charger.id)
        ).all()

        total_sessions_count = len(sessions)
        session_energy = sum(float(s.energy_delivered_kwh) for s in sessions)
        energy_delivered = max(float(charger.energy_delivered_kwh or 0), session_energy)

        total_revenue = sum(
            float(s.total_amount) if float(s.total_amount) > 0 else (float(s.energy_delivered_kwh) * float(s.unit_price or tariff))
            for s in sessions
        )
        total_revenue = round(total_revenue, 2)
        total_electricity_expense = round(energy_delivered * elec_rate, 2)
        operating_profit = round(total_revenue - total_electricity_expense, 2)

        return {
            "id": charger.id,
            "station_id": charger.station_id,
            "station_name": station_name,
            "charger_code": charger.charger_code,
            "charger_type": charger.charger_type,
            "connector_type": charger.connector_type,
            "rated_power_kw": float(charger.rated_power_kw),
            "voltage": float(charger.voltage) if charger.voltage is not None else 230.0,
            "current_amp": float(charger.current_amp) if charger.current_amp is not None else 0.0,
            "power_factor": float(charger.power_factor) if charger.power_factor is not None else 0.94,
            "current_power_kw": round(current_power_kw, 2),
            "energy_delivered_kwh": round(energy_delivered, 2),
            "total_sessions_count": total_sessions_count,
            "total_revenue": total_revenue,
            "total_electricity_expense": total_electricity_expense,
            "operating_profit": operating_profit,
            "status": charger.status,
            "location_name": charger.location_name or "Main Canopy",
            "current_session": active_sess.session_code if active_sess else None,
            "data_source": settings.DATA_SOURCE_LABEL,
            "disclaimer": "SIMULATED READING — NOT MEASURED PHYSICAL HARDWARE",
            "latest_reading_time": latest_reading or charger.updated_at,
            "created_at": charger.created_at,
            "updated_at": charger.updated_at,
        }

    @staticmethod
    def get_chargers(
        db: Session,
        station_id: Optional[int] = None,
        charger_type: Optional[str] = None,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[dict]:
        query = select(Charger).order_by(Charger.charger_code)

        if station_id:
            query = query.where(Charger.station_id == station_id)

        if charger_type and charger_type.lower() not in ["all types", "all"]:
            query = query.where(Charger.charger_type.ilike(charger_type))

        if status_filter and status_filter.lower() not in ["all statuses", "all"]:
            query = query.where(Charger.status.ilike(status_filter))

        chargers = db.scalars(query).all()
        enriched = [ChargerService._enrich_charger(c, db) for c in chargers]

        if search:
            s_low = search.strip().lower()
            enriched = [
                c for c in enriched
                if s_low in c["charger_code"].lower()
                or s_low in c["connector_type"].lower()
                or s_low in c["location_name"].lower()
            ]

        return enriched

    @staticmethod
    def get_charger_by_id_or_code(db: Session, identifier: str) -> Optional[Charger]:
        if str(identifier).isdigit():
            charger = db.scalar(select(Charger).where(Charger.id == int(identifier)))
            if charger:
                return charger

        return db.scalar(select(Charger).where(Charger.charger_code == str(identifier).strip()))

    @staticmethod
    def create_charger(db: Session, data: ChargerCreate) -> dict:
        station_id = data.station_id
        if not station_id:
            station = db.scalar(select(Station).where(Station.station_code == settings.STATION_CODE))
            if not station:
                station = db.scalar(select(Station).order_by(Station.id.asc()))
            if not station:
                raise HTTPException(status_code=404, detail="No station available to associate charger with.")
            station_id = station.id
        else:
            station = db.scalar(select(Station).where(Station.id == station_id))
            if not station:
                raise HTTPException(status_code=404, detail=f"Station with ID {station_id} not found.")

        # Check unique code within the station
        code_check = db.scalar(
            select(Charger)
            .where(Charger.station_id == station_id)
            .where(Charger.charger_code == data.charger_code.strip())
        )
        if code_check:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Charger '{data.charger_code}' already exists at this station.",
            )

        new_charger = Charger(
            station_id=station_id,
            charger_code=data.charger_code.strip(),
            charger_type=data.charger_type,
            connector_type=data.connector_type,
            rated_power_kw=data.rated_power_kw,
            voltage=data.voltage or Decimal("230.0"),
            current_amp=data.current_amp or Decimal("0.0"),
            power_factor=data.power_factor or Decimal("0.94"),
            energy_delivered_kwh=Decimal("0.0"),
            status=data.status or "Available",
            location_name=data.location_name or "Main Canopy",
            data_source=settings.DATA_SOURCE_LABEL,
        )
        db.add(new_charger)
        db.commit()
        db.refresh(new_charger)

        return ChargerService._enrich_charger(new_charger, db)

    @staticmethod
    def update_charger(db: Session, identifier: str, data: ChargerUpdate) -> dict:
        charger = ChargerService.get_charger_by_id_or_code(db, identifier)
        if not charger:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Charger '{identifier}' not found.",
            )

        if data.charger_code is not None:
            charger.charger_code = data.charger_code.strip()
        if data.charger_type is not None:
            charger.charger_type = data.charger_type
        if data.connector_type is not None:
            charger.connector_type = data.connector_type
        if data.rated_power_kw is not None:
            charger.rated_power_kw = data.rated_power_kw
        if data.voltage is not None:
            charger.voltage = data.voltage
        if data.current_amp is not None:
            charger.current_amp = data.current_amp
        if data.power_factor is not None:
            charger.power_factor = data.power_factor
        if data.status is not None:
            charger.status = data.status
        if data.location_name is not None:
            charger.location_name = data.location_name
        if data.station_id is not None:
            charger.station_id = data.station_id

        db.commit()
        db.refresh(charger)
        return ChargerService._enrich_charger(charger, db)

    @staticmethod
    def delete_charger(db: Session, identifier: str) -> dict:
        charger = ChargerService.get_charger_by_id_or_code(db, identifier)
        if not charger:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Charger '{identifier}' not found.",
            )

        # Safeguard: prevent delete if charging session is currently ongoing
        active_session = db.scalar(
            select(ChargingSession)
            .where(ChargingSession.charger_id == charger.id)
            .where(ChargingSession.status == "Ongoing")
        )
        if active_session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot remove charger '{charger.charger_code}' while session {active_session.session_code} is actively running.",
            )

        code = charger.charger_code
        db.delete(charger)
        db.commit()
        return {"message": f"Charger '{code}' successfully removed.", "status": "ok"}
