from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.models.user import User


def test_station_crud_and_safeguards(client: TestClient, admin_headers: dict):
    # 1. List stations
    r = client.get("/api/v1/stations", headers=admin_headers)
    assert r.status_code == 200
    stations = r.json()
    assert len(stations) >= 1
    default_id = stations[0]["id"]

    # 2. Create new station
    new_station_payload = {
        "station_code": "SEC-HYD-02",
        "station_name": "Secunderabad Hub Station",
        "owner_name": "Prabhu Enterprises",
        "address": "MG Road, Secunderabad, Telangana 500003",
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "India",
        "postal_code": "500003",
        "status": "Online",
        "initial_investment": 3200000.0,
        "monthly_fixed_cost": 22000.0,
    }
    r = client.post("/api/v1/stations", json=new_station_payload, headers=admin_headers)
    assert r.status_code == 201
    created = r.json()
    assert created["station_code"] == "SEC-HYD-02"
    assert created["initial_investment"] == 3200000.0
    created_id = created["id"]

    # 3. Update station
    update_payload = {
        "station_name": "Secunderabad Express Hub",
        "monthly_fixed_cost": 25000.0,
    }
    r = client.patch(f"/api/v1/stations/{created_id}", json=update_payload, headers=admin_headers)
    assert r.status_code == 200
    updated = r.json()
    assert updated["station_name"] == "Secunderabad Express Hub"

    # 4. Delete station
    r = client.delete(f"/api/v1/stations/{created_id}", headers=admin_headers)
    assert r.status_code == 200


def test_maintenance_records_crud(client: TestClient, admin_headers: dict, manager_headers: dict):
    # Get a station and charger
    st_r = client.get("/api/v1/stations", headers=admin_headers)
    station_id = st_r.json()[0]["id"]

    ch_r = client.get(f"/api/v1/chargers?station_id={station_id}", headers=admin_headers)
    chargers = ch_r.json()
    charger_id = chargers[0]["id"] if chargers else None

    # 1. Create maintenance record
    payload = {
        "station_id": station_id,
        "charger_id": charger_id,
        "equipment_name": "CCS2 Dispenser Contact Pin",
        "issue_description": "Wear on locking pin mechanism, requires cleaning and calibration",
        "severity": "Medium",
        "status": "Reported",
        "cost": 1500.0,
        "technician_name": "Rajesh Kumar",
    }
    r = client.post("/api/v1/maintenance", json=payload, headers=manager_headers)
    assert r.status_code == 201
    maint = r.json()
    maint_id = maint["id"]
    assert maint["equipment_name"] == "CCS2 Dispenser Contact Pin"

    # 2. Update maintenance record
    upd = {
        "status": "Completed",
        "resolution_notes": "Pins cleaned and calibrated. Verified 100% operational.",
    }
    r = client.patch(f"/api/v1/maintenance/{maint_id}", json=upd, headers=manager_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "Completed"

    # 3. List maintenance
    r = client.get("/api/v1/maintenance", headers=admin_headers)
    assert r.status_code == 200
    assert any(m["id"] == maint_id for m in r.json())


def test_station_expenses_and_financial_analytics(client: TestClient, admin_headers: dict):
    st_r = client.get("/api/v1/stations", headers=admin_headers)
    station_id = st_r.json()[0]["id"]

    # 1. Record station expense
    exp_payload = {
        "station_id": station_id,
        "category": "Site Lease",
        "amount": 25000.0,
        "description": "Monthly site parking canopy ground rent",
    }
    r = client.post("/api/v1/expenses", json=exp_payload, headers=admin_headers)
    assert r.status_code == 201
    exp_id = r.json()["id"]

    # 2. Get financial report
    r = client.get("/api/v1/analytics/financials", headers=admin_headers)
    assert r.status_code == 200
    fin = r.json()
    assert "total_charging_revenue" in fin
    assert "total_electricity_expense" in fin
    assert "total_operating_expenses" in fin
    assert "gross_contribution" in fin
    assert "net_operating_profit" in fin
    assert "roi_percentage" in fin
    assert len(fin["stations_financials"]) >= 1
    assert len(fin["chargers_financials"]) >= 1

    # Cleanup expense
    client.delete(f"/api/v1/expenses/{exp_id}", headers=admin_headers)
