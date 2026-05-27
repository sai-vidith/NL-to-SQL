"""
Nexus — Conversation repository.

Manages NL-to-SQL conversation records: per-user history, session grouping,
recency queries, full-text search via ILIKE, and per-user counts.
"""

from __future__ import annotations

from uuid import UUID

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.conversation import Conversation
from app.database.repositories.base import BaseRepository

logger = structlog.get_logger(__name__)


class ConversationRepository(BaseRepository[Conversation]):
    """Async repository for :class:`Conversation` operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Conversation)

    # ── Queries ──────────────────────────────────────────────────

    async def get_by_user(
        self, user_id: UUID, skip: int = 0, limit: int = 20
    ) -> list[Conversation]:
        """Return paginated conversations for a specific user."""
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_session(
        self, session_id: UUID, limit: int = 10
    ) -> list[Conversation]:
        """Return conversations belonging to a logical session."""
        stmt = (
            select(Conversation)
            .where(Conversation.session_id == session_id)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent(
        self, user_id: UUID, limit: int = 5
    ) -> list[Conversation]:
        """Return the most recent conversations for a user."""
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_user(self, user_id: UUID) -> int:
        """Count total conversations for a user."""
        stmt = (
            select(func.count())
            .select_from(Conversation)
            .where(Conversation.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def search(self, user_id: UUID, query: str) -> list[Conversation]:
        """Search conversations by question text using ILIKE.

        Parameters
        ----------
        user_id : UUID
            Restrict results to this user.
        query : str
            Free-text search term matched against the ``question`` column.
        """
        pattern = f"%{query}%"
        stmt = (
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
                Conversation.question.ilike(pattern),
            )
            .order_by(Conversation.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── Create ───────────────────────────────────────────────────

    async def create_conversation(
        self,
        user_id: UUID,
        question: str,
        intent_category: str,
        generated_sql: str,
        validated_sql: str,
        result_summary: str,
        row_count: int,
        execution_time_ms: float,
        response_text: str,
        session_id: UUID | None = None,
        error_message: str | None = None,
    ) -> Conversation:
        """Persist a full NL-to-SQL conversation turn.

        Parameters
        ----------
        user_id : UUID
            The user who asked the question.
        question : str
            The natural-language question submitted.
        intent_category : str
            Classified intent (e.g. ``revenue``, ``inventory``).
        generated_sql : str
            Raw SQL produced by the LLM.
        validated_sql : str
            SQL after safety validation.
        result_summary : str
            Human-readable summary of query results.
        row_count : int
            Number of rows returned.
        execution_time_ms : float
            Query execution duration in milliseconds.
        response_text : str
            Final response sent back to the user.
        session_id : UUID | None
            Optional grouping identifier for multi-turn sessions.
        error_message : str | None
            Error details if the query failed.
        """
        conversation = await self.create(
            user_id=user_id,
            question=question,
            intent_category=intent_category,
            generated_sql=generated_sql,
            validated_sql=validated_sql,
            result_summary=result_summary,
            row_count=row_count,
            execution_time_ms=execution_time_ms,
            response_text=response_text,
            session_id=session_id,
            error_message=error_message,
        )
        logger.info(
            "conversation.created",
            conversation_id=str(conversation.id),
            user_id=str(user_id),
            intent=intent_category,
        )
        return conversation
