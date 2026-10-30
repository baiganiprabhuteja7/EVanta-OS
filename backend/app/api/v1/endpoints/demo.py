from typing import Any, Dict, List
from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, require_admin
from app.models.user import User
from app.services.demo_service import DEMO_DISCLAIMER, DEMO_DATA_SOURCE, DemoService

router = APIRouter(prefix="/demo", tags=["Demo Environment"])


@router.get("/status")
def get_demo_status(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Check demo environment readiness and explicit simulated mode banner."""
    return {
        "status": "ready",
        "is_demo": True,
        "environment": "isolated_simulation",
        "data_source": DEMO_DATA_SOURCE,
        "disclaimer": DEMO_DISCLAIMER,
        "message": "Demo mode active. All readings are simulated demo data. Real station hardware is not controlled.",
    }


@router.get("/station")
def get_demo_station(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Retrieve isolated demo station profile and simulated KPIs."""
    return DemoService.get_station()


@router.get("/chargers")
def get_demo_chargers(
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Retrieve isolated demo AC and DC chargers with simulated telemetry."""
    return DemoService.get_chargers()


@router.get("/sessions")
def get_demo_sessions(
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Retrieve isolated demo charging sessions history."""
    return DemoService.get_sessions()


@router.get("/analytics")
def get_demo_analytics(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Retrieve isolated demo load profile, peak power demand, and energy trends."""
    return DemoService.get_analytics()


@router.get("/alerts")
def get_demo_alerts(
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Retrieve isolated demo station warnings and maintenance notices."""
    return DemoService.get_alerts()


@router.post("/reset")
def reset_demo(
    current_admin: User = Depends(require_admin),
) -> Dict[str, Any]:
    """Restore the isolated demo environment to initial simulated baseline (Administrator only)."""
    return DemoService.reset_demo()
