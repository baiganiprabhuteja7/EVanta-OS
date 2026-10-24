from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_admin, get_current_user, get_db
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserResponse, UserStatusUpdate, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def read_user_me(current_user: User = Depends(get_current_user)):
    """Retrieve current authenticated user's profile."""
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user's personal details."""
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name.strip()
    if user_update.email is not None:
        new_email = user_update.email.lower().strip()
        existing = db.scalar(select(User).where(User.email == new_email, User.id != current_user.id))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists.",
            )
        current_user.email = new_email
    if user_update.password:
        current_user.password_hash = hash_password(user_update.password)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
):
    """List all registered users (Administrator only)."""
    users = db.scalars(select(User).offset(skip).limit(limit)).all()
    return users


@router.patch("/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: int,
    status_update: UserStatusUpdate,
    current_admin: User = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
):
    """Change user activation status or role (Administrator only)."""
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found.",
        )

    if status_update.is_active is not None:
        user.is_active = status_update.is_active
    if status_update.role is not None:
        if status_update.role not in ["admin", "user"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role must be either 'admin' or 'user'.",
            )
        user.role = status_update.role

    db.commit()
    db.refresh(user)
    return user
