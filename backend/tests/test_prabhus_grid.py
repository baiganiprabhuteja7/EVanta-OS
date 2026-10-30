import pytest
from app.core.config import settings


def test_unauthorized_access_rejected_on_all_station_apis(client):
    """Direct URL or API access while unauthenticated returns 401."""
    protected_paths = [
        "/api/v1/station",
        "/api/v1/stations",
        "/api/v1/chargers",
        "/api/v1/sessions",
        "/api/v1/analytics/overview",
        "/api/v1/analytics/dashboard",
        "/api/v1/station/settings",
        "/api/v1/settings",
        "/api/v1/alerts",
        "/api/v1/demo/status",
        "/api/v1/demo/chargers",
    ]
    for path in protected_paths:
        res = client.get(path)
        assert res.status_code == 401, f"Expected 401 on {path}, got {res.status_code}"


def test_single_station_data_isolation(client, admin_headers):
    """Test that exactly one station in Hyderabad exists and queries are strictly isolated."""
    res = client.get("/api/v1/station", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["station_code"] == settings.STATION_CODE
    assert data["city"] == "Hyderabad"
    assert data["state"] == "Telangana"
    assert data["country"] == "India"

    # Multi-station query check: /stations must only return the single Hyderabad station
    list_res = client.get("/api/v1/stations", headers=admin_headers)
    assert list_res.status_code == 200
    stations = list_res.json()
    assert len(stations) == 1
    assert stations[0]["station_code"] == settings.STATION_CODE


def test_demo_source_labelling(client, admin_headers):
    """Verify DEMO / SIMULATED data labels on all authorized responses."""
    st_res = client.get("/api/v1/station", headers=admin_headers)
    assert "data_source" in st_res.json()
    assert "SIMULATED" in st_res.json()["data_source"]
    assert "SIMULATED" in st_res.json()["disclaimer"]

    chargers_res = client.get("/api/v1/chargers", headers=admin_headers)
    assert len(chargers_res.json()) > 0
    for ch in chargers_res.json():
        assert "SIMULATED" in ch["data_source"]

    analytics_res = client.get("/api/v1/analytics/overview", headers=admin_headers)
    assert "SIMULATED" in analytics_res.json()["data_source"]


def test_charger_capacity_and_electrical_correctness(client, admin_headers):
    """Validate installed capacity = sum of charger ratings and power <= rated capacity."""
    chargers_res = client.get("/api/v1/chargers", headers=admin_headers)
    assert chargers_res.status_code == 200
    chargers = chargers_res.json()

    total_rated = sum(ch["rated_power_kw"] for ch in chargers)
    assert total_rated > 0

    st_res = client.get("/api/v1/station", headers=admin_headers)
    st_data = st_res.json()
    assert abs(st_data["installed_capacity_kw"] - total_rated) < 0.5

    assert st_data["current_charging_power_kw"] <= st_data["installed_capacity_kw"]
    assert st_data["current_charging_power_kw"] >= 0.0

    for ch in chargers:
        assert ch["current_power_kw"] <= ch["rated_power_kw"]


def test_charger_crud_and_rbac(client, admin_headers, manager_headers, viewer_headers):
    """Test charger management: Admin allowed, Manager/Viewer forbidden."""
    new_code = "EV-AC-TEST"
    create_payload = {
        "charger_code": new_code,
        "charger_type": "AC",
        "connector_type": "Type 2",
        "rated_power_kw": 22.0,
        "voltage": 400.0,
        "status": "Available",
    }

    # 1. Read-only official cannot create charger (403)
    viewer_res = client.post("/api/v1/chargers", json=create_payload, headers=viewer_headers)
    assert viewer_res.status_code == 403

    # 2. Station Manager cannot create charger (403)
    manager_res = client.post("/api/v1/chargers", json=create_payload, headers=manager_headers)
    assert manager_res.status_code == 403

    # 3. Administrator can create charger (201)
    admin_create = client.post("/api/v1/chargers", json=create_payload, headers=admin_headers)
    assert admin_create.status_code == 201

    # 4. Clean up / delete charger (Admin only)
    admin_del = client.delete(f"/api/v1/chargers/{new_code}", headers=admin_headers)
    assert admin_del.status_code == 200


def test_session_state_transitions_and_roles(client, admin_headers, manager_headers, viewer_headers):
    """Test sessions: Manager & Admin can operate, Viewer cannot."""
    chargers = client.get("/api/v1/chargers?status=Available", headers=admin_headers).json()
    assert len(chargers) > 0
    charger_code = chargers[0]["charger_code"]

    # 1. Read-only official cannot start session (403)
    viewer_start = client.post(
        "/api/v1/sessions",
        json={"charger_code": charger_code, "unit_price": 18.5},
        headers=viewer_headers,
    )
    assert viewer_start.status_code == 403

    # 2. Manager starts session (201)
    manager_start = client.post(
        "/api/v1/sessions",
        json={"charger_code": charger_code, "unit_price": 18.5},
        headers=manager_headers,
    )
    assert manager_start.status_code == 201
    sess_id = manager_start.json()["session_code"]

    # 3. Read-only official cannot complete session (403)
    viewer_complete = client.post(
        f"/api/v1/sessions/{sess_id}/complete",
        json={"energy_delivered_kwh": 10.0},
        headers=viewer_headers,
    )
    assert viewer_complete.status_code == 403

    # 4. Manager completes session (200)
    manager_complete = client.post(
        f"/api/v1/sessions/{sess_id}/complete",
        json={"energy_delivered_kwh": 10.0},
        headers=manager_headers,
    )
    assert manager_complete.status_code == 200
    assert manager_complete.json()["status"] == "Completed"


def test_station_settings_and_demo_reset_rbac(client, admin_headers, manager_headers):
    """Admin can update settings and reset demo; Manager cannot."""
    new_address = "Madhapur Cyber Towers Junction, Hyderabad, Telangana 500081"

    # Manager cannot update settings (403)
    mgr_patch = client.patch(
        "/api/v1/station/settings",
        json={"station_address": new_address, "tariff_per_kwh": 19.0},
        headers=manager_headers,
    )
    assert mgr_patch.status_code == 403

    # Admin can update settings (200)
    admin_patch = client.patch(
        "/api/v1/station/settings",
        json={"station_address": new_address, "tariff_per_kwh": 19.0},
        headers=admin_headers,
    )
    assert admin_patch.status_code == 200
    assert admin_patch.json()["tariff_per_kwh"] == 19.0

    # Manager cannot reset demo data (403)
    mgr_reset = client.post("/api/v1/demo/reset", headers=manager_headers)
    assert mgr_reset.status_code == 403

    # Admin can reset demo data (200)
    admin_reset = client.post("/api/v1/demo/reset", headers=admin_headers)
    assert admin_reset.status_code == 200
