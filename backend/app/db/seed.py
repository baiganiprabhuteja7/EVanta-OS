from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.charger import Charger
from app.models.charging_session import ChargingSession
from app.models.payment import Payment
from app.models.setting import WorkspaceSetting
from app.models.station import Station
from app.models.user import User

SEED_STATIONS = [
    {
        "id": "EV-BLR-001",
        "name": "Northstar Mobility Hub",
        "city": "Bengaluru",
        "state": "Karnataka",
        "address": "42 Residency Road, Ashok Nagar, Bengaluru 560025",
        "chargers": 8,
        "active_chargers": 7,
        "status": "Online",
    },
    {
        "id": "EV-HYD-002",
        "name": "Airport Gateway",
        "city": "Hyderabad",
        "state": "Telangana",
        "address": "Shamshabad Airport Access Road, Hyderabad 500409",
        "chargers": 6,
        "active_chargers": 6,
        "status": "Online",
    },
    {
        "id": "EV-PUN-003",
        "name": "Tech Park Central",
        "city": "Pune",
        "state": "Maharashtra",
        "address": "Plot 18, Hinjawadi Phase 2, Pune 411057",
        "chargers": 5,
        "active_chargers": 4,
        "status": "Online",
    },
    {
        "id": "EV-MUM-004",
        "name": "Harbour Point",
        "city": "Mumbai",
        "state": "Maharashtra",
        "address": "Eastern Freeway Service Road, Wadala, Mumbai 400037",
        "chargers": 5,
        "active_chargers": 0,
        "status": "Offline",
    },
    {
        "id": "EV-MAA-005",
        "name": "Greenway Plaza",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "address": "OMR, Perungudi, Chennai 600096",
        "chargers": 4,
        "active_chargers": 2,
        "status": "Maintenance",
    },
    {
        "id": "EV-DEL-006",
        "name": "Ring Road Express",
        "city": "Delhi",
        "state": "NCR",
        "address": "Outer Ring Road, Pitampura, New Delhi 110034",
        "chargers": 4,
        "active_chargers": 3,
        "status": "Online",
    },
    {
        "id": "EV-JAI-007",
        "name": "Pink City Charge Point",
        "city": "Jaipur",
        "state": "Rajasthan",
        "address": "Tonk Road, Durgapura, Jaipur 302018",
        "chargers": 6,
        "active_chargers": 0,
        "status": "Faulted",
    },
    {
        "id": "EV-KOC-008",
        "name": "Coastal Link Station",
        "city": "Kochi",
        "state": "Kerala",
        "address": "NH 66, Edappally, Kochi 682024",
        "chargers": 4,
        "active_chargers": 0,
        "status": "Faulted",
    },
]

CHARGER_PROFILES = [
    {"type": "AC", "connector": "Type 2", "power": 7.4, "voltage": 230, "current": 32},
    {"type": "AC", "connector": "Type 2", "power": 22.0, "voltage": 400, "current": 34},
    {"type": "DC", "connector": "CCS2", "power": 60.0, "voltage": 500, "current": 120},
    {"type": "DC", "connector": "CCS2", "power": 120.0, "voltage": 650, "current": 185},
    {"type": "DC", "connector": "CHAdeMO", "power": 50.0, "voltage": 400, "current": 125},
]


