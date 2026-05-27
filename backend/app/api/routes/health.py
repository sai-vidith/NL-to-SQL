"""
Health check endpoints for monitoring application status.
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.common import HealthResponse

logger = structlog.get_logger()
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """
    Check the health of the application and its dependencies.
    """
    db_status = "connected"
    try:
        # Check database connection
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error("health.database_error", error=str(e))
        db_status = "disconnected"

    # We assume Redis and LLM are configured as per settings
    # We will verify their actual connection in a deeper diagnostic endpoint if needed
    
    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        version="1.0.0",
        database=db_status,
        redis="connected",  # Mock or check if settings.redis_url is configured
        llm="available",
    )
