from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_manager_or_admin, get_db
from app.models.user import User
from app.schemas.charging_session import SessionComplete, SessionCreate, SessionResponse
from app.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["Charging Sessions"])


@router.get("", response_model=List[SessionResponse])
def get_sessions(
    station_id: Optional[int] = Query(None, description="Filter by station ID"),
    charger_type: Optional[str] = Query(None, description="Filter by AC or DC"),
    status: Optional[str] = Query(None, description="Filter by status (Ongoing, Completed, Failed)"),
    search: Optional[str] = Query(None, description="Search by session code, charger, or station"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve charging session history and active sessions."""
    return SessionService.get_sessions(
        db=db,
        station_id=station_id,
        charger_type=charger_type,
        status_filter=status,
        search=search,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def start_session(
    session_in: SessionCreate,
    current_operator: User = Depends(require_manager_or_admin),
    db: Session = Depends(get_db),
):
    """Start a simulated charging session on a charger (Station Manager or Administrator)."""
    charger_ident = session_in.charger_id or session_in.charger_code
    if not charger_ident:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide charger_id or charger_code to start session.",
        )
    return SessionService.start_session(
        db=db,
        charger_id_or_code=str(charger_ident),
        unit_price=session_in.unit_price,
        user_id=current_operator.id,
    )


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve details for a single charging session."""
    session = SessionService.get_session_by_id_or_code(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    return SessionService._enrich_session(session, db)


@router.post("/{session_id}/complete", response_model=SessionResponse)
def complete_session(
    session_id: str,
    complete_in: Optional[SessionComplete] = None,
    current_operator: User = Depends(require_manager_or_admin),
    db: Session = Depends(get_db),
):
    """Conclude an active charging session, record final energy, cost, and payment (Station Manager or Administrator)."""
    return SessionService.complete_session(
        db=db,
        identifier=session_id,
        complete_data=complete_in,
    )
