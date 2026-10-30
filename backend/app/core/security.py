from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union
import uuid
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.token import RevokedToken

password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a password using Argon2id."""
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against an Argon2 hash."""
    try:
        return password_hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def create_access_token(
    subject: Union[str, Any],
    role: str = "viewer",
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generate a signed JWT access token with JTI and standard claims."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    jti = uuid.uuid4().hex
    payload = {
        "sub": str(subject),
        "role": role,
        "name": full_name or "",
        "email": email or "",
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
    }
    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token signature, expiration, and algorithm."""
    try:
        decoded_payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return decoded_payload
    except jwt.PyJWTError:
        return None


def is_token_revoked(db: Session, jti: str) -> bool:
    """Check if a token has been revoked via logout."""
    if not jti:
        return False
    revoked = db.scalar(select(RevokedToken).where(RevokedToken.jti == jti))
    return revoked is not None


def revoke_token(db: Session, jti: str, expires_at_timestamp: Optional[int] = None) -> None:
    """Store revoked token JTI so it cannot be used again."""
    if not jti:
        return
    if expires_at_timestamp:
        exp_dt = datetime.fromtimestamp(expires_at_timestamp, tz=timezone.utc)
    else:
        exp_dt = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    existing = db.scalar(select(RevokedToken).where(RevokedToken.jti == jti))
    if not existing:
        revoked = RevokedToken(jti=jti, expires_at=exp_dt)
        db.add(revoked)
        db.commit()


def create_password_reset_token(email: str, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a short-lived token for password reset."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=15))
    payload = {
        "sub": email.lower().strip(),
        "purpose": "password_reset",
        "jti": uuid.uuid4().hex,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_password_reset_token(token: str) -> Optional[str]:
    """Decode and validate password reset token, returning normalized email."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        if payload.get("purpose") != "password_reset":
            return None
        return payload.get("sub")
    except jwt.PyJWTError:
        return None
