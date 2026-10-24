from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WorkspaceSetting(Base):
    __tablename__ = "workspace_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, unique=True
    )
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    energy_unit: Mapped[str] = mapped_column(String(10), default="kWh", nullable=False)
    electricity_cost_per_kwh: Mapped[float] = mapped_column(
        Numeric(8, 2), default=8.5, nullable=False
    )
    initial_investment: Mapped[float] = mapped_column(
        Numeric(14, 2), default=12500000.0, nullable=False
    )
    monthly_operating_costs: Mapped[float] = mapped_column(
        Numeric(12, 2), default=185000.0, nullable=False
    )
    compact_tables: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reduce_motion: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notify_operational_alerts: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_session_updates: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_weekly_summary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
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

    user = relationship("User", back_populates="setting")
