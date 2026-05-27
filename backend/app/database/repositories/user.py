"""
Nexus — User repository.

Handles all database operations for the User model, including
lookup by email/username/telegram_id, role management, and deactivation.
"""

from __future__ import annotations

from uuid import UUID

import structlog
from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.database.repositories.base import BaseRepository

logger = structlog.get_logger(__name__)


class UserRepository(BaseRepository[User]):
    """Async repository for :class:`User` operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    # ── Lookups ──────────────────────────────────────────────────

    async def get_by_email(self, email: str) -> User | None:
        """Find a user by their email address (case-insensitive)."""
        stmt = select(User).where(User.email == email.lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """Find a user by their username."""
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Find a user by their Telegram chat ID."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ── Create ───────────────────────────────────────────────────

    async def create_user(
        self,
        username: str,
        email: str,
        password_hash: str,
        role: str = "viewer",
        telegram_id: int | None = None,
    ) -> User:
        """Create and return a new user.

        Parameters
        ----------
        username : str
            Unique display name.
        email : str
            User email (stored lowercase).
        password_hash : str
            Pre-hashed password string.
        role : str
            Application role – ``viewer``, ``analyst``, or ``admin``.
        telegram_id : int | None
            Optional Telegram chat ID for bot integration.
        """
        user = await self.create(
            username=username,
            email=email.lower(),
            password_hash=password_hash,
            role=role,
            telegram_id=telegram_id,
        )
        logger.info("user.created", user_id=str(user.id), username=username)
        return user

    # ── Update helpers ───────────────────────────────────────────

    async def update_role(self, user_id: UUID, role: str) -> User | None:
        """Change a user's role.

        Returns the updated user or ``None`` if not found.
        """
        stmt = (
            sa_update(User)
            .where(User.id == user_id)
            .values(role=role)
            .returning(User)
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is not None:
            await self.session.flush()
            logger.info("user.role_updated", user_id=str(user_id), new_role=role)
        return user

    async def deactivate(self, user_id: UUID) -> bool:
        """Soft-deactivate a user by setting ``is_active`` to False.

        Returns ``True`` if the user was deactivated, ``False`` if not found.
        """
        stmt = (
            sa_update(User)
            .where(User.id == user_id, User.is_active.is_(True))
            .values(is_active=False)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        deactivated = result.rowcount > 0  # type: ignore[union-attr]
        if deactivated:
            logger.info("user.deactivated", user_id=str(user_id))
        return deactivated
