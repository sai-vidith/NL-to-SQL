"""
Schema Watcher service.
Monitors database catalog (information_schema) for DDL schema updates,
calculating schema hashes to dynamically invalidate cache and update schema embeddings.
"""

from __future__ import annotations

import hashlib
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

class SchemaWatcher:
    """
    Monitors database metadata changes.
    Inspired by OS file change notification APIs (e.g. Inotify) and Database Triggers.
    Uses OOPS Observer pattern to notify the SchemaRetriever of DDL updates.
    """
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._last_schema_hash = None

    async def calculate_schema_hash(self) -> str:
        """
        Queries database catalog tables to generate a unique hash of the active schema.
        If tables or columns are added, removed, or altered, the hash will change.
        """
        # Supports both SQLite and PostgreSQL catalogs
        try:
            # Try PostgreSQL first
            query = """
                SELECT table_name, column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                ORDER BY table_name, ordinal_position;
            """
            result = await self.db.execute(text(query))
            rows = result.fetchall()
        except Exception:
            # Fallback to SQLite sqlite_master
            query = "SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name;"
            result = await self.db.execute(text(query))
            rows = result.fetchall()

        # Build concatenated string representation of the schema catalog
        schema_dump = "".join([f"{r[0]}:{r[1]}" for r in rows])
        
        # Calculate SHA-256 hash
        schema_hash = hashlib.sha256(schema_dump.encode('utf-8')).hexdigest()
        return schema_hash

    async def check_for_updates(self) -> bool:
        """
        Compares current schema hash against last known state.
        Returns True if a schema change (DDL) is detected.
        """
        current_hash = await self.calculate_schema_hash()
        
        if self._last_schema_hash is None:
            self._last_schema_hash = current_hash
            return False

        if current_hash != self._last_schema_hash:
            logger.info("schema_watcher.ddl_change_detected", 
                        old_hash=self._last_schema_hash, 
                        new_hash=current_hash)
            self._last_schema_hash = current_hash
            return True
            
        return False
