from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.alert import Alert
from app.models.charger import Charger
from app.models.charging_session import ChargingSession
from app.models.meter_reading import MeterReading
from app.models.payment import Payment
from app.models.setting import StationSetting
from app.models.station import Station
from app.models.user import User

PRABHUS_CHARGER_PROFILES = [
    {
        "code": "PG-AC-01",
        "type": "AC",
        "connector": "Type 2",
        "power": 7.4,
        "voltage": 230.0,
        "current": 0.0,
        "power_factor": 0.95,
        "status": "Available",
        "energy_delivered": 142.5,
    },
    {
        "code": "PG-AC-02",
        "type": "AC",
        "connector": "Type 2",
        "power": 22.0,
        "voltage": 400.0,
        "current": 32.0,
        "power_factor": 0.94,
        "status": "Charging",
        "energy_delivered": 318.0,
    },
    {
        "code": "PG-DC-01",
        "type": "DC",
        "connector": "CCS2",
        "power": 60.0,
        "voltage": 500.0,
        "current": 105.0,
        "power_factor": 0.98,
        "status": "Charging",
        "energy_delivered": 890.4,
    },
    {
        "code": "PG-DC-02",
        "type": "DC",
        "connector": "CCS2",
        "power": 120.0,
        "voltage": 650.0,
        "current": 0.0,
        "power_factor": 0.99,
        "status": "Available",
        "energy_delivered": 1450.2,
    },
    {
        "code": "PG-DC-03",
        "type": "DC",
        "connector": "CHAdeMO",
        "power": 50.0,
        "voltage": 400.0,
        "current": 0.0,
        "power_factor": 0.97,
        "status": "Available",
        "energy_delivered": 620.0,
    },
    {
        "code": "PG-AC-03",
        "type": "AC",
        "connector": "Type 2",
        "power": 11.0,
        "voltage": 400.0,
        "current": 0.0,
        "power_factor": 0.92,
        "status": "Faulted",
        "energy_delivered": 85.0,
    },
]


