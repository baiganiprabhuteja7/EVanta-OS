from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.alert import Alert
from app.models.charger import Charger
from app.models.charging_session import ChargingSession
from app.models.maintenance import MaintenanceRecord
from app.models.meter_reading import MeterReading
from app.models.setting import StationSetting
from app.models.station import Station
from app.models.station_expense import StationExpense
from app.services.station_service import StationService


class AnalyticsService:
    @staticmethod
    def get_overview(db: Session, station_id_or_code: Optional[str] = None) -> dict:
        """Calculates true electrical, operational and business KPIs directly from database records."""
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

        # Retrieve target station or all stations
        if station_id_or_code:
            station = StationService.get_station_by_id_or_code(db, station_id_or_code)
            if not station:
                station = StationService.get_prabhus_grid_station(db)
            stations = [station]
        else:
            stations = db.scalars(select(Station).order_by(Station.id.asc())).all()
            if not stations:
                stations = [StationService.get_prabhus_grid_station(db)]
            station = stations[0]

        station_ids = [s.id for s in stations]

        # Chargers
        chargers = db.scalars(
            select(Charger).where(Charger.station_id.in_(station_ids)).order_by(Charger.charger_code)
        ).all()

        total_chargers = len(chargers)
        installed_capacity_kw = sum(float(c.rated_power_kw) for c in chargers)

        active_chargers = 0
        available_chargers = 0
        faulted_chargers = 0
        offline_chargers = 0
        current_charging_power_kw = 0.0

        for c in chargers:
            st = c.status.lower()
            if st == "charging":
                active_chargers += 1
                if c.charger_type == "DC":
                    calc_kw = (float(c.voltage or 500) * float(c.current_amp or 0)) / 1000.0
                else:
                    calc_kw = (float(c.voltage or 230) * float(c.current_amp or 0) * float(c.power_factor or 0.94)) / 1000.0
                current_charging_power_kw += min(float(c.rated_power_kw), max(0.0, calc_kw))
            elif st == "available":
                available_chargers += 1
            elif st == "faulted":
                faulted_chargers += 1
            else:
                offline_chargers += 1

        current_charging_power_kw = round(current_charging_power_kw, 2)

        # Sessions
        sessions = db.scalars(
            select(ChargingSession)
            .join(Charger, ChargingSession.charger_id == Charger.id)
            .where(Charger.station_id.in_(station_ids))
            .order_by(ChargingSession.start_time.desc())
        ).all()

        active_sessions = [s for s in sessions if s.status.lower() == "ongoing"]
        active_sessions_count = len(active_sessions)

        energy_today_kwh = sum(float(s.energy_delivered_kwh) for s in sessions if s.start_time >= today_start)
        energy_month_kwh = sum(float(s.energy_delivered_kwh) for s in sessions if s.start_time >= month_start)
        total_energy_kwh = sum(float(s.energy_delivered_kwh) for s in sessions)

        # Settings
        setting = db.scalar(select(StationSetting).where(StationSetting.station_id == station.id))
        tariff = float(setting.tariff_per_kwh) if setting else 18.5
        elec_rate = float(setting.electricity_cost_per_kwh) if setting else 8.5

        # Financial Business Logic:
        # 1. Total charging revenue = Energy delivered × Applicable charging tariff (or sum of session total_amount)
        total_charging_revenue = round(
            sum(float(s.total_amount) if float(s.total_amount) > 0 else (float(s.energy_delivered_kwh) * float(s.unit_price or tariff)) for s in sessions),
            2
        )
        estimated_today_cost = round(energy_today_kwh * tariff, 2)

        # 2. Electricity expense = Energy consumed × Applicable electricity rate
        total_electricity_expense = round(total_energy_kwh * elec_rate, 2)

        # 3. Other operating expenses = recorded expenses in station_expenses + maintenance costs + monthly fixed cost
        recorded_expenses = db.scalars(
            select(StationExpense).where(StationExpense.station_id.in_(station_ids))
        ).all()
        maint_records = db.scalars(
            select(MaintenanceRecord).where(MaintenanceRecord.station_id.in_(station_ids))
        ).all()

        other_operating_expenses = round(
            sum(float(e.amount) for e in recorded_expenses)
            + sum(float(m.cost) for m in maint_records)
            + sum(float(s.monthly_fixed_cost or 18000.0) for s in stations),
            2
        )

        # 4. Operating profit = Charging revenue − Electricity expense − Other operating expenses
        operating_profit = round(total_charging_revenue - total_electricity_expense - other_operating_expenses, 2)

        # 5. Return on investment = (Operating profit / Recorded capital investment) * 100
        total_investment = sum(float(s.initial_investment or 2500000.0) for s in stations)
        roi_percentage = round((operating_profit / total_investment) * 100.0, 2) if total_investment > 0 else 0.0

        # Utilization Rate
        operational_chargers = total_chargers - faulted_chargers - offline_chargers
        utilization_rate = (
            round((active_chargers / operational_chargers) * 100.0, 1)
            if operational_chargers > 0
            else 0.0
        )

        # 6. Hourly load trends (past 24 hours) from meter readings and sessions
        hourly_readings = db.scalars(
            select(MeterReading)
            .join(Charger, MeterReading.charger_id == Charger.id)
            .where(Charger.station_id.in_(station_ids))
            .where(MeterReading.timestamp >= now - timedelta(hours=24))
            .order_by(MeterReading.timestamp.asc())
        ).all()

        hourly_buckets: Dict[datetime, dict] = {}
        for r in hourly_readings:
            h_dt = r.timestamp.replace(minute=0, second=0, microsecond=0)
            if h_dt not in hourly_buckets:
                hourly_buckets[h_dt] = {"power": 0.0, "energy": 0.0, "active": 0}
            hourly_buckets[h_dt]["power"] += float(r.power_kw)
            hourly_buckets[h_dt]["energy"] += float(r.energy_kwh)
            if float(r.power_kw) > 0.1:
                hourly_buckets[h_dt]["active"] += 1

        # Sessions ongoing in hourly window
        for s in sessions:
            if s.start_time >= now - timedelta(hours=24):
                h_dt = s.start_time.replace(minute=0, second=0, microsecond=0)
                if h_dt not in hourly_buckets:
                    hourly_buckets[h_dt] = {"power": 0.0, "energy": 0.0, "active": 0}
                hourly_buckets[h_dt]["energy"] += float(s.energy_delivered_kwh)
                hourly_buckets[h_dt]["active"] += 1
                hourly_buckets[h_dt]["power"] = max(hourly_buckets[h_dt]["power"], float(s.peak_power_kw or 22.0))

        hourly_trends = []
        for h in range(23, -1, -1):
            h_dt = (now - timedelta(hours=h)).replace(minute=0, second=0, microsecond=0)
            bucket = hourly_buckets.get(h_dt, {"power": 0.0, "energy": 0.0, "active": 0})
            hourly_trends.append({
                "timestamp": h_dt,
                "hour_label": h_dt.strftime("%H:%M"),
                "power_kw": round(bucket["power"], 1),
                "energy_kwh": round(bucket["energy"], 1),
                "active_chargers": bucket["active"],
                "data_source": settings.DATA_SOURCE_LABEL,
            })

        # 7. Daily trends (past 14 days) directly from database charging sessions
        daily_trends = []
        for d in range(13, -1, -1):
            day_dt = now - timedelta(days=d)
            date_str = day_dt.strftime("%b %d")
            day_start = datetime(day_dt.year, day_dt.month, day_dt.day, tzinfo=timezone.utc)
            day_end = day_start + timedelta(days=1)

            day_sessions = [s for s in sessions if day_start <= s.start_time < day_end]
            day_energy = sum(float(s.energy_delivered_kwh) for s in day_sessions)
            day_revenue = sum(
                float(s.total_amount) if float(s.total_amount) > 0 else (float(s.energy_delivered_kwh) * float(s.unit_price or tariff))
                for s in day_sessions
            )
            day_elec_cost = round(day_energy * elec_rate, 2)
            day_profit = round(day_revenue - day_elec_cost, 2)

            daily_trends.append({
                "date_label": date_str,
                "energy_kwh": round(day_energy, 1),
                "total_sessions": len(day_sessions),
                "estimated_revenue": round(day_revenue, 2),
                "electricity_expense": day_elec_cost,
                "operating_profit": day_profit,
                "data_source": settings.DATA_SOURCE_LABEL,
            })

        # 8. Recent Activities (from sessions, maintenance, alerts)
        recent_activities = []
        for s in sessions[:5]:
            recent_activities.append({
                "id": f"sess-{s.id}",
                "type": "session",
                "timestamp": s.start_time,
                "title": f"Session {s.session_code}",
                "description": f"{s.status} on charger ID {s.charger_id} ({float(s.energy_delivered_kwh):.1f} kWh, ₹{float(s.total_amount):.2f})",
                "status": s.status,
                "badge_color": "#00e5a3" if s.status == "Completed" else "#38bdf8",
            })

        for m in maint_records[:3]:
            recent_activities.append({
                "id": f"maint-{m.id}",
                "type": "maintenance",
                "timestamp": m.created_at,
                "title": f"Maintenance: {m.equipment_name}",
                "description": f"Status: {m.status} · Priority: {m.severity} · {m.issue_description[:60]}...",
                "status": m.status,
                "badge_color": "#f59e0b" if m.status != "Completed" else "#10b981",
            })

        recent_activities.sort(key=lambda x: x["timestamp"], reverse=True)

        return {
            "station_code": station.station_code,
            "station_name": station.station_name if len(stations) == 1 else "Evanta Network Grid",
            "location": f"{station.city}, {station.state}, {station.country}",
            "installed_capacity_kw": round(installed_capacity_kw, 1),
            "current_charging_power_kw": current_charging_power_kw,
            "energy_today_kwh": round(energy_today_kwh, 1),
            "energy_month_kwh": round(energy_month_kwh, 1),
            "utilization_rate": utilization_rate,
            "tariff_per_kwh": tariff,
            "electricity_cost_per_kwh": elec_rate,
            "estimated_today_cost": estimated_today_cost,
            "total_stations": len(stations),
            "total_chargers": total_chargers,
            "active_chargers": active_chargers,
            "occupied_chargers": active_chargers,
            "available_chargers": available_chargers,
            "faulted_chargers": faulted_chargers,
            "offline_chargers": offline_chargers,
            "active_sessions_count": active_sessions_count,
            "total_charging_revenue": total_charging_revenue,
            "electricity_expenses": total_electricity_expense,
            "operating_expenses": other_operating_expenses,
            "operating_profit": operating_profit,
            "return_on_investment": roi_percentage,
            "data_source": settings.DATA_SOURCE_LABEL,
            "disclaimer": "DEMO MODE — SIMULATED DATA — NOT LIVE STATION TELEMETRY",
            "hourly_trends": hourly_trends,
            "daily_trends": daily_trends,
            "recent_activities": recent_activities[:10],
        }

    @staticmethod
    def get_financial_report(
        db: Session,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        station_id: Optional[int] = None,
    ) -> dict:
        """Detailed commercial performance and financial intelligence report."""
        stations_query = select(Station)
        if station_id:
            stations_query = stations_query.where(Station.id == station_id)
        stations = db.scalars(stations_query.order_by(Station.id.asc())).all()

        start_dt = None
        end_dt = None
        if from_date:
            try:
                start_dt = datetime.strptime(from_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        if to_date:
            try:
                end_dt = datetime.strptime(to_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
            except ValueError:
                pass

        # Query sessions in date range
        sessions_query = select(ChargingSession).join(Charger, ChargingSession.charger_id == Charger.id)
        if station_id:
            sessions_query = sessions_query.where(Charger.station_id == station_id)
        if start_dt:
            sessions_query = sessions_query.where(ChargingSession.start_time >= start_dt)
        if end_dt:
            sessions_query = sessions_query.where(ChargingSession.start_time <= end_dt)

        sessions = db.scalars(sessions_query).all()

        total_energy = sum(float(s.energy_delivered_kwh) for s in sessions)

        # Baseline tariffs
        default_setting = db.scalar(select(StationSetting).order_by(StationSetting.id.asc()))
        sys_tariff = float(default_setting.tariff_per_kwh) if default_setting else 18.5
        sys_elec_rate = float(default_setting.electricity_cost_per_kwh) if default_setting else 8.5

        total_revenue = sum(
            float(s.total_amount) if float(s.total_amount) > 0 else (float(s.energy_delivered_kwh) * float(s.unit_price or sys_tariff))
            for s in sessions
        )
        total_elec_expense = total_energy * sys_elec_rate

        # Query recorded expenses in date range
        expenses_query = select(StationExpense)
        if station_id:
            expenses_query = expenses_query.where(StationExpense.station_id == station_id)
        if start_dt:
            expenses_query = expenses_query.where(StationExpense.expense_date >= start_dt)
        if end_dt:
            expenses_query = expenses_query.where(StationExpense.expense_date <= end_dt)

        expenses = db.scalars(expenses_query).all()
        maint_records = db.scalars(select(MaintenanceRecord)).all()
        if station_id:
            maint_records = [m for m in maint_records if m.station_id == station_id]

        total_op_expenses = sum(float(e.amount) for e in expenses) + sum(float(m.cost) for m in maint_records)
        # Add proportional fixed operating costs
        months = max(1, (end_dt - start_dt).days // 30) if (start_dt and end_dt) else 1
        total_op_expenses += sum(float(s.monthly_fixed_cost or 18000.0) for s in stations) * months

        gross_contribution = round(total_revenue - total_elec_expense, 2)
        gross_margin_pct = round((gross_contribution / total_revenue) * 100.0, 2) if total_revenue > 0 else 0.0
        net_operating_profit = round(gross_contribution - total_op_expenses, 2)

        total_investment = sum(float(s.initial_investment or 2500000.0) for s in stations)
        roi_pct = round((net_operating_profit / total_investment) * 100.0, 2) if total_investment > 0 else 0.0

        # Breakdowns by station
        stations_financials = []
        for st in stations:
            st_chargers = db.scalars(select(Charger).where(Charger.station_id == st.id)).all()
            st_sessions = [s for s in sessions if any(s.charger_id == c.id for c in st_chargers)]
            st_energy = sum(float(s.energy_delivered_kwh) for s in st_sessions)
            st_rev = sum(
                float(s.total_amount) if float(s.total_amount) > 0 else (float(s.energy_delivered_kwh) * float(s.unit_price or sys_tariff))
                for s in st_sessions
            )
            st_elec = round(st_energy * sys_elec_rate, 2)
            st_exp = sum(float(e.amount) for e in expenses if e.station_id == st.id) + float(st.monthly_fixed_cost or 18000.0) * months
            st_profit = round(st_rev - st_elec - st_exp, 2)
            st_inv = float(st.initial_investment or 2500000.0)
            st_roi = round((st_profit / st_inv) * 100.0, 2) if st_inv > 0 else 0.0

            stations_financials.append({
                "station_id": st.id,
                "station_code": st.station_code,
                "station_name": st.station_name,
                "total_chargers": len(st_chargers),
                "total_sessions": len(st_sessions),
                "energy_delivered_kwh": round(st_energy, 1),
                "charging_revenue": round(st_rev, 2),
                "electricity_expense": st_elec,
                "operating_expenses": round(st_exp, 2),
                "operating_profit": st_profit,
                "initial_investment": st_inv,
                "roi_percentage": st_roi,
            })

        # Breakdowns by charger
        all_chargers = db.scalars(select(Charger)).all()
        if station_id:
            all_chargers = [c for c in all_chargers if c.station_id == station_id]

        chargers_financials = []
        for ch in all_chargers:
            ch_sessions = [s for s in sessions if s.charger_id == ch.id]
            ch_energy = sum(float(s.energy_delivered_kwh) for s in ch_sessions)
            ch_rev = sum(
                float(s.total_amount) if float(s.total_amount) > 0 else (float(s.energy_delivered_kwh) * float(s.unit_price or sys_tariff))
                for s in ch_sessions
            )
            ch_elec = round(ch_energy * sys_elec_rate, 2)
            ch_profit = round(ch_rev - ch_elec, 2)
            ch_station = next((s for s in stations if s.id == ch.station_id), None)

            chargers_financials.append({
                "charger_id": ch.id,
                "charger_code": ch.charger_code,
                "station_name": ch_station.station_name if ch_station else "Unknown",
                "charger_type": ch.charger_type,
                "connector_type": ch.connector_type,
                "total_sessions": len(ch_sessions),
                "energy_delivered_kwh": round(ch_energy, 1),
                "charging_revenue": round(ch_rev, 2),
                "electricity_expense": ch_elec,
                "operating_profit": ch_profit,
            })

        return {
            "from_date": from_date,
            "to_date": to_date,
            "tariff_per_kwh": sys_tariff,
            "electricity_rate_per_kwh": sys_elec_rate,
            "total_energy_delivered_kwh": round(total_energy, 1),
            "total_charging_revenue": round(total_revenue, 2),
            "total_electricity_expense": round(total_elec_expense, 2),
            "total_operating_expenses": round(total_op_expenses, 2),
            "gross_contribution": gross_contribution,
            "gross_margin_percentage": gross_margin_pct,
            "net_operating_profit": net_operating_profit,
            "total_recorded_investment": round(total_investment, 2),
            "roi_percentage": roi_pct,
            "stations_financials": stations_financials,
            "chargers_financials": chargers_financials,
            "data_source": settings.DATA_SOURCE_LABEL,
            "disclaimer": "DERIVED FROM SYSTEM DATABASE RECORDS AND CONFIGURED TARIFFS",
        }
