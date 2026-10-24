from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user_optional, get_db
from app.models.user import User
from app.schemas.charging_session import SessionComplete, SessionCreate, SessionResponse
from app.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["Charging Sessions"])


@router.get("", response_model=List[SessionResponse])
def get_sessions(
    station: Optional[str] = Query(None, description="Filter by station code or name"),
    charger_type: Optional[str] = Query(None, description="Filter by charger type: AC or DC"),
    status: Optional[str] = Query(None, description="Filter by status: Completed, Ongoing, Failed"),
    search: Optional[str] = Query(None, description="Search term for session code, charger, or station"),
    from_date: Optional[str] = Query(None, description="From ISO timestamp"),
    to_date: Optional[str] = Query(None, description="To ISO timestamp"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Retrieve charging sessions with full filtering, timing calculations, and search."""
    return SessionService.get_sessions(
        db=db,
        station_id=station,
        charger_type=charger_type,
        status_filter=status,
        search=search,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    session_in: SessionCreate,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Initiate a charging session on a designated available charger."""
    target_charger = str(session_in.charger_id) if session_in.charger_id else session_in.charger_code
    if not target_charger:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either charger_id or charger_code must be provided.",
        )

    return SessionService.start_session(
        db=db,
        charger_identifier=target_charger,
        user=current_user,
        unit_price=session_in.unit_price,
    )


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, db: Session = Depends(get_db)):
    """Retrieve details of a specific charging session by ID or session code."""
    session = SessionService.get_session_by_id_or_code(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    return SessionService._enrich_session(session, db)


@router.post("/{session_id}/start", response_model=SessionResponse)
def start_session(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Transition a pending session to active/ongoing state."""
    session = SessionService.get_session_by_id_or_code(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    if session.status.lower() == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Completed sessions cannot be restarted.",
        )
    session.status = "Ongoing"
    db.commit()
    db.refresh(session)
    return SessionService._enrich_session(session, db)


@router.post("/{session_id}/complete", response_model=SessionResponse)
def complete_session(
    session_id: str,
    complete_in: Optional[SessionComplete] = None,
    db: Session = Depends(get_db),
):
    """Complete an active charging session, finalize energy & amount, and record simulated payment."""
    return SessionService.complete_session(
        db=db,
        identifier=session_id,
        complete_data=complete_in,
    )
