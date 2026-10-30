from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    station_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("stations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    charger_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("chargers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    equipment_name: Mapped[str] = mapped_column(String(100), nullable=False)
    issue_description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="Medium", nullable=False)  # Low, Medium, High, Critical
    status: Mapped[str] = mapped_column(
        String(30), default="Reported", nullable=False
    )  # Reported, Scheduled, In Progress, Completed, Cancelled
    scheduled_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cost: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    technician_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(
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
    station = relationship("Station", back_populates="maintenance_records")
    charger = relationship("Charger", back_populates="maintenance_records")
    creator = relationship("User")
