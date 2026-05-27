"""
Pydantic schemas for Saved Queries, Export, and Admin.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


# ── Saved Queries ────────────────────────────────────────────────

class SaveQueryRequest(BaseModel):
    """Save a query for future re-use."""
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    query_id: UUID = Field(description="ID of the conversation/query to save")


class SavedQueryResponse(BaseModel):
    """Saved query details."""
    id: UUID
    name: str
    description: str | None
    sql_query: str
    nl_question: str
    is_public: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateSavedQueryRequest(BaseModel):
    """Update saved query metadata."""
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    is_public: bool | None = None


# ── Export ────────────────────────────────────────────────────────

class ExportFormat(str, Enum):
    CSV = "csv"
    EXCEL = "excel"


# ── Admin ────────────────────────────────────────────────────────

class UpdateUserRoleRequest(BaseModel):
    """Change a user's role."""
    role: str = Field(pattern=r"^(admin|analyst|viewer)$")


class AuditLogResponse(BaseModel):
    """Audit log entry."""
    id: UUID
    user_id: UUID | None
    action: str
    details: str | None
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PlatformStats(BaseModel):
    """Platform-wide statistics for admin dashboard."""
    total_users: int
    total_queries: int
    total_saved_queries: int
    queries_today: int
    avg_execution_time_ms: float
    top_intents: list[dict[str, int]]
    active_users_24h: int


# ── Common ───────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""
    items: list
    total: int
    page: int = 1
    page_size: int = 20


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    database: str = "connected"
    redis: str = "connected"
    llm: str = "available"
