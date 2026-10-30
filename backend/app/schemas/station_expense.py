from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class StationExpenseBase(BaseModel):
    station_id: int
    expense_date: Optional[datetime] = None
    category: str = Field(default="Site Operations", max_length=50)
    amount: Decimal = Field(..., gt=0)
    description: Optional[str] = None


class StationExpenseCreate(StationExpenseBase):
    pass


class StationExpenseResponse(BaseModel):
    id: int
    station_id: int
    station_name: Optional[str] = None
    expense_date: datetime
    category: str
    amount: float
    description: Optional[str] = None
    recorded_by: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
