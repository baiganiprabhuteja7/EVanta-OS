from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LayoutAsset(BaseModel):
    id: str = Field(..., description="Unique stable asset ID")
    type: str = Field(..., description="Asset type: charger_ac, charger_dc, parking_bay, utility_room, transformer, signage, lane, pedestrian")
    name: str = Field(..., description="Display name / label")
    x: float = Field(..., description="Local X coordinate (units)")
    y: float = Field(..., description="Local Y coordinate (units)")
    width: float = Field(..., description="Object width (units)")
    height: float = Field(..., description="Object height/depth (units)")
    rotation: float = Field(default=0.0, description="Rotation in degrees")
    charger_code: Optional[str] = Field(None, description="Optional linked physical/simulated charger code (e.g. PRABHU-AC-01)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Asset metadata (power, status, connector, bay code, etc.)")


class StationBoundary(BaseModel):
    width: float = Field(default=1000.0)
    height: float = Field(default=650.0)
    label: str = Field(default="Hyderabad Station Perimeter")


class LayoutData(BaseModel):
    boundary: StationBoundary = Field(default_factory=StationBoundary)
    assets: List[LayoutAsset] = Field(default_factory=list)


class StationLayoutResponse(BaseModel):
    id: int
    station_id: int
    name: str
    version: int
    is_demo: bool
    scale_ratio: float
    scale_verified: bool
    disclaimer: str
    layout_data: LayoutData
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class StationLayoutUpdate(BaseModel):
    version: int = Field(..., description="Current version for optimistic concurrency control")
    name: Optional[str] = None
    scale_ratio: Optional[float] = None
    scale_verified: Optional[bool] = None
    layout_data: LayoutData
