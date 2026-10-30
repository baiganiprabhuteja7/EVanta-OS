import pytest


def test_sessions_listing_and_filtering(client, manager_headers):
    """Authenticated officials can view and filter sessions."""
    res = client.get("/api/v1/sessions", headers=manager_headers)
    assert res.status_code == 200
    sessions = res.json()
    assert isinstance(sessions, list)

    # Filter by status
    ongoing_res = client.get("/api/v1/sessions?status=Ongoing", headers=manager_headers)
    assert ongoing_res.status_code == 200
    for s in ongoing_res.json():
        assert s["status"] == "Ongoing"


def test_dashboard_and_business_analytics(client, viewer_headers):
    """Officials can view analytics overview and business metrics."""
    dash_res = client.get("/api/v1/analytics/dashboard", headers=viewer_headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["installed_capacity_kw"] > 0
    assert dash_data["current_charging_power_kw"] >= 0

    biz_res = client.get("/api/v1/analytics/business", headers=viewer_headers)
    assert biz_res.status_code == 200
    biz_data = biz_res.json()
    assert "estimated_today_cost" in biz_data


def test_station_settings_rbac(client, admin_headers, viewer_headers):
    """Viewers can inspect settings; only Administrators can modify them."""
    # View settings
    get_res = client.get("/api/v1/settings", headers=viewer_headers)
    assert get_res.status_code == 200
    assert get_res.json()["currency"] == "INR"

    # Viewer cannot modify settings (403)
    viewer_put = client.put(
        "/api/v1/settings",
        json={"tariff_per_kwh": 19.5, "electricity_cost_per_kwh": 8.0},
        headers=viewer_headers,
    )
    assert viewer_put.status_code == 403

    # Admin can modify settings (200)
    admin_put = client.put(
        "/api/v1/settings",
        json={"tariff_per_kwh": 19.5, "electricity_cost_per_kwh": 8.0},
        headers=admin_headers,
    )
    assert admin_put.status_code == 200
    assert admin_put.json()["tariff_per_kwh"] == 19.5
