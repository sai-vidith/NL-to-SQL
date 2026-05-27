"""
Nexus — Async database session configuration.

Provides two async engines:
  • app_engine  – full read-write access for application operations
  • ro_engine   – read-only access for executing user-generated SQL

Both expose async session generators compatible with FastAPI Depends().
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

settings = get_settings()

# ── Read-Write engine (application operations) ─────────────────────
app_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=5 if "memory" not in settings.database_url else None,
    max_overflow=10 if "memory" not in settings.database_url else None,
    pool_pre_ping=True,
    pool_recycle=300,
)

# ── Read-Only engine (executing generated SQL against biz tables) ──
# If enable_in_memory_db is set, use a completely isolated in-memory DB for rapid query speeds
ro_db_url = "sqlite+aiosqlite:///:memory:" if settings.enable_in_memory_db else settings.readonly_db_url
ro_engine = create_async_engine(
    ro_db_url,
    echo=settings.debug,
    pool_size=3 if "memory" not in ro_db_url else None,
    max_overflow=5 if "memory" not in ro_db_url else None,
    pool_pre_ping=True,
    pool_recycle=300,
    execution_options={"postgresql_readonly": True} if "sqlite" not in ro_db_url else {},
)

# ── Session factories ──────────────────────────────────────────────
AsyncSessionFactory = async_sessionmaker(
    bind=app_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

AsyncReadOnlySessionFactory = async_sessionmaker(
    bind=ro_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── FastAPI dependency generators ──────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session bound to the read-write engine."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_readonly_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session bound to the read-only engine."""
    async with AsyncReadOnlySessionFactory() as session:
        yield session
