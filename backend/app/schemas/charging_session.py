from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SessionCreate(BaseModel):
    charger_id: Optional[int] = None
    charger_code: Optional[str] = None
    user_id: Optional[int] = None
    unit_price: Optional[Decimal] = Field(default=Decimal("18.5"), ge=0)


class SessionComplete(BaseModel):
    energy_delivered_kwh: Optional[Decimal] = Field(None, ge=0)
    peak_power_kw: Optional[Decimal] = Field(None, ge=0)


class SessionResponse(BaseModel):
    id: int
    session_code: str
    station_id: Optional[int] = None
    station_name: Optional[str] = None
    charger_id: int
    charger_code: Optional[str] = None
    charger_type: Optional[str] = None
    connector_type: Optional[str] = None
    user_id: Optional[int] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    energy_delivered_kwh: float
    peak_power_kw: Optional[float] = None
    duration_seconds: int
    duration_minutes: int = 0
    status: str
    unit_price: float
    total_amount: float
    data_source: str = "SIMULATED_DEMO_SOURCE"
    disclaimer: str = "SIMULATED SESSION RECORD"
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
