from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class HourlyTrendPoint(BaseModel):
    timestamp: datetime
    hour_label: str
    power_kw: float
    energy_kwh: float
    active_chargers: int
    data_source: str = "SIMULATED_DEMO_SOURCE"


class DailyTrendPoint(BaseModel):
    date_label: str
    energy_kwh: float
    total_sessions: int
    estimated_revenue: float
    electricity_expense: float = 0.0
    operating_profit: float = 0.0
    data_source: str = "SIMULATED_DEMO_SOURCE"


class RecentActivityItem(BaseModel):
    id: str
    type: str  # session_start, session_end, alert, maintenance
    timestamp: datetime
    title: str
    description: str
    status: str
    badge_color: Optional[str] = None


class StationFinancialSummary(BaseModel):
    station_id: int
    station_code: str
    station_name: str
    total_chargers: int
    total_sessions: int
    energy_delivered_kwh: float
    charging_revenue: float
    electricity_expense: float
    operating_expenses: float
    operating_profit: float
    initial_investment: float
    roi_percentage: float


class ChargerFinancialSummary(BaseModel):
    charger_id: int
    charger_code: str
    station_name: str
    charger_type: str
    connector_type: str
    total_sessions: int
    energy_delivered_kwh: float
    charging_revenue: float
    electricity_expense: float
    operating_profit: float


class FinancialReportResponse(BaseModel):
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    tariff_per_kwh: float
    electricity_rate_per_kwh: float
    total_energy_delivered_kwh: float
    total_charging_revenue: float
    total_electricity_expense: float
    total_operating_expenses: float
    gross_contribution: float
    gross_margin_percentage: float
    net_operating_profit: float
    total_recorded_investment: float
    roi_percentage: float
    stations_financials: List[StationFinancialSummary] = []
    chargers_financials: List[ChargerFinancialSummary] = []
    data_source: str = "SIMULATED_DEMO_SOURCE"
    disclaimer: str = "DERIVED FROM SYSTEM DATABASE RECORDS AND CONFIGURED TARIFFS"


class AnalyticsOverviewResponse(BaseModel):
    station_code: str = "PRABHU-HYD-01"
    station_name: str = "Prabhu's Grid"
    location: str = "Hyderabad, Telangana, India"
    installed_capacity_kw: float
    current_charging_power_kw: float
    energy_today_kwh: float
    energy_month_kwh: float
    utilization_rate: float
    tariff_per_kwh: float
    electricity_cost_per_kwh: float = 8.5
    estimated_today_cost: float
    total_stations: int = 1
    total_chargers: int
    active_chargers: int
    occupied_chargers: int = 0
    available_chargers: int
    faulted_chargers: int
    offline_chargers: int
    active_sessions_count: int
    total_charging_revenue: float = 0.0
    electricity_expenses: float = 0.0
    operating_expenses: float = 0.0
    operating_profit: float = 0.0
    return_on_investment: float = 0.0
    data_source: str = "SIMULATED_DEMO_SOURCE"
    disclaimer: str = "DEMO MODE — SIMULATED DATA — NOT LIVE STATION TELEMETRY"
    hourly_trends: List[HourlyTrendPoint] = []
    daily_trends: List[DailyTrendPoint] = []
    recent_activities: List[RecentActivityItem] = []

    model_config = ConfigDict(from_attributes=True)
