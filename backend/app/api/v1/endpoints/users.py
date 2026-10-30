from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin, get_current_user, get_db
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import (
    VALID_ROLES,
    UserCreate,
    UserResponse,
    UserStatusUpdate,
    UserUpdate,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/users", tags=["Authorized User Management"])


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
    """Update current user's profile details."""
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name.strip()

    if user_update.email is not None:
        new_email = user_update.email.lower().strip()
        existing = db.scalar(
            select(User).where(func.lower(User.email) == new_email, User.id != current_user.id)
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists.",
            )
        current_user.email = new_email

    if user_update.username is not None:
        new_username = user_update.username.lower().strip()
        existing_u = db.scalar(
            select(User).where(func.lower(User.username) == new_username, User.id != current_user.id)
        )
        if existing_u:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this username already exists.",
            )
        current_user.username = new_username

    if user_update.password:
        current_user.password_hash = hash_password(user_update.password)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 100,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all authorized users (Administrator only)."""
    users = db.scalars(select(User).order_by(User.id.asc()).offset(skip).limit(limit)).all()
    return users


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new authorized official account (Administrator only)."""
    return AuthService.create_authorized_user(db, user_in)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update authorized user account (Administrator only)."""
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found.",
        )

    if user_update.full_name is not None:
        user.full_name = user_update.full_name.strip()

    if user_update.email is not None:
        new_email = user_update.email.lower().strip()
        existing = db.scalar(
            select(User).where(func.lower(User.email) == new_email, User.id != user.id)
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists.",
            )
        user.email = new_email

    if user_update.username is not None:
        new_user = user_update.username.lower().strip()
        existing_u = db.scalar(
            select(User).where(func.lower(User.username) == new_user, User.id != user.id)
        )
        if existing_u:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this username already exists.",
            )
        user.username = new_user

    if user_update.password:
        user.password_hash = hash_password(user_update.password)

    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: int,
    status_update: UserStatusUpdate,
    current_admin: User = Depends(require_admin),
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
        # Prevent administrator from deactivating themselves
        if user.id == current_admin.id and not status_update.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Administrators cannot deactivate their own account.",
            )
        user.is_active = status_update.is_active

    if status_update.role is not None:
        norm_role = status_update.role.lower().strip()
        if norm_role not in VALID_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role must be one of: {', '.join(VALID_ROLES)}.",
            )
        # Prevent last admin from demoting themselves
        if user.id == current_admin.id and norm_role != "admin":
            admin_count = db.scalar(
                select(func.count(User.id)).where(User.role == "admin", User.is_active == True)
            )
            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot demote the sole active administrator account.",
                )
        user.role = norm_role

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Remove an authorized user account (Administrator only)."""
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found.",
        )

    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot delete their own account.",
        )

    db.delete(user)
    db.commit()
    return {"message": f"User {user_id} deleted successfully.", "status": "ok"}
