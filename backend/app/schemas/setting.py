from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class WorkspaceSettingBase(BaseModel):
    currency: str = "INR"
    energy_unit: str = "kWh"
    electricity_cost_per_kwh: Decimal = Field(default=Decimal("8.5"), gt=0)
    initial_investment: Decimal = Field(default=Decimal("12500000.0"), ge=0)
    monthly_operating_costs: Decimal = Field(default=Decimal("185000.0"), ge=0)
    compact_tables: bool = False
    reduce_motion: bool = False
    notify_operational_alerts: bool = True
    notify_session_updates: bool = True
    notify_weekly_summary: bool = False


class WorkspaceSettingUpdate(BaseModel):
    currency: Optional[str] = None
    energy_unit: Optional[str] = None
    electricity_cost_per_kwh: Optional[Decimal] = Field(None, gt=0)
    initial_investment: Optional[Decimal] = Field(None, ge=0)
    monthly_operating_costs: Optional[Decimal] = Field(None, ge=0)
    compact_tables: Optional[bool] = None
    reduce_motion: Optional[bool] = None
    notify_operational_alerts: Optional[bool] = None
    notify_session_updates: Optional[bool] = None
    notify_weekly_summary: Optional[bool] = None


class WorkspaceSettingResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    currency: str
    energy_unit: str
    electricity_cost_per_kwh: float
    initial_investment: float
    monthly_operating_costs: float
    compact_tables: bool
    reduce_motion: bool
    notify_operational_alerts: bool
    notify_session_updates: bool
    notify_weekly_summary: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
