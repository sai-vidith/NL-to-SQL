"""
Nexus — Database models package.

All models are imported here so that:
  1. Alembic ``env.py`` can discover them via ``Base.metadata``
  2. Application code can do:  ``from app.database.models import User, Conversation, ...``
"""

from __future__ import annotations

from app.database.models.base import Base, TimestampMixin

# ── Platform models ────────────────────────────────────────────────
from app.database.models.user import User
from app.database.models.conversation import Conversation
from app.database.models.saved_query import SavedQuery
from app.database.models.audit_log import AuditLog
from app.database.models.schema_metadata import FewShotExample, SchemaMetadata

# ── Business domain models ─────────────────────────────────────────
from app.database.models.business import (
    BizCustomer,
    BizOrder,
    BizOrderItem,
    BizPayment,
    BizProduct,
    BizReview,
    BizSeller,
)

__all__ = [
    "Base",
    "TimestampMixin",
    # platform
    "User",
    "Conversation",
    "SavedQuery",
    "AuditLog",
    "SchemaMetadata",
    "FewShotExample",
    # business
    "BizCustomer",
    "BizProduct",
    "BizOrder",
    "BizOrderItem",
    "BizPayment",
    "BizSeller",
    "BizReview",
]
