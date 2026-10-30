import copy
from datetime import datetime, timezone
from typing import Any, Dict, List

DEMO_DISCLAIMER = "DEMO PROJECT — SIMULATED DATA — NOT CONNECTED TO REAL STATION HARDWARE"
DEMO_DATA_SOURCE = "SIMULATED_DEMO_SOURCE"

INITIAL_DEMO_STATION: Dict[str, Any] = {
    "id": 9999,
    "station_code": "PRABHU-DEMO-01",
    "station_name": "Prabhu's Grid [Demo Prototype]",
    "owner_name": "Prabhu (Demo Mode)",
    "city": "Hyderabad",
    "state": "Telangana",
    "country": "India",
    "address": "HITEC City / Madhapur Corridor, Hyderabad, Telangana 500081, India",
    "status": "Online",
    "installed_capacity_kw": 270.4,
    "current_charging_power_kw": 64.53,
    "energy_today_kwh": 92.4,
    "energy_month_kwh": 1339.8,
    "total_chargers": 6,
    "active_chargers": 2,
    "available_chargers": 3,
    "faulted_chargers": 1,
    "offline_chargers": 0,
    "utilization_rate": 40.0,
    "tariff_per_kwh": 18.5,
    "estimated_today_cost": 1709.4,
    "is_demo": True,
    "data_source": DEMO_DATA_SOURCE,
    "disclaimer": DEMO_DISCLAIMER,
    "created_at": datetime.now(timezone.utc).isoformat(),
    "updated_at": datetime.now(timezone.utc).isoformat(),
}

INITIAL_DEMO_CHARGERS: List[Dict[str, Any]] = [
    {
        "id": 101,
        "charger_code": "PG-AC-01",
        "station_id": 9999,
        "station_code": "PRABHU-DEMO-01",
        "charger_type": "AC",
        "connector_type": "Type 2",
        "rated_power_kw": 7.4,
        "voltage": 230.0,
        "current_amp": 0.0,
        "power_factor": 0.94,
        "status": "Available",
        "current_power_kw": 0.0,
        "energy_delivered_kwh": 312.4,
        "current_session": None,
        "latest_reading_time": datetime.now(timezone.utc).isoformat(),
        "is_demo": True,
        "data_source": DEMO_DATA_SOURCE,
        "disclaimer": DEMO_DISCLAIMER,
    },
    {
        "id": 102,
        "charger_code": "PG-AC-02",
        "station_id": 9999,
        "station_code": "PRABHU-DEMO-01",
        "charger_type": "AC",
        "connector_type": "Type 2",
        "rated_power_kw": 22.0,
        "voltage": 400.0,
        "current_amp": 28.5,
        "power_factor": 0.94,
        "status": "Charging",
        "current_power_kw": 18.56,
        "energy_delivered_kwh": 489.1,
        "current_session": "SES-DEMO-02",
        "latest_reading_time": datetime.now(timezone.utc).isoformat(),
        "is_demo": True,
        "data_source": DEMO_DATA_SOURCE,
        "disclaimer": DEMO_DISCLAIMER,
    },
    {
        "id": 103,
        "charger_code": "PG-AC-03",
        "station_id": 9999,
        "station_code": "PRABHU-DEMO-01",
        "charger_type": "AC",
        "connector_type": "Type 2",
        "rated_power_kw": 11.0,
        "voltage": 400.0,
        "current_amp": 0.0,
        "power_factor": 0.94,
        "status": "Faulted",
        "current_power_kw": 0.0,
        "energy_delivered_kwh": 142.0,
        "current_session": None,
        "latest_reading_time": datetime.now(timezone.utc).isoformat(),
        "is_demo": True,
        "data_source": DEMO_DATA_SOURCE,
        "disclaimer": DEMO_DISCLAIMER,
    },
    {
        "id": 104,
        "charger_code": "PG-DC-01",
        "station_id": 9999,
        "station_code": "PRABHU-DEMO-01",
        "charger_type": "DC",
        "connector_type": "CCS2",
        "rated_power_kw": 60.0,
        "voltage": 420.0,
        "current_amp": 109.5,
        "power_factor": 1.0,
        "status": "Charging",
        "current_power_kw": 45.97,
        "energy_delivered_kwh": 1280.5,
        "current_session": "SES-DEMO-01",
        "latest_reading_time": datetime.now(timezone.utc).isoformat(),
        "is_demo": True,
        "data_source": DEMO_DATA_SOURCE,
        "disclaimer": DEMO_DISCLAIMER,
    },
    {
        "id": 105,
        "charger_code": "PG-DC-02",
        "station_id": 9999,
        "station_code": "PRABHU-DEMO-01",
        "charger_type": "DC",
        "connector_type": "CCS2",
        "rated_power_kw": 120.0,
        "voltage": 500.0,
        "current_amp": 0.0,
        "power_factor": 1.0,
        "status": "Available",
        "current_power_kw": 0.0,
        "energy_delivered_kwh": 2410.0,
        "current_session": None,
        "latest_reading_time": datetime.now(timezone.utc).isoformat(),
        "is_demo": True,
        "data_source": DEMO_DATA_SOURCE,
        "disclaimer": DEMO_DISCLAIMER,
    },
    {
        "id": 106,
        "charger_code": "PG-DC-03",
        "station_id": 9999,
        "station_code": "PRABHU-DEMO-01",
        "charger_type": "DC",
        "connector_type": "CHAdeMO",
        "rated_power_kw": 50.0,
        "voltage": 400.0,
        "current_amp": 0.0,
        "power_factor": 1.0,
        "status": "Available",
        "current_power_kw": 0.0,
        "energy_delivered_kwh": 890.2,
        "current_session": None,
        "latest_reading_time": datetime.now(timezone.utc).isoformat(),
        "is_demo": True,
        "data_source": DEMO_DATA_SOURCE,
        "disclaimer": DEMO_DISCLAIMER,
    },
]

