from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.setting import WorkspaceSetting
from app.models.user import User
from app.schemas.auth import RegisterRequest, Token


class AuthService:
    @staticmethod
    def register_user(db: Session, request: RegisterRequest) -> Token:
        normalized_email = request.email.lower().strip()
        existing_user = db.scalar(select(User).where(User.email == normalized_email))
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists.",
            )

        # First registered user becomes admin if no users exist
        user_count = db.scalar(select(User.id).limit(1))
        assigned_role = "admin" if user_count is None else (request.role or "user")

        new_user = User(
            full_name=request.full_name.strip(),
            email=normalized_email,
            password_hash=hash_password(request.password),
            role=assigned_role,
            is_active=True,
        )
        db.add(new_user)
        db.flush()

        # Create default workspace setting for the user
        setting = WorkspaceSetting(user_id=new_user.id)
        db.add(setting)
        db.commit()
        db.refresh(new_user)

        access_token = create_access_token(subject=new_user.id, role=new_user.role)
        return Token(
            access_token=access_token,
            token_type="bearer",
            role=new_user.role,
            user_id=new_user.id,
            full_name=new_user.full_name,
            email=new_user.email,
        )

    @staticmethod
    def authenticate_user(
        db: Session, email: str, password: str
    ) -> Optional[User]:
        normalized_email = email.lower().strip()
        user = db.scalar(select(User).where(User.email == normalized_email))
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    def login_user(db: Session, email: str, password: str) -> Token:
        user = AuthService.authenticate_user(db, email, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account is currently deactivated.",
            )

        access_token = create_access_token(subject=user.id, role=user.role)
        return Token(
            access_token=access_token,
            token_type="bearer",
            role=user.role,
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
        )