def seed_database(force_reset: bool = False):
    """
    Seeds Prabhu's Grid - strictly single-station setup for Hyderabad.
    Guarantees table existence and populates demo configuration, chargers,
    meter readings, alerts, sessions, and settings.
    """
    import app.models  # ensure models are registered
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # 1. Administrator reference (never auto-seed hardcoded credentials)
        admin = db.scalar(select(User).where(User.role == "admin").limit(1))
        admin_id = admin.id if admin else None

        # If force reset requested or old multi-station data exists, clean up
        existing_stations = db.scalars(select(Station)).all()
        has_unrelated_stations = any(s.station_code != settings.STATION_CODE for s in existing_stations)

        if force_reset or has_unrelated_stations:
            # Clean up all old stations and dependent rows
            db.execute(delete(MeterReading))
            db.execute(delete(Alert))
            db.execute(delete(Payment))
            db.execute(delete(ChargingSession))
            db.execute(delete(Charger))
            db.execute(delete(StationSetting))
            db.execute(delete(Station))
            db.flush()

        # 2. Prabhu's Grid Station (Single Station Scope)
        station = db.scalar(select(Station).where(Station.station_code == settings.STATION_CODE))
        if not station:
            station = Station(
                station_code=settings.STATION_CODE,
                station_name=settings.STATION_NAME,
                owner_name=settings.STATION_OWNER,
                description="Personal EV charging station management and monitoring prototype in Hyderabad.",
                address=settings.DEFAULT_ADDRESS,
                city=settings.STATION_CITY,
                state=settings.STATION_STATE,
                country=settings.STATION_COUNTRY,
                postal_code="500081",
                latitude=Decimal("17.448293"),
                longitude=Decimal("78.374187"),
                status="Online",
                data_source="SIMULATED",
                created_by=admin_id,
            )
            db.add(station)
            db.flush()

        # 3. Station Settings
        setting = db.scalar(select(StationSetting).where(StationSetting.station_id == station.id))
        if not setting:
            setting = StationSetting(
                station_id=station.id,
                station_address=station.address or settings.DEFAULT_ADDRESS,
                tariff_per_kwh=Decimal(str(settings.DEFAULT_TARIFF)),
                electricity_cost_per_kwh=Decimal("7.5"),
                currency="INR",
                energy_unit="kWh",
                power_unit="kW",
                demo_mode_active=True,
                auto_refresh_seconds=15,
                notify_operational_alerts=True,
                notify_session_updates=True,
            )
            db.add(setting)
            db.flush()

        # 4. Configured Chargers for Prabhu's Grid
        existing_chargers = db.scalars(select(Charger).where(Charger.station_id == station.id)).all()
        charger_map = {c.charger_code: c for c in existing_chargers}

        created_chargers = []
        for profile in PRABHUS_CHARGER_PROFILES:
            code = profile["code"]
            if code not in charger_map:
                ch = Charger(
                    station_id=station.id,
                    charger_code=code,
                    charger_type=profile["type"],
                    connector_type=profile["connector"],
                    rated_power_kw=Decimal(str(profile["power"])),
                    voltage=Decimal(str(profile["voltage"])),
                    current_amp=Decimal(str(profile["current"])),
                    power_factor=Decimal(str(profile["power_factor"])),
                    energy_delivered_kwh=Decimal(str(profile["energy_delivered"])),
                    status=profile["status"],
                    data_source="SIMULATED",
                )
                db.add(ch)
                db.flush()
                created_chargers.append(ch)
            else:
                created_chargers.append(charger_map[code])

        # 5. Timestamped Meter Readings (for 24h trend charts)
        reading_count = db.scalar(select(MeterReading.id).limit(1))
        if reading_count is None:
            # Generate deterministic 24-hour hourly telemetry samples
            for h in range(24, 0, -1):
                sample_time = now - timedelta(hours=h)
                hour_of_day = sample_time.hour

                for ch in created_chargers:
                    # Realistic day-night curve peaking between 10:00 and 19:00
                    active_prob = 0.8 if 9 <= hour_of_day <= 20 else 0.25
                    rated = float(ch.rated_power_kw)

                    if ch.status == "Faulted":
                        p_kw = 0.0
                        curr = 0.0
                    elif (h % 3 == 0) and active_prob > 0.5:
                        p_kw = round(rated * (0.65 + ((h * 7) % 30) / 100.0), 2)
                        p_kw = min(p_kw, rated)
                        curr = round((p_kw * 1000) / float(ch.voltage or 230), 1)
                    else:
                        p_kw = 0.0
                        curr = 0.0

                    # Non-decreasing cumulative energy calculation
                    energy_cum = round(float(ch.energy_delivered_kwh) - (h * 1.8), 2)
                    energy_cum = max(10.0, energy_cum)

                    mr = MeterReading(
                        charger_id=ch.id,
                        timestamp=sample_time,
                        power_kw=Decimal(str(p_kw)),
                        energy_kwh=Decimal(str(energy_cum)),
                        voltage_v=ch.voltage,
                        current_a=Decimal(str(curr)),
                        power_factor=ch.power_factor,
                        data_source="SIMULATED",
                    )
                    db.add(mr)

        # 6. Active and Historical Charging Sessions for Prabhu's Grid
        sess_count = db.scalar(select(ChargingSession.id).limit(1))
        if sess_count is None:
            # Active ongoing sessions for currently charging chargers
            charging_chargers = [c for c in created_chargers if c.status == "Charging"]
            for idx, ch in enumerate(charging_chargers):
                dur_min = 28 + (idx * 15)
                start_dt = now - timedelta(minutes=dur_min)
                power_rate = min(float(ch.rated_power_kw), 50.0 if ch.charger_type == "DC" else 11.0)
                energy_delivered = round(power_rate * (dur_min / 60.0) * 0.9, 1)
                tariff = Decimal(str(settings.DEFAULT_TARIFF))

                sess = ChargingSession(
                    session_code=f"SES-PG-{ch.charger_code[-2:]}-{idx + 1:02d}",
                    charger_id=ch.id,
                    user_id=admin_id,
                    start_time=start_dt,
                    end_time=None,
                    duration_seconds=dur_min * 60,
                    energy_delivered_kwh=Decimal(str(energy_delivered)),
                    peak_power_kw=Decimal(str(power_rate)),
                    unit_price=tariff,
                    total_amount=round(Decimal(str(energy_delivered)) * tariff, 2),
                    status="Ongoing",
                    data_source="SIMULATED",
                )
                db.add(sess)

            # Historical completed sessions
            for i in range(25):
                ch = created_chargers[i % len(created_chargers)]
                if ch.status == "Faulted" and i % 3 != 0:
                    continue

                dur_min = 20 + ((i * 13) % 75)
                days_ago = (i * 2) % 15
                start_dt = now - timedelta(days=days_ago, hours=(i % 14) + 1, minutes=dur_min)
                end_dt = start_dt + timedelta(minutes=dur_min)
                is_failed = (i == 7)
                status_str = "Failed" if is_failed else "Completed"
                
                power_rate = min(float(ch.rated_power_kw), 45.0 if ch.charger_type == "DC" else 9.5)
                energy_val = Decimal("0.0") if is_failed else Decimal(str(round(power_rate * (dur_min / 60.0) * 0.88, 1)))
                tariff = Decimal(str(settings.DEFAULT_TARIFF))
                amt = Decimal("0.0") if is_failed else round(energy_val * tariff, 2)

                sess = ChargingSession(
                    session_code=f"SES-PG-HIST-{i + 1:03d}",
                    charger_id=ch.id,
                    user_id=admin_id,
                    start_time=start_dt,
                    end_time=end_dt,
                    duration_seconds=dur_min * 60,
                    energy_delivered_kwh=energy_val,
                    peak_power_kw=Decimal(str(power_rate)),
                    unit_price=tariff,
                    total_amount=amt,
                    status=status_str,
                    data_source="SIMULATED",
                )
                db.add(sess)
                db.flush()

                if not is_failed:
                    payment = Payment(
                        charging_session_id=sess.id,
                        amount=amt,
                        currency="INR",
                        payment_method="simulated_upi",
                        status="completed",
                        transaction_reference=f"TXN-PG-{i + 1:04d}",
                        created_at=end_dt,
                    )
                    db.add(payment)

        # 7. Station Alerts
        alert_count = db.scalar(select(Alert.id).limit(1))
        if alert_count is None:
            faulted_charger = next((c for c in created_chargers if c.status == "Faulted"), None)
            alerts_to_seed = [
                Alert(
                    station_id=station.id,
                    charger_id=faulted_charger.id if faulted_charger else None,
                    severity="warning",
                    code="CHARGER_GROUND_FAULT",
                    title="Charger PG-AC-03 Insulation Fault",
                    message="Ground fault detected on PG-AC-03 connector. Charger isolated automatically for inspection.",
                    is_active=True,
                    data_source="SIMULATED",
                ),
                Alert(
                    station_id=station.id,
                    charger_id=None,
                    severity="info",
                    code="STATION_ONLINE",
                    title="Prabhu's Grid Systems Operational",
                    message="Station telemetry feed active in simulated prototype mode.",
                    is_active=True,
                    data_source="SIMULATED",
                ),
            ]
            for al in alerts_to_seed:
                db.add(al)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error seeding Prabhu's Grid: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database(force_reset=True)
    print("Prabhu's Grid database seeded successfully.")
