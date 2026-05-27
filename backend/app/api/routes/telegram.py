"""
Telegram Bot webhook receiver and message router endpoints.
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Request, Response, status

logger = structlog.get_logger()
router = APIRouter()


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
) -> Response:
    """
    Handle incoming updates from Telegram Bot API.
    """
    try:
        update_data = await request.json()
        logger.info("telegram.webhook_update", update=update_data)
        
        from app.services.telegram import TelegramService
        tg_service = TelegramService.get_instance()
        await tg_service.process_update(update_data)
        
        return Response(status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.error("telegram.webhook_error", error=str(e))
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

