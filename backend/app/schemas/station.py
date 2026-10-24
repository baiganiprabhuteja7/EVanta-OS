from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.charger import ChargerResponse


class StationBase(BaseModel):
    station_code: str = Field(..., min_length=2, max_length=50)
    station_name: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    status: str = Field(default="Online")


class StationCreate(StationBase):
    chargers_count: Optional[int] = Field(default=0, ge=0, le=100)


class StationUpdate(BaseModel):
    station_name: Optional[str] = Field(None, min_length=2, max_length=150)
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    status: Optional[str] = None
    chargers_count: Optional[int] = Field(None, ge=0, le=100)


class StationResponse(BaseModel):
    id: int
    station_code: str
    station_name: str
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: str
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    # Computed fields for API & frontend integration
    location: Optional[str] = None
    chargers: int = 0
    active_chargers: int = 0
    energy_delivered: float = 0.0
    todays_revenue: float = 0.0
    utilization: int = 0

    model_config = ConfigDict(from_attributes=True)


class StationDetailResponse(StationResponse):
    charger_list: List[ChargerResponse] = []
