from datetime import datetime, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token, is_token_revoked
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Retrieve current user from JWT token if present, without raising 401 if missing."""
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None

    jti = payload.get("jti")
    if jti and is_token_revoked(db, jti):
        return None

    user_id_str = payload.get("sub")
    if not user_id_str:
        return None
    try:
        user_id = int(user_id_str)
    except ValueError:
        return None

    user = db.scalar(select(User).where(User.id == user_id))
    if not user or not user.is_active:
        return None
    return user


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate JWT token, check revocation and active status, and return user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token has expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    # Token revocation check (e.g. after logout)
    jti = payload.get("jti")
    if jti and is_token_revoked(db, jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been terminated. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise credentials_exception

    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact an administrator.",
        )

    now = datetime.now(timezone.utc)
    if user.locked_until and user.locked_until > now:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account is temporarily locked due to repeated failed login attempts.",
        )

    return user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Enforce administrator privileges for privileged operations."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required for this action.",
        )
    return current_user


# Backward compatibility alias
get_current_active_admin = require_admin


def require_manager_or_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Enforce Station Manager or Administrator role for operational actions
    (e.g., starting/completing sessions, acknowledging alerts).
    """
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operational action requires Station Manager or Administrator privileges.",
        )
    return current_user
