import pytest
from app.core.config import settings


def test_station_single_isolation(client, admin_headers):
    """Only the single configured Hyderabad station exists."""
    res = client.get("/api/v1/station", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["city"] == "Hyderabad"
    assert res.json()["station_code"] == settings.STATION_CODE

    chargers_res = client.get("/api/v1/chargers", headers=admin_headers)
    assert chargers_res.status_code == 200
    chargers = chargers_res.json()
    assert len(chargers) >= 6
    assert any(c["charger_type"] == "AC" for c in chargers)
    assert any(c["charger_type"] == "DC" for c in chargers)
