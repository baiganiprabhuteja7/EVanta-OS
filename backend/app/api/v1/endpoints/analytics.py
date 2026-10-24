from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.dashboard import BusinessAnalyticsResponse, DashboardSummary, EnergyHistoryItem
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics & Intelligence"])


@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db)):
    """Retrieve high-level overview metrics and network status."""
    return AnalyticsService.get_dashboard_summary(db)


@router.get("/energy", response_model=List[EnergyHistoryItem])
def get_energy_history(
    days: int = Query(30, ge=1, le=90, description="Number of days of energy history"),
    db: Session = Depends(get_db),
):
    """Retrieve daily energy consumption timelines across stations."""
    return AnalyticsService.get_energy_history(db, days=days)


@router.get("/business", response_model=BusinessAnalyticsResponse)
def get_business_analytics(db: Session = Depends(get_db)):
    """Retrieve financial performance and operating margins."""
    return AnalyticsService.get_business_analytics(db)
