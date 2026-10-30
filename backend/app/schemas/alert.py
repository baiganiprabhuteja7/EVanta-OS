from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AlertResponse(BaseModel):
    id: int
    station_id: int
    charger_id: Optional[int] = None
    charger_code: Optional[str] = None
    severity: str  # info, warning, critical
    code: str
    title: str
    message: str
    is_active: bool
    data_source: str = "SIMULATED_DEMO_SOURCE"
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AlertResolveRequest(BaseModel):
    is_active: bool = False
