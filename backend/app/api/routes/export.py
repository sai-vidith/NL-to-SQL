"""
Export routes for exporting query results to CSV and Excel formats.
"""

from __future__ import annotations

import csv
import io
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import get_current_user
from app.database.repositories.conversation import ConversationRepository
from app.database.session import get_db
from app.schemas.auth import UserProfile
from app.schemas.common import ExportFormat

router = APIRouter()


@router.get("/{query_id}")
async def export_query_results(
    query_id: UUID,
    format: ExportFormat = Query(default=ExportFormat.CSV),
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export the results of a past query to CSV or Excel.
    """
    convo_repo = ConversationRepository(db)
    convo = await convo_repo.get_by_id(query_id)
    
    if not convo or convo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query results not found",
        )
        
    # In a full setup, row results would be fetched from database or from conversation JSON metadata.
    # For now, we mock exporting the results in the appropriate format.
    columns = ["Metric", "Value"]
    rows = [
        ["Total Revenue", 154020.50],
        ["Active Customers", 1250],
        ["Orders Processed", 423],
    ]
    
    filename_base = f"nexus_export_{query_id.hex[:8]}"
    
    if format == ExportFormat.CSV:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        writer.writerows(rows)
        output.seek(0)
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename_base}.csv"},
        )
        
    elif format == ExportFormat.EXCEL:
        wb = Workbook()
        ws = wb.active
        ws.title = "Nexus Results"
        
        ws.append(columns)
        for row in rows:
            ws.append(row)
            
        file_stream = io.BytesIO()
        wb.save(file_stream)
        file_stream.seek(0)
        
        return StreamingResponse(
            file_stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename_base}.xlsx"},
        )
        
    raise HTTPException(status_code=400, detail="Invalid export format")
