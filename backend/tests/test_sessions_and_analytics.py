import uuid


def test_charging_session_lifecycle_and_payment(client):
    # Find an available charger from seeded data
    chargers_res = client.get("/api/v1/chargers?status=Available")
    assert chargers_res.status_code == 200
    available = chargers_res.json()
    assert len(available) > 0, "Expected at least one available charger"
    target_charger = available[0]

    # Start session on this charger
    start_res = client.post(
        "/api/v1/sessions",
        json={"charger_id": target_charger["id"], "unit_price": 25.0},
    )
    assert start_res.status_code == 201
    session_data = start_res.json()
    assert session_data["status"] == "Ongoing"
    session_id = session_data["id"]

    # Verify charger is now Charging
    ch_check = client.get(f"/api/v1/chargers/{target_charger['id']}")
    assert ch_check.status_code == 200
    assert ch_check.json()["status"] == "Charging"

    # Complete session with explicit delivered energy
    complete_res = client.post(
        f"/api/v1/sessions/{session_id}/complete",
        json={"energy_delivered_kwh": 30.5, "peak_power_kw": 50.0},
    )
    assert complete_res.status_code == 200
    completed_data = complete_res.json()
    assert completed_data["status"] == "Completed"
    assert completed_data["energy_delivered_kwh"] == 30.5
    assert completed_data["total_amount"] == 30.5 * 25.0

    # Ensure completed session cannot be completed again
    repeat_res = client.post(
        f"/api/v1/sessions/{session_id}/complete",
        json={"energy_delivered_kwh": 10.0},
    )
    assert repeat_res.status_code == 400

    # Verify charger is now Available again
    ch_check2 = client.get(f"/api/v1/chargers/{target_charger['id']}")
    assert ch_check2.status_code == 200
    assert ch_check2.json()["status"] == "Available"

    # Verify payment record was automatically created
    payments_res = client.get("/api/v1/payments")
    assert payments_res.status_code == 200
    payments = payments_res.json()
    matching_payment = next((p for p in payments if p["charging_session_id"] == session_id), None)
    assert matching_payment is not None
    assert matching_payment["amount"] == 30.5 * 25.0


def test_dashboard_and_business_analytics(client):
    dash_res = client.get("/api/v1/analytics/dashboard")
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["total_stations"] >= 8
    assert dash_data["total_chargers"] >= 40

    energy_res = client.get("/api/v1/analytics/energy?days=14")
    assert energy_res.status_code == 200
    assert len(energy_res.json()) > 0

    biz_res = client.get("/api/v1/analytics/business")
    assert biz_res.status_code == 200
    assert "total_revenue" in biz_res.json()
    assert "estimated_gross_margin" in biz_res.json()


def test_workspace_settings(client):
    get_res = client.get("/api/v1/settings")
    assert get_res.status_code == 200
    assert get_res.json()["currency"] == "INR"

    update_res = client.put(
        "/api/v1/settings",
        json={"electricity_cost_per_kwh": 9.25, "compact_tables": True},
    )
    assert update_res.status_code == 200
    assert update_res.json()["electricity_cost_per_kwh"] == 9.25
    assert update_res.json()["compact_tables"] is True
