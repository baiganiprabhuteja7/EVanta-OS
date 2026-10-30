def test_demo_requires_authentication(client, admin_headers):
    """Demo mode must not bypass authentication."""
    # 1. Unauthenticated demo access must return 401
    assert client.get("/api/v1/demo/status").status_code == 401
    assert client.get("/api/v1/demo/station").status_code == 401
    assert client.get("/api/v1/demo/chargers").status_code == 401

    # 2. Authenticated demo access succeeds
    status_res = client.get("/api/v1/demo/status", headers=admin_headers)
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["is_demo"] is True
    assert status_data["status"] == "ready"


def test_demo_readings_labeled_simulated(client, admin_headers):
    """Demo readings and responses are explicitly labeled simulated."""
    for path in ["/api/v1/demo/status", "/api/v1/demo/station", "/api/v1/demo/analytics"]:
        res = client.get(path, headers=admin_headers)
        assert res.status_code == 200
        payload = res.json()
        assert payload.get("is_demo") is True
        assert "SIMULATED" in payload.get("data_source", "")
        assert "SIMULATED DATA" in payload.get("disclaimer", "")

    chargers = client.get("/api/v1/demo/chargers", headers=admin_headers).json()
    for ch in chargers:
        assert ch["is_demo"] is True
        assert "SIMULATED" in ch["data_source"]
        assert "SIMULATED DATA" in ch["disclaimer"]


def test_demo_users_cannot_access_protected_apis_without_token(client):
    """Unauthenticated users cannot access protected APIs."""
    assert client.get("/api/v1/users").status_code == 401
    assert client.get("/api/v1/users/me").status_code == 401
    assert client.post("/api/v1/auth/logout").status_code == 401


def test_reset_demo_rbac(client, admin_headers, viewer_headers):
    """Reset Demo restores initial state for Admin, forbidden for Viewer."""
    # Viewer cannot reset demo (403)
    viewer_res = client.post("/api/v1/demo/reset", headers=viewer_headers)
    assert viewer_res.status_code == 403

    # Admin can reset demo (200)
    reset_res = client.post("/api/v1/demo/reset", headers=admin_headers)
    assert reset_res.status_code == 200
    data = reset_res.json()
    assert data["status"] == "success"

    chargers_res = client.get("/api/v1/demo/chargers", headers=admin_headers)
    assert chargers_res.status_code == 200
    chargers = chargers_res.json()
    assert len(chargers) == 6
    assert any(c["charger_type"] == "AC" for c in chargers)
    assert any(c["charger_type"] == "DC" for c in chargers)
