"""Pydantic schemas for the /auth router."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from backend.config import settings


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=settings.password_min_length, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=8, max_length=512)


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = Field(default=None, max_length=512)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime


TokenResponse.model_rebuild()
