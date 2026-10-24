from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ChargerBase(BaseModel):
    charger_code: str = Field(..., min_length=2, max_length=50)
    charger_type: str = Field(default="AC", pattern="^(AC|DC)$")
    connector_type: str = Field(..., min_length=2, max_length=50)
    rated_power_kw: Decimal = Field(..., gt=0)
    voltage: Optional[Decimal] = Field(default=Decimal("230.0"), gt=0)
    current_amp: Optional[Decimal] = Field(default=Decimal("0.0"), ge=0)
    power_factor: Optional[Decimal] = Field(default=Decimal("0.94"), ge=0, le=1)
    status: str = Field(default="Available")


class ChargerCreate(ChargerBase):
    pass


class ChargerUpdate(BaseModel):
    charger_code: Optional[str] = None
    charger_type: Optional[str] = Field(None, pattern="^(AC|DC)$")
    connector_type: Optional[str] = None
    rated_power_kw: Optional[Decimal] = Field(None, gt=0)
    voltage: Optional[Decimal] = Field(None, gt=0)
    current_amp: Optional[Decimal] = Field(None, ge=0)
    power_factor: Optional[Decimal] = Field(None, ge=0, le=1)
    status: Optional[str] = None


class ChargerResponse(BaseModel):
    id: int
    station_id: int
    charger_code: str
    charger_type: str
    connector_type: str
    rated_power_kw: float
    voltage: Optional[float] = 230.0
    current_amp: Optional[float] = 0.0
    power_factor: Optional[float] = 0.94
    status: str
    created_at: datetime
    updated_at: datetime

    # Additional computed helper fields for frontend compatibility
    station_code: Optional[str] = None
    current_session: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
