from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.seed import seed_database
from app.models.alert import Alert
from app.models.charger import Charger
from app.models.charging_session import ChargingSession
from app.models.maintenance import MaintenanceRecord
from app.models.meter_reading import MeterReading
from app.models.setting import StationSetting
from app.models.station import Station
from app.models.station_expense import StationExpense
from app.schemas.station import StationCreate, StationUpdate


class StationService:
    @staticmethod
    def get_prabhus_grid_station(db: Session) -> Station:
        """Retrieves Prabhu's Grid default station record."""
        station = db.scalar(select(Station).where(Station.station_code == settings.STATION_CODE))
        if not station:
            seed_database(force_reset=False)
            station = db.scalar(select(Station).where(Station.station_code == settings.STATION_CODE))
            if not station:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Default station record could not be initialized.",
                )
        return station

    @staticmethod
    def get_station_by_id_or_code(db: Session, identifier: str) -> Optional[Station]:
        if str(identifier).isdigit():
            station = db.scalar(select(Station).where(Station.id == int(identifier)))
            if station:
                return station
        return db.scalar(select(Station).where(Station.station_code == identifier))

    @staticmethod
    def compute_station_metrics(station: Station, db: Session) -> dict:
        chargers = db.scalars(
            select(Charger).where(Charger.station_id == station.id).order_by(Charger.charger_code)
        ).all()
        setting = db.scalar(select(StationSetting).where(StationSetting.station_id == station.id))

        tariff = float(setting.tariff_per_kwh) if setting else settings.DEFAULT_TARIFF
        elec_rate = float(setting.electricity_cost_per_kwh) if setting else 8.5
        address = setting.station_address if setting and setting.station_address else (station.address or settings.DEFAULT_ADDRESS)

        # 1. Capacity & instantaneous power
        installed_capacity_kw = sum(float(c.rated_power_kw) for c in chargers)
        current_charging_power_kw = 0.0
        active_chargers = 0
        available_chargers = 0
        faulted_chargers = 0
        offline_chargers = 0

        for c in chargers:
            st = c.status.lower()
            if st == "charging":
                active_chargers += 1
                if c.charger_type == "DC":
                    calc_kw = (float(c.voltage or 500) * float(c.current_amp or 0)) / 1000.0
                else:
                    calc_kw = (float(c.voltage or 230) * float(c.current_amp or 0) * float(c.power_factor or 0.94)) / 1000.0
                power_kw = min(float(c.rated_power_kw), max(0.0, calc_kw))
                current_charging_power_kw += power_kw
            elif st == "available":
                available_chargers += 1
            elif st == "faulted":
                faulted_chargers += 1
            else:
                offline_chargers += 1

        current_charging_power_kw = round(current_charging_power_kw, 2)

        # 2. Sessions & Energy delivered
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

        all_sessions = db.scalars(
            select(ChargingSession)
            .join(Charger, ChargingSession.charger_id == Charger.id)
            .where(Charger.station_id == station.id)
        ).all()

        total_energy_kwh = sum(float(s.energy_delivered_kwh) for s in all_sessions)
        energy_today_kwh = sum(float(s.energy_delivered_kwh) for s in all_sessions if s.start_time >= today_start)
        energy_month_kwh = sum(float(s.energy_delivered_kwh) for s in all_sessions if s.start_time >= month_start)

        ongoing_sessions = [s for s in all_sessions if s.status.lower() == "ongoing"]
        ongoing_count = len(ongoing_sessions)

        # 3. Utilization rate
        operational_chargers = len(chargers) - faulted_chargers - offline_chargers
        utilization_rate = (
            round((active_chargers / operational_chargers) * 100.0, 1)
            if operational_chargers > 0
            else 0.0
        )

        # 4. Financial Calculations based on real definitions:
        # Charging revenue = Energy delivered × Applicable charging tariff (or sum of recorded total_amount)
        total_charging_revenue = round(
            sum(float(s.total_amount) if float(s.total_amount) > 0 else (float(s.energy_delivered_kwh) * float(s.unit_price or tariff)) for s in all_sessions),
            2
        )
        estimated_today_cost = round(energy_today_kwh * tariff, 2)

        # Electricity expense = Energy consumed × Applicable electricity rate
        total_electricity_expense = round(total_energy_kwh * elec_rate, 2)

        # Other operating expenses = recorded expenses in station_expenses + maintenance costs
        recorded_expenses = db.scalars(
            select(StationExpense).where(StationExpense.station_id == station.id)
        ).all()
        maint_costs = db.scalars(
            select(MaintenanceRecord).where(MaintenanceRecord.station_id == station.id)
        ).all()

        other_operating_expenses = round(
            sum(float(e.amount) for e in recorded_expenses) + sum(float(m.cost) for m in maint_costs) + float(station.monthly_fixed_cost or 18000.0),
            2
        )

        # Operating profit = Charging revenue − Electricity expense − Other operating expenses
        operating_profit = round(total_charging_revenue - total_electricity_expense - other_operating_expenses, 2)

        # ROI % = (Operating profit / Recorded Investment) * 100
        initial_inv = float(station.initial_investment or 2500000.0)
        roi_percentage = round((operating_profit / initial_inv) * 100.0, 2) if initial_inv > 0 else 0.0

        return {
            "id": station.id,
            "station_code": station.station_code,
            "station_name": station.station_name,
            "owner_name": station.owner_name,
            "city": station.city,
            "state": station.state,
            "country": station.country,
            "address": address,
            "status": station.status,
            "initial_investment": initial_inv,
            "monthly_fixed_cost": float(station.monthly_fixed_cost or 18000.0),
            "data_source": settings.DATA_SOURCE_LABEL,
            "disclaimer": "DEMO MODE — SIMULATED DATA — NOT LIVE STATION TELEMETRY",
            "created_at": station.created_at,
            "updated_at": station.updated_at,
            "installed_capacity_kw": round(installed_capacity_kw, 1),
            "current_charging_power_kw": current_charging_power_kw,
            "energy_today_kwh": round(energy_today_kwh, 1),
            "energy_month_kwh": round(energy_month_kwh, 1),
            "total_energy_kwh": round(total_energy_kwh, 1),
            "active_sessions_count": ongoing_count,
            "total_chargers": len(chargers),
            "active_chargers": active_chargers,
            "available_chargers": available_chargers,
            "faulted_chargers": faulted_chargers,
            "offline_chargers": offline_chargers,
            "utilization_rate": utilization_rate,
            "tariff_per_kwh": tariff,
            "electricity_cost_per_kwh": elec_rate,
            "estimated_today_cost": estimated_today_cost,
            "total_revenue": total_charging_revenue,
            "total_electricity_expense": total_electricity_expense,
            "total_operating_expenses": other_operating_expenses,
            "operating_profit": operating_profit,
            "roi_percentage": roi_percentage,
        }

    @staticmethod
    def get_all_stations(db: Session) -> List[dict]:
        stations = db.scalars(select(Station).order_by(Station.id.asc())).all()
        if not stations:
            default_st = StationService.get_prabhus_grid_station(db)
            stations = [default_st]
        return [StationService.compute_station_metrics(st, db) for st in stations]

    @staticmethod
    def get_station_summary(db: Session, station_id_or_code: Optional[str] = None) -> dict:
        if station_id_or_code:
            st = StationService.get_station_by_id_or_code(db, station_id_or_code)
            if not st:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Station '{station_id_or_code}' not found.",
                )
            return StationService.compute_station_metrics(st, db)
        station = StationService.get_prabhus_grid_station(db)
        return StationService.compute_station_metrics(station, db)

    @staticmethod
    def create_station(db: Session, data: StationCreate, user_id: Optional[int] = None) -> dict:
        existing = db.scalar(select(Station).where(Station.station_code == data.station_code.strip()))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Station code '{data.station_code}' already exists.",
            )

        new_station = Station(
            station_code=data.station_code.strip().upper(),
            station_name=data.station_name.strip(),
            owner_name=data.owner_name.strip(),
            description=data.description,
            address=data.address,
            city=data.city,
            state=data.state,
            country=data.country,
            postal_code=data.postal_code,
            latitude=data.latitude,
            longitude=data.longitude,
            status=data.status,
            initial_investment=data.initial_investment,
            monthly_fixed_cost=data.monthly_fixed_cost,
            created_by=user_id,
        )
        db.add(new_station)
        db.commit()
        db.refresh(new_station)

        # Create baseline station setting
        st_setting = StationSetting(
            station_id=new_station.id,
            station_address=new_station.address or "",
            tariff_per_kwh=Decimal(str(settings.DEFAULT_TARIFF)),
            electricity_cost_per_kwh=Decimal("8.5"),
            currency="INR",
            energy_unit="kWh",
            power_unit="kW",
            demo_mode_active=True,
            auto_refresh_seconds=15,
        )
        db.add(st_setting)
        db.commit()

        return StationService.compute_station_metrics(new_station, db)

    @staticmethod
    def update_station(db: Session, identifier: str, data: StationUpdate) -> dict:
        station = StationService.get_station_by_id_or_code(db, identifier)
        if not station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Station '{identifier}' not found.",
            )

        update_dict = data.model_dump(exclude_unset=True)
        for key, val in update_dict.items():
            if hasattr(station, key) and val is not None:
                setattr(station, key, val)

        db.commit()
        db.refresh(station)

        # Also update station setting address if modified
        if data.address is not None:
            setting = db.scalar(select(StationSetting).where(StationSetting.station_id == station.id))
            if setting:
                setting.station_address = data.address
                db.commit()

        return StationService.compute_station_metrics(station, db)

    @staticmethod
    def delete_station(db: Session, identifier: str) -> dict:
        station = StationService.get_station_by_id_or_code(db, identifier)
        if not station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Station '{identifier}' not found.",
            )

        # Safeguard: prevent deleting Prabhu's Grid if it's the sole station
        total_stations = db.scalar(select(func.count(Station.id)))
        if total_stations <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the only remaining station in EVanta OS.",
            )

        # Safeguard: check active sessions
        active_sessions = db.scalar(
            select(func.count(ChargingSession.id))
            .join(Charger, ChargingSession.charger_id == Charger.id)
            .where(Charger.station_id == station.id)
            .where(ChargingSession.status == "Ongoing")
        )
        if active_sessions > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete station while {active_sessions} charging session(s) are actively ongoing.",
            )

        st_code = station.station_code
        db.delete(station)
        db.commit()

        return {
            "status": "success",
            "message": f"Station '{st_code}' deleted successfully.",
        }

    @staticmethod
    def get_settings(db: Session, station_id_or_code: Optional[str] = None) -> dict:
        station = (
            StationService.get_station_by_id_or_code(db, station_id_or_code)
            if station_id_or_code
            else StationService.get_prabhus_grid_station(db)
        )
        setting = db.scalar(select(StationSetting).where(StationSetting.station_id == station.id))
        if not setting:
            setting = StationSetting(
                station_id=station.id,
                station_address=station.address or settings.DEFAULT_ADDRESS,
                tariff_per_kwh=Decimal(str(settings.DEFAULT_TARIFF)),
                electricity_cost_per_kwh=Decimal("8.5"),
                currency="INR",
                energy_unit="kWh",
                power_unit="kW",
                demo_mode_active=True,
                auto_refresh_seconds=15,
                notify_operational_alerts=True,
                notify_session_updates=True,
            )
            db.add(setting)
            db.commit()
            db.refresh(setting)

        return {
            "id": setting.id,
            "station_id": setting.station_id,
            "station_address": setting.station_address,
            "tariff_per_kwh": float(setting.tariff_per_kwh),
            "electricity_cost_per_kwh": float(setting.electricity_cost_per_kwh),
            "currency": setting.currency,
            "energy_unit": setting.energy_unit,
            "power_unit": setting.power_unit,
            "demo_mode_active": setting.demo_mode_active,
            "auto_refresh_seconds": setting.auto_refresh_seconds,
            "notify_operational_alerts": setting.notify_operational_alerts,
            "notify_session_updates": setting.notify_session_updates,
            "data_source": settings.DATA_SOURCE_LABEL,
            "disclaimer": "DEMO MODE — SIMULATED DATA — NOT LIVE STATION TELEMETRY",
            "created_at": setting.created_at,
            "updated_at": setting.updated_at,
        }

    @staticmethod
    def update_settings(db: Session, update_data: dict, station_id_or_code: Optional[str] = None) -> dict:
        station = (
            StationService.get_station_by_id_or_code(db, station_id_or_code)
            if station_id_or_code
            else StationService.get_prabhus_grid_station(db)
        )
        setting = db.scalar(select(StationSetting).where(StationSetting.station_id == station.id))
        if not setting:
            setting = StationSetting(station_id=station.id)
            db.add(setting)

        if "station_address" in update_data and update_data["station_address"] is not None:
            setting.station_address = update_data["station_address"]
            station.address = update_data["station_address"]

        if "tariff_per_kwh" in update_data and update_data["tariff_per_kwh"] is not None:
            setting.tariff_per_kwh = Decimal(str(update_data["tariff_per_kwh"]))

        if "electricity_cost_per_kwh" in update_data and update_data["electricity_cost_per_kwh"] is not None:
            setting.electricity_cost_per_kwh = Decimal(str(update_data["electricity_cost_per_kwh"]))

        if "auto_refresh_seconds" in update_data and update_data["auto_refresh_seconds"] is not None:
            setting.auto_refresh_seconds = int(update_data["auto_refresh_seconds"])

        if "demo_mode_active" in update_data and update_data["demo_mode_active"] is not None:
            setting.demo_mode_active = bool(update_data["demo_mode_active"])

        db.commit()
        db.refresh(setting)
        return StationService.get_settings(db, station_id_or_code)

    @staticmethod
    def reset_demo_data(db: Session) -> dict:
        seed_database(force_reset=True)
        return {
            "status": "success",
            "message": "EVanta OS station demo data has been reset to baseline.",
            "station": settings.STATION_NAME,
            "data_source": settings.DATA_SOURCE_LABEL,
            "disclaimer": "DEMO MODE — SIMULATED DATA — NOT LIVE STATION TELEMETRY",
        }
