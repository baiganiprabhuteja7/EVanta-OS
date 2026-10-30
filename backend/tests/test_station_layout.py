import pytest
from fastapi.testclient import TestClient


def test_station_layout_unauthenticated_rejected(client: TestClient):
    """Unauthenticated requests must be rejected with 401."""
    resp = client.get("/api/v1/station/layout")
    assert resp.status_code == 401


def test_station_layout_viewer_forbidden(client: TestClient, viewer_headers):
    """Read-Only Officials (viewers) cannot access the virtual station map."""
    resp = client.get("/api/v1/station/layout", headers=viewer_headers)
    assert resp.status_code == 403
    assert "Administrator access required" in resp.json().get("detail", "")


def test_station_layout_manager_forbidden(client: TestClient, manager_headers):
    """Station Managers cannot access the virtual station map."""
    resp = client.get("/api/v1/station/layout", headers=manager_headers)
    assert resp.status_code == 403
    assert "Administrator access required" in resp.json().get("detail", "")


def test_station_layout_admin_success(client: TestClient, admin_headers):
    """Administrators can successfully load the full virtual station layout."""
    resp = client.get("/api/v1/station/layout", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] >= 1
    assert "SAMPLE LAYOUT" in data["disclaimer"]
    assert "layout_data" in data
    assert "boundary" in data["layout_data"]
    assets = data["layout_data"]["assets"]
    assert len(assets) > 0

    # Verify charger types exist
    types = {a["type"] for a in assets}
    assert "charger_ac" in types
    assert "charger_dc" in types
    assert "parking_bay" in types
    assert "utility_room" in types
    assert "transformer" in types


def test_station_layout_update_permissions_and_concurrency(
    client: TestClient, admin_headers, viewer_headers, manager_headers
):
    """Verify update permissions and optimistic concurrency."""
    # 1. Fetch current layout as admin
    resp = client.get("/api/v1/station/layout", headers=admin_headers)
    assert resp.status_code == 200
    layout = resp.json()
    current_ver = layout["version"]

    payload = {
        "version": current_ver,
        "name": "Customized Hyderabad Station Layout v2",
        "scale_ratio": 1.25,
        "scale_verified": False,
        "layout_data": layout["layout_data"],
    }

    # 2. Non-admin update attempts rejected with 403
    resp_viewer = client.put("/api/v1/station/layout", json=payload, headers=viewer_headers)
    assert resp_viewer.status_code == 403

    resp_manager = client.put("/api/v1/station/layout", json=payload, headers=manager_headers)
    assert resp_manager.status_code == 403

    # 3. Admin update succeeds and increments version
    resp_admin = client.put("/api/v1/station/layout", json=payload, headers=admin_headers)
    assert resp_admin.status_code == 200
    updated = resp_admin.json()
    assert updated["version"] == current_ver + 1
    assert updated["name"] == "Customized Hyderabad Station Layout v2"

    # 4. Outdated version update rejected with 409 Conflict
    resp_conflict = client.put("/api/v1/station/layout", json=payload, headers=admin_headers)
    assert resp_conflict.status_code == 409
    assert "Conflict" in resp_conflict.json().get("detail", "")


def test_station_layout_reset(client: TestClient, admin_headers, viewer_headers):
    """Administrator can reset the layout back to canonical sample."""
    # Viewer rejected
    r_view = client.post("/api/v1/station/layout/reset", headers=viewer_headers)
    assert r_view.status_code == 403

    # Admin succeeds
    r_reset = client.post("/api/v1/station/layout/reset", headers=admin_headers)
    assert r_reset.status_code == 200
    data = r_reset.json()
    assert "SAMPLE LAYOUT" in data["disclaimer"]
    assert data["scale_verified"] is False
