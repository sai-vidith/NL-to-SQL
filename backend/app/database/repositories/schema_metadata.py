"""
Nexus — Schema metadata & few-shot example repositories.

Handles pgvector cosine-similarity search for RAG-style retrieval of
relevant table/column metadata and few-shot SQL examples during query
generation.
"""

from __future__ import annotations

from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.schema_metadata import FewShotExample, SchemaMetadata
from app.database.repositories.base import BaseRepository

logger = structlog.get_logger(__name__)


# ═════════════════════════════════════════════════════════════════
#  Schema Metadata Repository
# ═════════════════════════════════════════════════════════════════


class SchemaMetadataRepository(BaseRepository[SchemaMetadata]):
    """Async repository for :class:`SchemaMetadata` operations.

    Supports pgvector cosine-similarity search for RAG retrieval of
    table/column descriptions relevant to a user's natural-language question.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SchemaMetadata)

    # ── Lookups ──────────────────────────────────────────────────

    async def get_by_table(self, table_name: str) -> list[SchemaMetadata]:
        """Return all metadata rows for a given table."""
        stmt = (
            select(SchemaMetadata)
            .where(SchemaMetadata.table_name == table_name)
            .order_by(SchemaMetadata.column_name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_intent(self, intent_category: str) -> list[SchemaMetadata]:
        """Return metadata rows tagged with a specific intent category."""
        stmt = (
            select(SchemaMetadata)
            .where(SchemaMetadata.intent_category == intent_category)
            .order_by(SchemaMetadata.table_name, SchemaMetadata.column_name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── Vector search ────────────────────────────────────────────

    async def search_similar(
        self, embedding: list[float], limit: int = 5
    ) -> list[SchemaMetadata]:
        """Find schema metadata closest to the query embedding.

        Uses pgvector's ``<=>`` cosine distance operator and orders results
        by ascending distance (most similar first).

        Parameters
        ----------
        embedding : list[float]
            Query embedding vector (must match the stored dimension).
        limit : int
            Maximum number of results to return.
        """
        distance = SchemaMetadata.embedding.cosine_distance(embedding)
        stmt = (
            select(SchemaMetadata)
            .order_by(distance)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── Upsert ───────────────────────────────────────────────────

    async def upsert_metadata(
        self,
        table_name: str,
        column_name: str,
        data_type: str,
        description: str,
        business_context: str,
        sample_values: list[str],
        embedding: list[float],
        intent_category: str,
    ) -> SchemaMetadata:
        """Insert or update schema metadata for a table/column pair.

        If a row with the same ``(table_name, column_name)`` exists it is
        updated in place; otherwise a new row is created.

        Parameters
        ----------
        table_name : str
            Database table name.
        column_name : str
            Column name within the table.
        data_type : str
            SQL data type of the column.
        description : str
            Human-readable column description.
        business_context : str
            Business-domain explanation for the column.
        sample_values : list[str]
            Representative sample values.
        embedding : list[float]
            Embedding vector for similarity search.
        intent_category : str
            Intent category tag (e.g. ``revenue``, ``inventory``).
        """
        # Check for existing row
        stmt = select(SchemaMetadata).where(
            SchemaMetadata.table_name == table_name,
            SchemaMetadata.column_name == column_name,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is not None:
            existing.data_type = data_type
            existing.description = description
            existing.business_context = business_context
            existing.sample_values = sample_values
            existing.embedding = embedding
            existing.intent_category = intent_category
            await self.session.flush()
            await self.session.refresh(existing)
            logger.info(
                "schema_metadata.updated",
                table=table_name,
                column=column_name,
            )
            return existing

        metadata = await self.create(
            table_name=table_name,
            column_name=column_name,
            data_type=data_type,
            description=description,
            business_context=business_context,
            sample_values=sample_values,
            embedding=embedding,
            intent_category=intent_category,
        )
        logger.info(
            "schema_metadata.created",
            metadata_id=str(metadata.id),
            table=table_name,
            column=column_name,
        )
        return metadata


# ═════════════════════════════════════════════════════════════════
#  Few-Shot Example Repository
# ═════════════════════════════════════════════════════════════════


class FewShotRepository(BaseRepository[FewShotExample]):
    """Async repository for :class:`FewShotExample` operations.

    Supports pgvector cosine-similarity search for retrieving the most
    relevant NL→SQL examples during prompt construction.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, FewShotExample)

    # ── Vector search ────────────────────────────────────────────

    async def search_similar(
        self, embedding: list[float], limit: int = 3
    ) -> list[FewShotExample]:
        """Find few-shot examples closest to the query embedding.

        Uses pgvector's ``<=>`` cosine distance operator and orders results
        by ascending distance (most similar first).

        Parameters
        ----------
        embedding : list[float]
            Query embedding vector.
        limit : int
            Maximum number of examples to return.
        """
        distance = FewShotExample.embedding.cosine_distance(embedding)
        stmt = (
            select(FewShotExample)
            .order_by(distance)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── Lookups ──────────────────────────────────────────────────

    async def get_by_intent(
        self, intent_category: str, limit: int = 3
    ) -> list[FewShotExample]:
        """Return few-shot examples filtered by intent category."""
        stmt = (
            select(FewShotExample)
            .where(FewShotExample.intent_category == intent_category)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── Create ───────────────────────────────────────────────────

    async def add_example(
        self,
        question: str,
        sql_query: str,
        intent_category: str,
        explanation: str,
        embedding: list[float],
    ) -> FewShotExample:
        """Add a new few-shot NL→SQL example.

        Parameters
        ----------
        question : str
            Natural-language question.
        sql_query : str
            Corresponding SQL query.
        intent_category : str
            Intent tag for categorical filtering.
        explanation : str
            Step-by-step reasoning for the SQL.
        embedding : list[float]
            Embedding vector for similarity retrieval.
        """
        example = await self.create(
            question=question,
            sql_query=sql_query,
            intent_category=intent_category,
            explanation=explanation,
            embedding=embedding,
        )
        logger.info(
            "few_shot.created",
            example_id=str(example.id),
            intent=intent_category,
        )
        return example
