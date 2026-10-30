from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


class StationLayout(Base):
    __tablename__ = "station_layouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    station_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("stations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), default="Hyderabad Station Engineering Floor Plan", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    scale_ratio: Mapped[float] = mapped_column(Numeric(10, 4), default=1.0, nullable=False)
    scale_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    disclaimer: Mapped[str] = mapped_column(
        String(255),
        default="SAMPLE LAYOUT · ILLUSTRATIVE DIMENSIONS · NOT SURVEYED HARDWARE TELEMETRY",
        nullable=False,
    )
    # Stored layout geometry, zones, assets, and positions
    layout_data = mapped_column(JSON, nullable=False)

    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    station = relationship("Station")
    creator = relationship("User")
