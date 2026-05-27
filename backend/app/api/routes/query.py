"""
Query endpoints for submitting natural language queries, getting query details,
retrieving suggestion chips, and view recent/history items.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import get_current_user
from app.database.repositories.conversation import ConversationRepository
from app.database.session import get_db, get_readonly_db
from app.schemas.auth import UserProfile
from app.schemas.query import (
    DEFAULT_SUGGESTIONS,
    ChartConfig,
    ChartType,
    QueryHistoryItem,
    QueryHistoryResponse,
    QueryRequest,
    QueryResponse,
    QuerySuggestion,
)

router = APIRouter()


from app.services.query import QueryService

@router.post("", response_model=QueryResponse)
async def submit_query(
    payload: QueryRequest,
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ro_db: AsyncSession = Depends(get_readonly_db),
) -> QueryResponse:
    """
    Submit a natural language business question.
    Generates, validates, and executes the SQL query, saving the conversation history.
    """
    service = QueryService(db=db, ro_db=ro_db)
    return await service.execute_nl_query(
        user_id=current_user.id,
        question=payload.question,
        session_id=payload.session_id,
    )


@router.get("/suggestions", response_model=list[QuerySuggestion])
async def get_suggestions(
    current_user: UserProfile = Depends(get_current_user),
) -> list[QuerySuggestion]:
    """Retrieve pre-built suggestion queries for the home dashboard."""
    return DEFAULT_SUGGESTIONS


@router.get("/history", response_model=QueryHistoryResponse)
async def get_query_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QueryHistoryResponse:
    """Retrieve a paginated list of past queries submitted by the current user."""
    convo_repo = ConversationRepository(db)
    skip = (page - 1) * page_size
    
    items = await convo_repo.get_by_user(current_user.id, skip=skip, limit=page_size)
    total = await convo_repo.count_by_user(current_user.id)
    
    history_items = [
        QueryHistoryItem(
            id=item.id,
            question=item.question,
            intent=item.intent_category,
            row_count=item.row_count,
            execution_time_ms=item.execution_time_ms,
            summary=item.result_summary,
            error_message=item.error_message,
            created_at=item.created_at,
        )
        for item in items
    ]
    
    return QueryHistoryResponse(
        items=history_items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{query_id}", response_model=QueryResponse)
async def get_query_details(
    query_id: UUID,
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QueryResponse:
    """Retrieve complete details for a specific query."""
    convo_repo = ConversationRepository(db)
    convo = await convo_repo.get_by_id(query_id)
    
    if not convo or convo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query conversation not found",
        )
        
    # Return mock row / column metadata for mock presentation
    columns = ["label", "value"]
    rows = [["Metric", 100.0]]
    
    return QueryResponse(
        id=convo.id,
        question=convo.question,
        intent=convo.intent_category,
        generated_sql=convo.generated_sql,
        columns=columns,
        rows=rows,
        row_count=convo.row_count,
        execution_time_ms=convo.execution_time_ms,
        summary=convo.result_summary,
        chart_config=None,
        session_id=convo.session_id,
        created_at=convo.created_at,
    )
