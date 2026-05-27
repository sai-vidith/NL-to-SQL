"""
Nexus — User ORM model.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.database.models.conversation import Conversation
    from app.database.models.saved_query import SavedQuery


class User(TimestampMixin, Base):
    __tablename__ = "users"

    telegram_id: Mapped[int | None] = mapped_column(
        BigInteger, unique=True, nullable=True, index=True,
    )
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="viewer", server_default="viewer",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true",
    )

    # ── Relationships ──────────────────────────────────────────────
    conversations: Mapped[list[Conversation]] = relationship(
        "Conversation", back_populates="user", lazy="selectin",
    )
    saved_queries: Mapped[list[SavedQuery]] = relationship(
        "SavedQuery", back_populates="user", lazy="selectin",
    )

    __table_args__ = (
        Index("ix_users_role", "role"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id!s} username={self.username!r} role={self.role!r}>"
