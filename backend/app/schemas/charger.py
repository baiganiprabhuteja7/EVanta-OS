from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ChargerBase(BaseModel):
    station_id: Optional[int] = None
    charger_code: str = Field(..., min_length=2, max_length=50)
    charger_type: str = Field(default="AC", pattern="^(AC|DC)$")
    connector_type: str = Field(..., min_length=2, max_length=50)
    rated_power_kw: Decimal = Field(..., gt=0, description="Nameplate power rating in kW")
    voltage: Optional[Decimal] = Field(default=Decimal("230.0"), ge=0)
    current_amp: Optional[Decimal] = Field(default=Decimal("0.0"), ge=0)
    power_factor: Optional[Decimal] = Field(default=Decimal("0.94"), ge=0, le=1)
    status: str = Field(default="Available")
    location_name: Optional[str] = "Main Canopy"


class ChargerCreate(ChargerBase):
    pass


class ChargerUpdate(BaseModel):
    station_id: Optional[int] = None
    charger_code: Optional[str] = None
    charger_type: Optional[str] = Field(None, pattern="^(AC|DC)$")
    connector_type: Optional[str] = None
    rated_power_kw: Optional[Decimal] = Field(None, gt=0)
    voltage: Optional[Decimal] = Field(None, ge=0)
    current_amp: Optional[Decimal] = Field(None, ge=0)
    power_factor: Optional[Decimal] = Field(None, ge=0, le=1)
    status: Optional[str] = None
    location_name: Optional[str] = None


class ChargerResponse(BaseModel):
    id: int
    station_id: int
    station_name: Optional[str] = None
    charger_code: str
    charger_type: str
    connector_type: str
    rated_power_kw: float
    voltage: float = 230.0
    current_amp: float = 0.0
    power_factor: float = 0.94
    current_power_kw: float = 0.0
    energy_delivered_kwh: float = 0.0
    total_sessions_count: int = 0
    total_revenue: float = 0.0
    total_electricity_expense: float = 0.0
    operating_profit: float = 0.0
    status: str
    location_name: str = "Main Canopy"
    current_session: Optional[str] = None
    data_source: str = "SIMULATED_DEMO_SOURCE"
    disclaimer: str = "SIMULATED READING — NOT MEASURED PHYSICAL HARDWARE"
    latest_reading_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
