from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ChargingSession(Base):
    __tablename__ = "charging_sessions"
    __table_args__ = (
        CheckConstraint("energy_delivered_kwh >= 0", name="check_energy_non_negative"),
        CheckConstraint("total_amount >= 0", name="check_amount_non_negative"),
        CheckConstraint("duration_seconds >= 0", name="check_duration_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=True)
    charger_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chargers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    energy_delivered_kwh: Mapped[float] = mapped_column(
        Numeric(8, 2), default=0.0, nullable=False
    )
    peak_power_kw: Mapped[float] = mapped_column(Numeric(6, 2), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="Ongoing", nullable=False
    )  # Pending, Ongoing, Completed, Failed
    unit_price: Mapped[float] = mapped_column(
        Numeric(8, 2), default=22.0, nullable=False
    )
    total_amount: Mapped[float] = mapped_column(
        Numeric(10, 2), default=0.0, nullable=False
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
    charger = relationship("Charger", back_populates="charging_sessions")
    user = relationship("User", back_populates="charging_sessions")
    payments = relationship("Payment", back_populates="charging_session", cascade="all, delete-orphan")
