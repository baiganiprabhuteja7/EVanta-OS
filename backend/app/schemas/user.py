from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


VALID_ROLES = ["admin", "manager", "viewer", "read_only"]


class UserBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    username: Optional[str] = Field(None, max_length=100)
    role: str = "viewer"
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=6, max_length=100)


class UserStatusUpdate(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    username: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
