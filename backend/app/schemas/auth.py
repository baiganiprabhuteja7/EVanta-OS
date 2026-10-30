from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.user import UserResponse


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    full_name: str
    email: str
    username: Optional[str] = None


TokenResponse = Token


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    jti: Optional[str] = None
    exp: Optional[int] = None


class LoginRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: str
    username: Optional[str] = None
    password: str = Field(..., min_length=6, max_length=100)
    role: Optional[str] = Field(default="viewer")


UserCreate = RegisterRequest


class PasswordResetRequest(BaseModel):
    email: str = Field(..., description="Email address or username of account to reset")


class PasswordResetConfirm(BaseModel):
    token: str = Field(..., description="Password reset verification token")
    new_password: str = Field(..., min_length=6, description="New secure password")


class PasswordResetResponse(BaseModel):
    message: str
    email_configured: bool = False
