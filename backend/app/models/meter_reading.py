from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MeterReading(Base):
    __tablename__ = "meter_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    charger_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chargers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    power_kw: Mapped[float] = mapped_column(Numeric(8, 2), default=0.0, nullable=False)
    energy_kwh: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    voltage_v: Mapped[float] = mapped_column(Numeric(6, 2), default=230.0, nullable=True)
    current_a: Mapped[float] = mapped_column(Numeric(6, 2), default=0.0, nullable=True)
    power_factor: Mapped[float] = mapped_column(Numeric(4, 2), default=0.94, nullable=True)
    data_source: Mapped[str] = mapped_column(String(50), default="SIMULATED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship
    charger = relationship("Charger", back_populates="meter_readings")
