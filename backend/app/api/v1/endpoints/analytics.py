from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.dashboard import AnalyticsOverviewResponse, FinancialReportResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics & Financial Intelligence"])


@router.get("/overview", response_model=AnalyticsOverviewResponse)
def get_analytics_overview(
    station_id: Optional[str] = Query(None, description="Optional station ID or code"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve electrical overview, installed capacity, current power, and trend charts."""
    return AnalyticsService.get_overview(db, station_id_or_code=station_id)


@router.get("/dashboard", response_model=AnalyticsOverviewResponse)
def get_dashboard_kpis(
    station_id: Optional[str] = Query(None, description="Optional station ID or code"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Dashboard KPIs for overview, operational metrics, and financial return."""
    return AnalyticsService.get_overview(db, station_id_or_code=station_id)


@router.get("/financials", response_model=FinancialReportResponse)
def get_financial_report(
    from_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    to_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    station_id: Optional[int] = Query(None, description="Optional station ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve comprehensive commercial performance: revenue, electricity expenses, operating expenses, profit, and ROI."""
    return AnalyticsService.get_financial_report(
        db=db,
        from_date=from_date,
        to_date=to_date,
        station_id=station_id,
    )


@router.get("/energy")
def get_energy_metrics(
    days: int = 30,
    station_id: Optional[str] = Query(None, description="Optional station ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve energy delivery trends and load profiling."""
    overview = AnalyticsService.get_overview(db, station_id_or_code=station_id)
    return {
        "energy_today_kwh": overview["energy_today_kwh"],
        "energy_month_kwh": overview["energy_month_kwh"],
        "hourly_trends": overview["hourly_trends"],
        "daily_trends": overview["daily_trends"],
        "data_source": overview["data_source"],
        "disclaimer": overview["disclaimer"],
    }


@router.get("/business")
def get_business_analytics(
    station_id: Optional[str] = Query(None, description="Optional station ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve commercial performance, revenue, profit, and ROI calculations."""
    overview = AnalyticsService.get_overview(db, station_id_or_code=station_id)
    return {
        "station_name": overview["station_name"],
        "tariff_per_kwh": overview["tariff_per_kwh"],
        "electricity_cost_per_kwh": overview["electricity_cost_per_kwh"],
        "estimated_today_cost": overview["estimated_today_cost"],
        "total_charging_revenue": overview["total_charging_revenue"],
        "electricity_expenses": overview["electricity_expenses"],
        "operating_expenses": overview["operating_expenses"],
        "operating_profit": overview["operating_profit"],
        "return_on_investment": overview["return_on_investment"],
        "energy_today_kwh": overview["energy_today_kwh"],
        "energy_month_kwh": overview["energy_month_kwh"],
        "utilization_rate": overview["utilization_rate"],
        "data_source": overview["data_source"],
        "disclaimer": overview["disclaimer"],
    }
