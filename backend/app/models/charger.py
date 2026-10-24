from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Charger(Base):
    __tablename__ = "chargers"
    __table_args__ = (
        UniqueConstraint("station_id", "charger_code", name="uq_station_charger_code"),
        CheckConstraint("rated_power_kw > 0", name="check_rated_power_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    station_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("stations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    charger_code: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    charger_type: Mapped[str] = mapped_column(String(20), default="AC", nullable=False)  # AC, DC
    connector_type: Mapped[str] = mapped_column(String(50), nullable=False)  # Type 2, CCS2, CHAdeMO
    rated_power_kw: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    voltage: Mapped[float] = mapped_column(Numeric(6, 2), default=230.0, nullable=True)
    current_amp: Mapped[float] = mapped_column(Numeric(6, 2), default=0.0, nullable=True)
    power_factor: Mapped[float] = mapped_column(Numeric(4, 2), default=0.94, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="Available", nullable=False
    )  # Available, Charging, Offline, Faulted
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
    station = relationship("Station", back_populates="chargers")
    charging_sessions = relationship("ChargingSession", back_populates="charger", cascade="all, delete-orphan")
