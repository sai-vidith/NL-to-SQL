"""
Pydantic request/response schemas for Authentication.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ── Request Schemas ──────────────────────────────────────────────

class UserRegister(BaseModel):
    """Registration request payload."""
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)


class UserLogin(BaseModel):
    """Login request payload."""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


# ── Response Schemas ─────────────────────────────────────────────

class TokenResponse(BaseModel):
    """JWT token pair response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token expiry in seconds")


class UserProfile(BaseModel):
    """User profile response."""
    id: UUID
    username: str
    email: str
    role: str
    is_active: bool
    telegram_connected: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}
