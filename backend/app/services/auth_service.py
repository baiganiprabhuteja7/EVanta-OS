from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    decode_access_token,
    decode_password_reset_token,
    hash_password,
    revoke_token,
    verify_password,
)
from app.models.setting import StationSetting
from app.models.user import User
from app.schemas.auth import RegisterRequest, Token
from app.schemas.user import VALID_ROLES, UserCreate


class AuthService:
    @staticmethod
    def authenticate_user(
        db: Session, identifier: str, password: str
    ) -> User:
        """
        Authenticate an authorized official by email or username.
        Implements login throttling, account lockout after repeated failures,
        and safe error responses that do not reveal account existence.
        """
        if not identifier or not password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email/username or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        norm_id = identifier.strip().lower()
        now = datetime.now(timezone.utc)

        # Lookup by normalized email or username
        user = db.scalar(
            select(User).where(
                or_(
                    func.lower(User.email) == norm_id,
                    func.lower(User.username) == norm_id,
                )
            )
        )

        # Check temporary account lockout
        if user and user.locked_until:
            if user.locked_until > now:
                remaining_sec = int((user.locked_until - now).total_seconds())
                remaining_min = max(1, round(remaining_sec / 60))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Account is temporarily locked due to repeated failed login attempts. Please try again in {remaining_min} minute(s).",
                )
            else:
                # Lock expired, reset counter
                user.locked_until = None
                user.failed_login_attempts = 0
                db.commit()

        # Validate credentials
        if not user or not verify_password(password, user.password_hash):
            if user:
                user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                if user.failed_login_attempts >= 5:
                    user.locked_until = now + timedelta(minutes=15)
                db.commit()

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email/username or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Account status check
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated. Please contact an administrator.",
            )

        # Successful authentication: reset failed attempts
        if user.failed_login_attempts > 0 or user.locked_until:
            user.failed_login_attempts = 0
            user.locked_until = None
            db.commit()

        return user

    @staticmethod
    def login_user(db: Session, identifier: str, password: str) -> Token:
        """Authenticate user and generate Bearer JWT token."""
        user = AuthService.authenticate_user(db, identifier=identifier, password=password)

        access_token = create_access_token(
            subject=user.id,
            role=user.role,
            full_name=user.full_name,
            email=user.email,
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            role=user.role,
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            username=user.username,
        )

    @staticmethod
    def dev_login_admin(db: Session) -> Token:
        """
        Development-only bypass: authenticates as an active administrator
        without requiring password input. Strictly prohibited in production.
        """
        if not settings.is_dev_auth_bypass_enabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Development authentication bypass is disabled.",
            )

        admin_user = db.scalar(
            select(User)
            .where(User.role == "admin", User.is_active == True)
            .order_by(User.id.asc())
        )

        if not admin_user:
            admin_user = User(
                full_name="Station Administrator",
                email="admin@evanta.os",
                username="admin",
                role="admin",
                is_active=True,
                password_hash=hash_password("DevAdminPass2026!"),
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

        access_token = create_access_token(
            subject=admin_user.id,
            role=admin_user.role,
            full_name=admin_user.full_name,
            email=admin_user.email,
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            role=admin_user.role,
            user_id=admin_user.id,
            full_name=admin_user.full_name,
            email=admin_user.email,
            username=admin_user.username,
        )

    @staticmethod
    def logout_user(db: Session, token_str: Optional[str]) -> dict:
        """Revoke current JWT access token so it cannot be reused."""
        if token_str:
            payload = decode_access_token(token_str)
            if payload:
                jti = payload.get("jti")
                exp = payload.get("exp")
                if jti:
                    revoke_token(db, jti=jti, expires_at_timestamp=exp)

        return {"message": "Successfully logged out.", "status": "ok"}

    @staticmethod
    def request_password_reset(db: Session, identifier: str) -> dict:
        """
        Handle password reset request. If email is not configured,
        cleanly return guidance to contact the station administrator.
        """
        if not settings.is_email_configured:
            return {
                "message": "Password reset via email is not configured in this environment. Please contact an administrator to reset your credentials.",
                "email_configured": False,
            }

        norm_id = identifier.strip().lower()
        user = db.scalar(
            select(User).where(
                or_(
                    func.lower(User.email) == norm_id,
                    func.lower(User.username) == norm_id,
                )
            )
        )

        if user and user.is_active:
            reset_token = create_password_reset_token(user.email)
            # In a live SMTP environment, dispatch email here.

        return {
            "message": f"If an account matches '{identifier}', instructions have been dispatched.",
            "email_configured": True,
        }

    @staticmethod
    def confirm_password_reset(db: Session, token: str, new_password: str) -> dict:
        """Validate reset token and update user password."""
        email = decode_password_reset_token(token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token.",
            )

        user = db.scalar(select(User).where(func.lower(User.email) == email.lower()))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Associated user account not found.",
            )

        user.password_hash = hash_password(new_password)
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()

        return {"message": "Password has been successfully updated. You may now sign in."}

    @staticmethod
    def create_authorized_user(db: Session, request: UserCreate) -> User:
        """Admin creates an authorized official account."""
        norm_email = request.email.lower().strip()
        existing_email = db.scalar(select(User).where(func.lower(User.email) == norm_email))
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists.",
            )

        norm_username = request.username.strip().lower() if request.username else None
        if norm_username:
            existing_username = db.scalar(
                select(User).where(func.lower(User.username) == norm_username)
            )
            if existing_username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A user with this username already exists.",
                )

        role = request.role.lower().strip() if request.role else "viewer"
        if role not in VALID_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}.",
            )

        new_user = User(
            full_name=request.full_name.strip(),
            email=norm_email,
            username=norm_username,
            password_hash=hash_password(request.password),
            role=role,
            is_active=request.is_active,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
