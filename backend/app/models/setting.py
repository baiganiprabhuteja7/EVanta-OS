from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StationSetting(Base):
    __tablename__ = "station_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    station_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("stations.id", ondelete="CASCADE"), nullable=True, unique=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    station_address: Mapped[str] = mapped_column(
        String(255),
        default="HITEC City / Madhapur Corridor, Hyderabad, Telangana 500081, India",
        nullable=False,
    )
    tariff_per_kwh: Mapped[float] = mapped_column(Numeric(8, 2), default=18.5, nullable=False)
    electricity_cost_per_kwh: Mapped[float] = mapped_column(Numeric(8, 2), default=7.5, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    energy_unit: Mapped[str] = mapped_column(String(10), default="kWh", nullable=False)
    power_unit: Mapped[str] = mapped_column(String(10), default="kW", nullable=False)
    demo_mode_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_refresh_seconds: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    notify_operational_alerts: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_session_updates: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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

    # Legacy properties
    @property
    def compact_tables(self) -> bool:
        return False

    @property
    def reduce_motion(self) -> bool:
        return False

    @property
    def initial_investment(self) -> float:
        return 0.0

    @property
    def monthly_operating_costs(self) -> float:
        return 0.0

    @property
    def notify_weekly_summary(self) -> bool:
        return False


# Legacy alias
WorkspaceSetting = StationSetting