INITIAL_DEMO_SESSIONS: List[Dict[str, Any]] = [
    {
        "id": 201,
        "session_code": "SES-DEMO-01",
        "charger_code": "PG-DC-01",
        "charger_type": "DC",
        "connector_type": "CCS2",
        "start_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end_time": None,
        "status": "Ongoing",
        "duration_minutes": 35,
        "energy_delivered_kwh": 26.8,
        "peak_power_kw": 58.2,
        "unit_price": 18.5,
        "total_amount": 495.8,
        "is_demo": True,
        "data_source": DEMO_DATA_SOURCE,
        "disclaimer": DEMO_DISCLAIMER,
    },
    {
        "id": 202,
        "session_code": "SES-DEMO-02",
        "charger_code": "PG-AC-02",
        "charger_type": "AC",
        "connector_type": "Type 2",
        "start_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end_time": None,
        "status": "Ongoing",
        "duration_minutes": 50,
        "energy_delivered_kwh": 14.5,
        "peak_power_kw": 21.0,
        "unit_price": 18.5,
        "total_amount": 268.25,
        "is_demo": True,
        "data_source": DEMO_DATA_SOURCE,
        "disclaimer": DEMO_DISCLAIMER,
    },
    {
        "id": 203,
        "session_code": "SES-DEMO-03",
        "charger_code": "PG-DC-02",
        "charger_type": "DC",
        "connector_type": "CCS2",
        "start_time": "2026-10-24T14:15:00Z",
        "end_time": "2026-10-24T15:05:00Z",
        "status": "Completed",
        "duration_minutes": 50,
        "energy_delivered_kwh": 68.4,
        "peak_power_kw": 114.5,
        "unit_price": 18.5,
        "total_amount": 1265.4,
        "is_demo": True,
        "data_source": DEMO_DATA_SOURCE,
        "disclaimer": DEMO_DISCLAIMER,
    },
    {
        "id": 204,
        "session_code": "SES-DEMO-04",
        "charger_code": "PG-AC-01",
        "charger_type": "AC",
        "connector_type": "Type 2",
        "start_time": "2026-10-24T11:00:00Z",
        "end_time": "2026-10-24T13:30:00Z",
        "status": "Completed",
        "duration_minutes": 150,
        "energy_delivered_kwh": 18.2,
        "peak_power_kw": 7.4,
        "unit_price": 18.5,
        "total_amount": 336.7,
        "is_demo": True,
        "data_source": DEMO_DATA_SOURCE,
        "disclaimer": DEMO_DISCLAIMER,
    },
]

