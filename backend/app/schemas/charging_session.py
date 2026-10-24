from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SessionCreate(BaseModel):
    charger_id: Optional[int] = None
    charger_code: Optional[str] = None
    user_id: Optional[int] = None
    unit_price: Optional[Decimal] = Field(default=Decimal("22.0"), ge=0)


class SessionComplete(BaseModel):
    energy_delivered_kwh: Decimal = Field(..., ge=0)
    peak_power_kw: Optional[Decimal] = Field(None, ge=0)


class SessionResponse(BaseModel):
    id: int
    session_code: Optional[str] = None
    charger_id: int
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
    created_at: datetime
    updated_at: datetime

    # Contextual metadata for frontend views
    station_code: Optional[str] = None
    station_name: Optional[str] = None
    charger_code: Optional[str] = None
    charger_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
