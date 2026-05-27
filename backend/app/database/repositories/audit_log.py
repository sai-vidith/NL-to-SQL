"""
Nexus — Audit log repository.

Provides append-only logging of user actions and system events,
plus retrieval by user and recency.
"""

from __future__ import annotations

from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.audit_log import AuditLog
from app.database.repositories.base import BaseRepository

logger = structlog.get_logger(__name__)


class AuditLogRepository(BaseRepository[AuditLog]):
    """Async repository for :class:`AuditLog` operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AuditLog)

    # ── Write ────────────────────────────────────────────────────

    async def log_action(
        self,
        user_id: UUID | None,
        action: str,
        details: str | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        """Record an auditable action.

        Parameters
        ----------
        user_id : UUID | None
            The acting user, or ``None`` for system/anonymous events.
        action : str
            Short identifier for the action (e.g. ``user.login``, ``query.execute``).
        details : str | None
            Free-form JSON or text with extra context.
        ip_address : str | None
            Client IP address, if available.
        """
        entry = await self.create(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=ip_address,
        )
        logger.debug(
            "audit.logged",
            audit_id=str(entry.id),
            action=action,
            user_id=str(user_id) if user_id else None,
        )
        return entry

    # ── Queries ──────────────────────────────────────────────────

    async def get_by_user(
        self, user_id: UUID, skip: int = 0, limit: int = 50
    ) -> list[AuditLog]:
        """Return paginated audit entries for a specific user."""
        stmt = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent(self, limit: int = 50) -> list[AuditLog]:
        """Return the most recent audit log entries across all users."""
        stmt = (
            select(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
