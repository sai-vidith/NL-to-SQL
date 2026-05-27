"""
Nexus — Generic async base repository.

Provides standard CRUD operations using SQLAlchemy 2.0 async syntax.
All concrete repositories should inherit from BaseRepository[T].
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar
from uuid import UUID

import structlog
from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Generic async repository with standard CRUD operations.

    Parameters
    ----------
    session : AsyncSession
        The async SQLAlchemy session bound to the current request.
    model : type[T]
        The ORM model class this repository manages.
    """

    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        self.session = session
        self.model = model

    # ── Read ─────────────────────────────────────────────────────

    async def get_by_id(self, id: UUID) -> T | None:
        """Fetch a single record by its primary-key UUID."""
        stmt = select(self.model).where(self.model.id == id)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        """Return a paginated list of records.

        Parameters
        ----------
        skip : int
            Number of rows to skip (offset).
        limit : int
            Maximum number of rows to return.
        """
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self) -> int:
        """Return the total number of records in the table."""
        stmt = select(func.count()).select_from(self.model)  # type: ignore[arg-type]
        result = await self.session.execute(stmt)
        return result.scalar_one()

    # ── Create ───────────────────────────────────────────────────

    async def create(self, **kwargs: Any) -> T:
        """Insert a new record and return the created instance.

        Parameters
        ----------
        **kwargs
            Column-value pairs for the new row.
        """
        instance = self.model(**kwargs)  # type: ignore[call-arg]
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        logger.debug(
            "repository.create",
            model=self.model.__name__,  # type: ignore[attr-defined]
            id=str(getattr(instance, "id", None)),
        )
        return instance

    # ── Update ───────────────────────────────────────────────────

    async def update(self, id: UUID, **kwargs: Any) -> T | None:
        """Update a record by its primary-key UUID.

        Returns the refreshed instance, or ``None`` if not found.
        """
        # Filter out None values to avoid overwriting with nulls accidentally
        values = {k: v for k, v in kwargs.items() if v is not None}
        if not values:
            return await self.get_by_id(id)

        stmt = (
            sa_update(self.model)
            .where(self.model.id == id)  # type: ignore[attr-defined]
            .values(**values)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        instance = result.scalar_one_or_none()
        if instance is not None:
            await self.session.flush()
            logger.debug(
                "repository.update",
                model=self.model.__name__,  # type: ignore[attr-defined]
                id=str(id),
                fields=list(values.keys()),
            )
        return instance

    # ── Delete ───────────────────────────────────────────────────

    async def delete(self, id: UUID) -> bool:
        """Delete a record by its primary-key UUID.

        Returns ``True`` if a row was deleted, ``False`` otherwise.
        """
        stmt = (
            sa_delete(self.model)
            .where(self.model.id == id)  # type: ignore[attr-defined]
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        deleted = result.rowcount > 0  # type: ignore[union-attr]
        if deleted:
            logger.debug(
                "repository.delete",
                model=self.model.__name__,  # type: ignore[attr-defined]
                id=str(id),
            )
        return deleted