def seed_database():
    """Seeds initial administrative account, stations, chargers, sessions, and settings if empty."""
    from app.db.base import Base
    from app.db.session import engine
    import app.models  # ensure models are registered with Base.metadata

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # 1. Admin user
        admin = db.scalar(select(User).where(User.email == "admin@evanta.os"))
        if not admin:
            admin = User(
                full_name="EVanta Admin",
                email="admin@evanta.os",
                password_hash=hash_password("Admin@123456"),
                role="admin",
                is_active=True,
            )
            db.add(admin)
            db.flush()

        # 2. Workspace settings
        setting = db.scalar(select(WorkspaceSetting).order_by(WorkspaceSetting.id))
        if not setting:
            setting = WorkspaceSetting(
                user_id=admin.id,
                currency="INR",
                energy_unit="kWh",
                electricity_cost_per_kwh=Decimal("8.5"),
                initial_investment=Decimal("12500000.0"),
                monthly_operating_costs=Decimal("185000.0"),
                compact_tables=False,
                reduce_motion=False,
                notify_operational_alerts=True,
                notify_session_updates=True,
                notify_weekly_summary=False,
            )
            db.add(setting)

        # 3. Stations & Chargers
        station_count = db.scalar(select(Station.id).limit(1))
        if station_count is None:
            now = datetime.now(timezone.utc)
            all_chargers: list[Charger] = []

            for st_data in SEED_STATIONS:
                station = Station(
                    station_code=st_data["id"],
                    station_name=st_data["name"],
                    city=st_data["city"],
                    state=st_data["state"],
                    address=st_data["address"],
                    status=st_data["status"],
                    created_by=admin.id,
                )
                db.add(station)
                db.flush()

                prefix = st_data["id"].replace("EV-", "CH-")
                num_chargers = st_data["chargers"]
                active_chargers = st_data["active_chargers"]

                for i in range(1, num_chargers + 1):
                    profile = CHARGER_PROFILES[(i - 1 + len(st_data["id"])) % len(CHARGER_PROFILES)]
                    status_val = "Available"
                    if station.status == "Offline":
                        status_val = "Offline"
                    elif station.status in ["Faulted", "Maintenance"]:
                        status_val = "Faulted" if i == 1 else "Offline"
                    elif i <= active_chargers:
                        status_val = "Charging"

                    is_charging = status_val == "Charging"
                    current_amp = Decimal(str(profile["current"])) if is_charging else Decimal("0.0")

                    charger = Charger(
                        station_id=station.id,
                        charger_code=f"{prefix}-{str(i).zfill(2)}",
                        charger_type=profile["type"],
                        connector_type=profile["connector"],
                        rated_power_kw=Decimal(str(profile["power"])),
                        voltage=Decimal(str(profile["voltage"])),
                        current_amp=current_amp,
                        power_factor=Decimal("0.94"),
                        status=status_val,
                    )
                    db.add(charger)
                    db.flush()
                    all_chargers.append(charger)

            # 4. Initial Charging Sessions
            # Active/ongoing sessions for currently charging chargers
            ongoing_chargers = [c for c in all_chargers if c.status == "Charging"]
            for idx, ch in enumerate(ongoing_chargers):
                duration_min = 18 + ((idx * 13) % 62)
                start_dt = now - timedelta(minutes=duration_min)
                energy = Decimal(str(round(5.5 + ((idx * 19) % 147) / 10.0, 1)))
                rate = Decimal(str(19 + (idx % 6)))
                sess = ChargingSession(
                    session_code=f"SES-{ch.charger_code[-6:]}-{idx + 1:02d}",
                    charger_id=ch.id,
                    user_id=admin.id,
                    start_time=start_dt,
                    duration_seconds=duration_min * 60,
                    energy_delivered_kwh=energy,
                    peak_power_kw=ch.rated_power_kw,
                    unit_price=rate,
                    total_amount=round(energy * rate, 2),
                    status="Ongoing",
                )
                db.add(sess)

            # Historical completed sessions
            for idx in range(36):
                ch = all_chargers[(idx * 7 + 3) % len(all_chargers)]
                duration_min = 25 + ((idx * 17) % 96)
                days_ago = (idx * 5) % 30
                start_dt = now - timedelta(days=days_ago, hours=(idx % 12), minutes=duration_min)
                end_dt = start_dt + timedelta(minutes=duration_min)
                is_failed = idx % 13 == 0
                status_val = "Failed" if is_failed else "Completed"
                energy = Decimal("0.0") if is_failed else Decimal(str(round(12.0 + ((idx * 23) % 580) / 10.0, 1)))
                rate = Decimal(str(19 + ((idx + 2) % 6)))
                total_amt = Decimal("0.0") if is_failed else round(energy * rate, 2)

                sess = ChargingSession(
                    session_code=f"SES-HIST-{idx + 1:04d}",
                    charger_id=ch.id,
                    user_id=admin.id,
                    start_time=start_dt,
                    end_time=end_dt,
                    duration_seconds=duration_min * 60,
                    energy_delivered_kwh=energy,
                    peak_power_kw=ch.rated_power_kw,
                    unit_price=rate,
                    total_amount=total_amt,
                    status=status_val,
                )
                db.add(sess)
                db.flush()

                if not is_failed:
                    payment = Payment(
                        charging_session_id=sess.id,
                        amount=total_amt,
                        currency="INR",
                        payment_method="simulated_card",
                        status="completed",
                        transaction_reference=f"TXN-HIST-{idx + 1:04d}",
                        created_at=end_dt,
                    )
                    db.add(payment)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
    print("Database seeding completed.")
