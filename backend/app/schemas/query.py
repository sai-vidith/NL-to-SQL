"""
Pydantic request/response schemas for NL-to-SQL Queries.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────

class IntentCategory(str, Enum):
    SALES = "sales"
    FINANCE = "finance"
    INVENTORY = "inventory"
    CUSTOMERS = "customers"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    GENERAL = "general"


class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    DOUGHNUT = "doughnut"
    HORIZONTAL_BAR = "horizontalBar"
    NONE = "none"


# ── Request Schemas ──────────────────────────────────────────────

class QueryRequest(BaseModel):
    """Submit a natural language query."""
    question: str = Field(
        min_length=3,
        max_length=1000,
        description="Natural language business question",
        examples=["Show total revenue by state for last quarter"],
    )
    session_id: UUID | None = Field(
        default=None,
        description="Session ID for multi-turn conversations",
    )


class ChartRequest(BaseModel):
    """Request chart generation for query results."""
    chart_type: ChartType = ChartType.BAR
    x_column: str
    y_column: str
    title: str | None = None
    color_scheme: str | None = None


# ── Response Schemas ─────────────────────────────────────────────

class ChartConfig(BaseModel):
    """Chart.js configuration for frontend rendering."""
    chart_type: ChartType
    labels: list[str]
    datasets: list[dict[str, Any]]
    title: str
    x_label: str | None = None
    y_label: str | None = None


class QueryResponse(BaseModel):
    """Full query result response."""
    id: UUID
    question: str
    intent: str
    generated_sql: str
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    execution_time_ms: float
    summary: str
    chart_config: ChartConfig | None = None
    session_id: UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class QueryHistoryItem(BaseModel):
    """Compact query record for history listing."""
    id: UUID
    question: str
    intent: str
    row_count: int
    execution_time_ms: float
    summary: str | None = None
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class QueryHistoryResponse(BaseModel):
    """Paginated query history."""
    items: list[QueryHistoryItem]
    total: int
    page: int
    page_size: int


# ── Smart Suggestions ────────────────────────────────────────────

class QuerySuggestion(BaseModel):
    """Pre-built query suggestion for the dashboard."""
    text: str
    category: IntentCategory
    icon: str = "💡"


# Default suggestions for the dashboard
DEFAULT_SUGGESTIONS: list[QuerySuggestion] = [
    QuerySuggestion(text="Show total revenue for this month", category=IntentCategory.SALES, icon="💰"),
    QuerySuggestion(text="Top 10 customers by order value", category=IntentCategory.CUSTOMERS, icon="👥"),
    QuerySuggestion(text="Product categories with highest returns", category=IntentCategory.INVENTORY, icon="📦"),
    QuerySuggestion(text="Monthly sales trend for 2025", category=IntentCategory.SALES, icon="📈"),
    QuerySuggestion(text="Average delivery time by shipping mode", category=IntentCategory.OPERATIONS, icon="🚚"),
    QuerySuggestion(text="Revenue breakdown by payment method", category=IntentCategory.FINANCE, icon="💳"),
    QuerySuggestion(text="States with most active customers", category=IntentCategory.MARKETING, icon="🗺️"),
    QuerySuggestion(text="Products that have never been ordered", category=IntentCategory.INVENTORY, icon="⚠️"),
]
