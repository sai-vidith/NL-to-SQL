"""
Routes for managing saved queries (bookmarks) for fast re-execution.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import get_current_user
from app.database.repositories.conversation import ConversationRepository
from app.database.repositories.saved_query import SavedQueryRepository
from app.database.session import get_db
from app.schemas.auth import UserProfile
from app.schemas.common import (
    SavedQueryResponse,
    SaveQueryRequest,
    UpdateSavedQueryRequest,
)

router = APIRouter()


@router.post("", response_model=SavedQueryResponse, status_code=status.HTTP_201_CREATED)
async def save_query(
    payload: SaveQueryRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SavedQueryResponse:
    """Save/bookmark a query from conversation history."""
    convo_repo = ConversationRepository(db)
    convo = await convo_repo.get_by_id(payload.query_id)
    
    if not convo or convo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original query or conversation not found",
        )
        
    saved_repo = SavedQueryRepository(db)
    # Check if name already exists for this user
    existing = await saved_repo.get_by_name(current_user.id, payload.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A saved query with this name already exists",
        )
        
    saved = await saved_repo.save_query(
        user_id=current_user.id,
        name=payload.name,
        sql_query=convo.validated_sql,
        nl_question=convo.question,
        description=payload.description,
    )
    
    return SavedQueryResponse.model_validate(saved)


@router.get("", response_model=list[SavedQueryResponse])
async def get_saved_queries(
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SavedQueryResponse]:
    """Retrieve all bookmarked queries for the current user."""
    saved_repo = SavedQueryRepository(db)
    items = await saved_repo.get_by_user(current_user.id)
    return [SavedQueryResponse.model_validate(item) for item in items]


@router.patch("/{query_id}", response_model=SavedQueryResponse)
async def update_saved_query(
    query_id: UUID,
    payload: UpdateSavedQueryRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SavedQueryResponse:
    """Update metadata of a saved query."""
    saved_repo = SavedQueryRepository(db)
    saved = await saved_repo.get_by_id(query_id)
    
    if not saved or saved.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved query not found",
        )
        
    update_data = payload.model_dump(exclude_unset=True)
    updated = await saved_repo.update(query_id, **update_data)
    
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed to update saved query",
        )
        
    return SavedQueryResponse.model_validate(updated)


@router.delete("/{query_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_query(
    query_id: UUID,
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a saved query."""
    saved_repo = SavedQueryRepository(db)
    saved = await saved_repo.get_by_id(query_id)
    
    if not saved or saved.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved query not found",
        )
        
    await saved_repo.delete(query_id)
    from fastapi import Response
    return Response(status_code=status.HTTP_204_NO_CONTENT)
