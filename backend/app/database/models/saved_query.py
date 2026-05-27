"""
Nexus — SavedQuery ORM model.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.database.models.user import User


class SavedQuery(TimestampMixin, Base):
    __tablename__ = "saved_queries"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sql_query: Mapped[str] = mapped_column(Text, nullable=False)
    nl_question: Mapped[str] = mapped_column(Text, nullable=False)
    is_public: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false",
    )

    # ── Relationships ──────────────────────────────────────────────
    user: Mapped[User] = relationship("User", back_populates="saved_queries")

    __table_args__ = (
        Index("ix_saved_queries_user_id", "user_id"),
        Index("ix_saved_queries_is_public", "is_public"),
    )

    def __repr__(self) -> str:
        return f"<SavedQuery id={self.id!s} name={self.name!r} public={self.is_public}>"
