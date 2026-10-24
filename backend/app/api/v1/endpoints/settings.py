from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user_optional, get_db
from app.models.setting import WorkspaceSetting
from app.models.user import User
from app.schemas.setting import WorkspaceSettingResponse, WorkspaceSettingUpdate

router = APIRouter(prefix="/settings", tags=["Settings"])


def _setting_to_response(s: WorkspaceSetting) -> WorkspaceSettingResponse:
    return WorkspaceSettingResponse(
        id=s.id,
        user_id=s.user_id,
        currency=s.currency,
        energy_unit=s.energy_unit,
        electricity_cost_per_kwh=float(s.electricity_cost_per_kwh),
        initial_investment=float(s.initial_investment),
        monthly_operating_costs=float(s.monthly_operating_costs),
        compact_tables=s.compact_tables,
        reduce_motion=s.reduce_motion,
        notify_operational_alerts=s.notify_operational_alerts,
        notify_session_updates=s.notify_session_updates,
        notify_weekly_summary=s.notify_weekly_summary,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


@router.get("", response_model=WorkspaceSettingResponse)
def get_settings(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Retrieve workspace and user settings."""
    setting = None
    if current_user:
        setting = db.scalar(select(WorkspaceSetting).where(WorkspaceSetting.user_id == current_user.id))

    if not setting:
        setting = db.scalar(select(WorkspaceSetting).order_by(WorkspaceSetting.id))

    if not setting:
        setting = WorkspaceSetting(
            user_id=current_user.id if current_user else None,
            currency="INR",
            energy_unit="kWh",
            electricity_cost_per_kwh=Decimal("8.5"),
            initial_investment=Decimal("12500000.0"),
            monthly_operating_costs=Decimal("185000.0"),
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)

    return _setting_to_response(setting)


@router.put("", response_model=WorkspaceSettingResponse)
def update_settings(
    update_in: WorkspaceSettingUpdate,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Update workspace parameters, business assumptions, and UI preferences."""
    setting = None
    if current_user:
        setting = db.scalar(select(WorkspaceSetting).where(WorkspaceSetting.user_id == current_user.id))

    if not setting:
        setting = db.scalar(select(WorkspaceSetting).order_by(WorkspaceSetting.id))

    if not setting:
        setting = WorkspaceSetting(user_id=current_user.id if current_user else None)
        db.add(setting)

    if update_in.currency is not None:
        setting.currency = update_in.currency
    if update_in.energy_unit is not None:
        setting.energy_unit = update_in.energy_unit
    if update_in.electricity_cost_per_kwh is not None:
        setting.electricity_cost_per_kwh = update_in.electricity_cost_per_kwh
    if update_in.initial_investment is not None:
        setting.initial_investment = update_in.initial_investment
    if update_in.monthly_operating_costs is not None:
        setting.monthly_operating_costs = update_in.monthly_operating_costs
    if update_in.compact_tables is not None:
        setting.compact_tables = update_in.compact_tables
    if update_in.reduce_motion is not None:
        setting.reduce_motion = update_in.reduce_motion
    if update_in.notify_operational_alerts is not None:
        setting.notify_operational_alerts = update_in.notify_operational_alerts
    if update_in.notify_session_updates is not None:
        setting.notify_session_updates = update_in.notify_session_updates
    if update_in.notify_weekly_summary is not None:
        setting.notify_weekly_summary = update_in.notify_weekly_summary

    db.commit()
    db.refresh(setting)
    return _setting_to_response(setting)