INITIAL_DEMO_ALERTS: List[Dict[str, Any]] = [
    {
        "id": 301,
        "severity": "Warning",
        "code": "WARN_OVERVOLTAGE_AC03",
        "title": "Grid Voltage Fluctuation",
        "message": "Charger PG-AC-03 reported line voltage spike 428V (> threshold 420V). Connector isolated.",
        "charger_code": "PG-AC-03",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_demo": True,
        "data_source": DEMO_DATA_SOURCE,
        "disclaimer": DEMO_DISCLAIMER,
    },
    {
        "id": 302,
        "severity": "Info",
        "code": "INFO_MAINTENANCE_DUE",
        "title": "Scheduled Filter Inspection",
        "message": "PG-DC-02 intake airflow dust filter inspection scheduled for next weekly cycle.",
        "charger_code": "PG-DC-02",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_demo": True,
        "data_source": DEMO_DATA_SOURCE,
        "disclaimer": DEMO_DISCLAIMER,
    },
]


class DemoService:
    """
    Isolated Demo Service for Evanta OS / Prabhu's Grid prototype.
    Maintains simulated in-memory state separate from production database operations.
    """

    _station = copy.deepcopy(INITIAL_DEMO_STATION)
    _chargers = copy.deepcopy(INITIAL_DEMO_CHARGERS)
    _sessions = copy.deepcopy(INITIAL_DEMO_SESSIONS)
    _alerts = copy.deepcopy(INITIAL_DEMO_ALERTS)

    @classmethod
    def get_station(cls) -> Dict[str, Any]:
        return copy.deepcopy(cls._station)

    @classmethod
    def get_chargers(cls) -> List[Dict[str, Any]]:
        return copy.deepcopy(cls._chargers)

    @classmethod
    def get_sessions(cls) -> List[Dict[str, Any]]:
        return copy.deepcopy(cls._sessions)

    @classmethod
    def get_alerts(cls) -> List[Dict[str, Any]]:
        return copy.deepcopy(cls._alerts)

    @classmethod
    def get_analytics(cls) -> Dict[str, Any]:
        # 24-hour deterministic hourly load curve for demo
        hourly_trends = []
        for i in range(24):
            is_peak = 18 <= i <= 22
            is_day = 9 <= i <= 17
            power = 85.0 + (i * 3) % 25 if is_peak else (45.0 + (i * 2) % 30 if is_day else 12.0 + (i % 8))
            hourly_trends.append({
                "hour": i,
                "power_kw": round(power, 2),
                "energy_kwh": round(power * 0.95, 2),
                "data_source": DEMO_DATA_SOURCE,
                "disclaimer": DEMO_DISCLAIMER,
            })

        # 14 days trends
        daily_trends = []
        for d in range(14):
            energy = 210.0 + ((d * 19 + 7) % 85)
            peak = 88.0 + ((d * 7 + 13) % 45)
            daily_trends.append({
                "date": f"2026-10-{11 + d:02d}",
                "energy_delivered_kwh": round(energy, 1),
                "peak_power_kw": round(peak, 1),
                "active_sessions": 12 + (d % 6),
                "estimated_revenue": round(energy * 18.5, 2),
                "data_source": DEMO_DATA_SOURCE,
                "disclaimer": DEMO_DISCLAIMER,
            })

        return {
            "station_code": cls._station["station_code"],
            "station_name": cls._station["station_name"],
            "installed_capacity_kw": cls._station["installed_capacity_kw"],
            "current_charging_power_kw": cls._station["current_charging_power_kw"],
            "energy_today_kwh": cls._station["energy_today_kwh"],
            "utilization_rate": cls._station["utilization_rate"],
            "hourly_trends": hourly_trends,
            "daily_trends": daily_trends,
            "is_demo": True,
            "data_source": DEMO_DATA_SOURCE,
            "disclaimer": DEMO_DISCLAIMER,
        }

    @classmethod
    def reset_demo(cls) -> Dict[str, Any]:
        cls._station = copy.deepcopy(INITIAL_DEMO_STATION)
        cls._chargers = copy.deepcopy(INITIAL_DEMO_CHARGERS)
        cls._sessions = copy.deepcopy(INITIAL_DEMO_SESSIONS)
        cls._alerts = copy.deepcopy(INITIAL_DEMO_ALERTS)
        return {
            "status": "success",
            "message": "Demo data environment successfully reset to initial simulated baseline.",
            "is_demo": True,
            "disclaimer": DEMO_DISCLAIMER,
        }
