from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetResponse,
    Token,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/dev-login", response_model=Token)
def dev_login(db: Session = Depends(get_db)):
    """Development-only single-click admin access (disabled in production)."""
    return AuthService.dev_login_admin(db)


@router.get("/dev-status")
def get_dev_auth_status():
    """Check if development authentication bypass is currently enabled."""
    return {
        "dev_auth_bypass": settings.is_dev_auth_bypass_enabled,
        "environment": settings.ENVIRONMENT,
    }


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Authenticate an authorized station official.
    Accepts JSON body: {"email": "...", "password": "..."} or {"username": "...", "password": "..."}
    or OAuth2 Form URL-encoded data.
    Protected against credential enumeration and repeated failed attempts.
    """
    identifier = None
    password = None

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            identifier = body.get("email") or body.get("username")
            password = body.get("password")
        except Exception:
            pass
    elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        try:
            form = await request.form()
            identifier = form.get("username") or form.get("email")
            password = form.get("password")
        except Exception:
            pass
    else:
        # Fallback attempt
        try:
            body = await request.json()
            identifier = body.get("email") or body.get("username")
            password = body.get("password")
        except Exception:
            try:
                form = await request.form()
                identifier = form.get("username") or form.get("email")
                password = form.get("password")
            except Exception:
                pass

    if not identifier or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email/username and password are required.",
        )

    return AuthService.login_user(db, identifier=str(identifier), password=str(password))


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Retrieve details of the currently authenticated official."""
    return current_user


@router.post("/logout")
def logout(
    authorization: Optional[str] = Header(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Invalidate local session and revoke JWT access token."""
    token_str = None
    if authorization and authorization.lower().startswith("bearer "):
        token_str = authorization.split(" ", 1)[1].strip()

    return AuthService.logout_user(db, token_str=token_str)


@router.post("/password-reset-request", response_model=PasswordResetResponse)
def request_password_reset(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    """
    Request password reset instructions.
    If email delivery is not configured, provides guidance to contact the station administrator.
    """
    return AuthService.request_password_reset(db, identifier=payload.email)


@router.post("/password-reset-confirm")
def confirm_password_reset(
    payload: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    """Confirm password reset using a cryptographically signed token."""
    return AuthService.confirm_password_reset(
        db, token=payload.token, new_password=payload.new_password
    )
