import uuid


def test_stations_crud_and_metrics(client):
    unique_code = f"EV-TST-{uuid.uuid4().hex[:4].upper()}"

    # 1. Create Station
    create_payload = {
        "station_code": unique_code,
        "station_name": "Test Supercharge Hub",
        "address": "100 MG Road, Bengaluru 560001",
        "city": "Bengaluru",
        "state": "Karnataka",
        "status": "Online",
        "chargers_count": 3,
    }
    create_res = client.post("/api/v1/stations", json=create_payload)
    assert create_res.status_code == 201
    station_data = create_res.json()
    assert station_data["station_code"] == unique_code
    assert station_data["chargers"] == 3
    station_id = station_data["id"]

    # 2. Get Station by code and by ID
    get_by_code = client.get(f"/api/v1/stations/{unique_code}")
    assert get_by_code.status_code == 200
    assert len(get_by_code.json()["charger_list"]) == 3

    get_by_id = client.get(f"/api/v1/stations/{station_id}")
    assert get_by_id.status_code == 200

    # 3. List Stations with search
    list_res = client.get(f"/api/v1/stations?search={unique_code}")
    assert list_res.status_code == 200
    assert any(s["station_code"] == unique_code for s in list_res.json())

    # 4. Add Charger to Station
    new_charger_code = f"{unique_code.replace('EV-', 'CH-')}-04"
    charger_payload = {
        "charger_code": new_charger_code,
        "charger_type": "DC",
        "connector_type": "CCS2",
        "rated_power_kw": 120.0,
        "voltage": 600.0,
        "status": "Available",
    }
    add_ch_res = client.post(f"/api/v1/stations/{unique_code}/chargers", json=charger_payload)
    assert add_ch_res.status_code == 201
    assert add_ch_res.json()["charger_code"] == new_charger_code

    # 5. Update Station status
    update_res = client.patch(
        f"/api/v1/stations/{unique_code}",
        json={"status": "Maintenance"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "Maintenance"

    # 6. Delete Station
    del_res = client.delete(f"/api/v1/stations/{unique_code}")
    assert del_res.status_code == 200

    # 7. Verify deletion
    not_found_res = client.get(f"/api/v1/stations/{unique_code}")
    assert not_found_res.status_code == 404
