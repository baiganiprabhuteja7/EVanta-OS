from typing import List, Optional
from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_stations: int
    online_stations: int
    offline_stations: int
    maintenance_stations: int
    faulted_stations: int
    total_chargers: int
    active_chargers: int
    available_chargers: int
    total_energy_delivered: float
    todays_revenue: float
    overall_utilization: int


class EnergyHistoryItem(BaseModel):
    date: str
    station_id: str
    station_name: str
    energy: float
    peak_power: float
    average_power: float
    ac_energy: float
    dc_energy: float


class BusinessAnalyticsResponse(BaseModel):
    total_revenue: float
    total_energy_kwh: float
    estimated_energy_cost: float
    estimated_gross_margin: float
    operating_expenses: float
    estimated_net_benefit: float
