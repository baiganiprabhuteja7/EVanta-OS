from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class StationBase(BaseModel):
    station_code: str = Field(..., min_length=2, max_length=50)
    station_name: str = Field(..., min_length=2, max_length=150)
    owner_name: str = Field(default="Prabhu", min_length=1, max_length=100)
    description: Optional[str] = None
    address: Optional[str] = "HITEC City / Madhapur Corridor, Hyderabad, Telangana 500081, India"
    city: str = Field(default="Hyderabad")
    state: str = Field(default="Telangana")
    country: str = Field(default="India")
    postal_code: Optional[str] = "500081"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: str = Field(default="Online")
    initial_investment: Decimal = Field(default=Decimal("2500000.0"), ge=0)
    monthly_fixed_cost: Decimal = Field(default=Decimal("18000.0"), ge=0)


class StationCreate(StationBase):
    pass


class StationUpdate(BaseModel):
    station_code: Optional[str] = None
    station_name: Optional[str] = None
    owner_name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    status: Optional[str] = None
    initial_investment: Optional[Decimal] = Field(None, ge=0)
    monthly_fixed_cost: Optional[Decimal] = Field(None, ge=0)


class StationSummaryResponse(BaseModel):
    id: int
    station_code: str
    station_name: str
    owner_name: str
    city: str
    state: str
    country: str
    address: str
    status: str
    initial_investment: float = 2500000.0
    monthly_fixed_cost: float = 18000.0
    data_source: str = "SIMULATED_DEMO_SOURCE"
    disclaimer: str = "DEMO MODE — SIMULATED DATA — NOT LIVE STATION TELEMETRY"
    created_at: datetime
    updated_at: datetime

    # Electrical & Operational KPIs
    installed_capacity_kw: float
    current_charging_power_kw: float
    energy_today_kwh: float
    energy_month_kwh: float
    total_energy_kwh: float = 0.0
    active_sessions_count: int
    total_chargers: int
    active_chargers: int
    available_chargers: int
    faulted_chargers: int
    offline_chargers: int
    utilization_rate: float
    tariff_per_kwh: float
    electricity_cost_per_kwh: float = 8.5
    estimated_today_cost: float
    total_revenue: float = 0.0
    total_electricity_expense: float = 0.0
    total_operating_expenses: float = 0.0
    operating_profit: float = 0.0
    roi_percentage: float = 0.0

    model_config = ConfigDict(from_attributes=True)


StationResponse = StationSummaryResponse
