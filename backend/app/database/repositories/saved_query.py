"""
Nexus — Saved query repository.

Handles CRUD and lookup for user-saved SQL queries, including
per-user listings, name-based dedup, and public query discovery.
"""

from __future__ import annotations

from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.saved_query import SavedQuery
from app.database.repositories.base import BaseRepository

logger = structlog.get_logger(__name__)


class SavedQueryRepository(BaseRepository[SavedQuery]):
    """Async repository for :class:`SavedQuery` operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SavedQuery)

    # ── Queries ──────────────────────────────────────────────────

    async def get_by_user(self, user_id: UUID) -> list[SavedQuery]:
        """Return all saved queries belonging to a user."""
        stmt = (
            select(SavedQuery)
            .where(SavedQuery.user_id == user_id)
            .order_by(SavedQuery.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_name(self, user_id: UUID, name: str) -> SavedQuery | None:
        """Find a saved query by user and name (unique pair)."""
        stmt = select(SavedQuery).where(
            SavedQuery.user_id == user_id,
            SavedQuery.name == name,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_public(self) -> list[SavedQuery]:
        """Return all publicly shared saved queries."""
        stmt = (
            select(SavedQuery)
            .where(SavedQuery.is_public.is_(True))
            .order_by(SavedQuery.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── Create ───────────────────────────────────────────────────

    async def save_query(
        self,
        user_id: UUID,
        name: str,
        sql_query: str,
        nl_question: str,
        description: str | None = None,
    ) -> SavedQuery:
        """Save a named query for later reuse.

        Parameters
        ----------
        user_id : UUID
            Owner of the saved query.
        name : str
            Human-readable label for the query.
        sql_query : str
            The SQL to persist.
        nl_question : str
            Original natural-language question that generated the SQL.
        description : str | None
            Optional long-form description.
        """
        saved = await self.create(
            user_id=user_id,
            name=name,
            sql_query=sql_query,
            nl_question=nl_question,
            description=description,
        )
        logger.info(
            "saved_query.created",
            query_id=str(saved.id),
            user_id=str(user_id),
            name=name,
        )
        return saved
