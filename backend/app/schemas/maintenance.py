from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class MaintenanceRecordBase(BaseModel):
    station_id: int
    charger_id: Optional[int] = None
    equipment_name: str = Field(..., min_length=2, max_length=100)
    issue_description: str = Field(..., min_length=5)
    severity: str = Field(default="Medium", pattern="^(Low|Medium|High|Critical)$")
    status: str = Field(default="Reported", pattern="^(Reported|Scheduled|In Progress|Completed|Cancelled)$")
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    cost: Decimal = Field(default=Decimal("0.0"), ge=0)
    technician_name: Optional[str] = None
    resolution_notes: Optional[str] = None


class MaintenanceRecordCreate(MaintenanceRecordBase):
    pass


class MaintenanceRecordUpdate(BaseModel):
    station_id: Optional[int] = None
    charger_id: Optional[int] = None
    equipment_name: Optional[str] = None
    issue_description: Optional[str] = None
    severity: Optional[str] = Field(None, pattern="^(Low|Medium|High|Critical)$")
    status: Optional[str] = Field(None, pattern="^(Reported|Scheduled|In Progress|Completed|Cancelled)$")
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    cost: Optional[Decimal] = Field(None, ge=0)
    technician_name: Optional[str] = None
    resolution_notes: Optional[str] = None


class MaintenanceRecordResponse(BaseModel):
    id: int
    station_id: int
    station_name: Optional[str] = None
    charger_id: Optional[int] = None
    charger_code: Optional[str] = None
    equipment_name: str
    issue_description: str
    severity: str
    status: str
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    cost: float
    technician_name: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
