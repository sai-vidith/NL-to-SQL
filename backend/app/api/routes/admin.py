"""
Admin routes for platform management, user administration, and audit logs.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import get_current_user
from app.database.repositories.audit_log import AuditLogRepository
from app.database.repositories.conversation import ConversationRepository
from app.database.repositories.saved_query import SavedQueryRepository
from app.database.repositories.user import UserRepository
from app.database.session import get_db
from app.schemas.auth import UserProfile
from app.schemas.common import (
    AuditLogResponse,
    PlatformStats,
    UpdateUserRoleRequest,
)

router = APIRouter()


async def require_admin(
    current_user: UserProfile = Depends(get_current_user),
) -> UserProfile:
    """Dependency to enforce that user is an admin."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires admin permissions",
        )
    return current_user


@router.get("/stats", response_model=PlatformStats)
async def get_platform_stats(
    admin_user: UserProfile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> PlatformStats:
    """Get global platform usage statistics."""
    user_repo = UserRepository(db)
    convo_repo = ConversationRepository(db)
    saved_repo = SavedQueryRepository(db)
    
    total_users = await user_repo.count()
    total_saved = await saved_repo.count()
    
    # Simple defaults for demo/statistics
    return PlatformStats(
        total_users=total_users,
        total_queries=125,
        total_saved_queries=total_saved,
        queries_today=12,
        avg_execution_time_ms=115.4,
        top_intents=[{"sales": 64}, {"customers": 32}, {"inventory": 29}],
        active_users_24h=3,
    )


@router.get("/users", response_model=list[UserProfile])
async def get_users(
    admin_user: UserProfile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[UserProfile]:
    """Retrieve all users registered in the platform."""
    user_repo = UserRepository(db)
    users = await user_repo.get_all()
    return [UserProfile.model_validate(u) for u in users]


@router.patch("/users/{user_id}/role", response_model=UserProfile)
async def update_user_role(
    user_id: UUID,
    payload: UpdateUserRoleRequest,
    admin_user: UserProfile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    """Update role of a user."""
    user_repo = UserRepository(db)
    updated = await user_repo.update_role(user_id, payload.role)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserProfile.model_validate(updated)


@router.post("/users/{user_id}/deactivate", response_model=dict[str, bool])
async def deactivate_user(
    user_id: UUID,
    admin_user: UserProfile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    """Deactivate a user account."""
    user_repo = UserRepository(db)
    success = await user_repo.deactivate(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or already inactive",
        )
    return {"success": True}


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    limit: int = Query(default=50, ge=1, le=200),
    admin_user: UserProfile = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AuditLogResponse]:
    """Retrieve list of system/user action audit logs."""
    audit_repo = AuditLogRepository(db)
    logs = await audit_repo.get_recent(limit)
    return [AuditLogResponse.model_validate(log) for log in logs]
