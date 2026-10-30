from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class StationSettingUpdate(BaseModel):
    station_address: Optional[str] = None
    tariff_per_kwh: Optional[Decimal] = Field(None, gt=0)
    electricity_cost_per_kwh: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = None
    energy_unit: Optional[str] = None
    power_unit: Optional[str] = None
    demo_mode_active: Optional[bool] = None
    auto_refresh_seconds: Optional[int] = Field(None, ge=5, le=300)
    notify_operational_alerts: Optional[bool] = None
    notify_session_updates: Optional[bool] = None


class StationSettingResponse(BaseModel):
    id: int
    station_id: Optional[int] = None
    station_address: str
    tariff_per_kwh: float
    electricity_cost_per_kwh: float
    currency: str
    energy_unit: str
    power_unit: str
    demo_mode_active: bool
    auto_refresh_seconds: int
    notify_operational_alerts: bool
    notify_session_updates: bool
    data_source: str = "SIMULATED_DEMO_SOURCE"
    disclaimer: str = "DEMO MODE — SIMULATED DATA — NOT LIVE STATION TELEMETRY"
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Compatibility aliases
WorkspaceSettingUpdate = StationSettingUpdate
WorkspaceSettingResponse = StationSettingResponse
