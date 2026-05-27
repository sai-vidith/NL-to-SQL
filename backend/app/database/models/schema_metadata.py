"""
Nexus — SchemaMetadata & FewShotExample ORM models.

These models power the RAG pipeline:
  • SchemaMetadata  – vector-indexed catalogue of every table/column in the
                      business schema, enabling semantic retrieval of relevant
                      schema context for NL-to-SQL generation.
  • FewShotExample – curated NL→SQL pairs with embeddings, used for dynamic
                      few-shot prompt construction.
"""

from __future__ import annotations

import uuid
from datetime import datetime

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    # Fallback dummy class representing Vector representation for SQLite/non-Postgres setups
    from sqlalchemy import String as Vector

from sqlalchemy import Boolean, DateTime, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base


class SchemaMetadata(Base):
    __tablename__ = "schema_metadata"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4,
    )
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    column_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    data_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    business_context: Mapped[str] = mapped_column(Text, nullable=False)
    sample_values: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(768), nullable=True,
    )
    intent_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_schema_metadata_table_name", "table_name"),
        Index("ix_schema_metadata_intent_category", "intent_category"),
    )

    def __repr__(self) -> str:
        col = f".{self.column_name}" if self.column_name else ""
        return f"<SchemaMetadata {self.table_name}{col}>"


class FewShotExample(Base):
    __tablename__ = "few_shot_examples"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    sql_query: Mapped[str] = mapped_column(Text, nullable=False)
    intent_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(768), nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    __table_args__ = (
        Index("ix_few_shot_examples_intent_category", "intent_category"),
        Index("ix_few_shot_examples_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return (
            f"<FewShotExample id={self.id!s} "
            f"intent={self.intent_category!r} active={self.is_active}>"
        )
