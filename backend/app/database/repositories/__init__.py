"""
Nexus — Repository layer.

Re-exports all repository classes for convenient imports:
    from app.database.repositories import UserRepository, ConversationRepository, ...
"""

from __future__ import annotations

from app.database.repositories.audit_log import AuditLogRepository
from app.database.repositories.base import BaseRepository
from app.database.repositories.conversation import ConversationRepository
from app.database.repositories.saved_query import SavedQueryRepository
from app.database.repositories.schema_metadata import (
    FewShotRepository,
    SchemaMetadataRepository,
)
from app.database.repositories.user import UserRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "ConversationRepository",
    "SavedQueryRepository",
    "AuditLogRepository",
    "SchemaMetadataRepository",
    "FewShotRepository",
]
