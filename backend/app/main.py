"""
Nexus — NL-to-SQL Analytics Platform
FastAPI Application Factory

This is the main entry point for the application.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.exceptions import NexusError

# Configure structlog for JSON logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if get_settings().debug else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(0),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle — startup and shutdown."""
    settings = get_settings()
    logger.info(
        "nexus.startup",
        app_name=settings.app_name,
        environment=settings.app_env,
        debug=settings.debug,
    )

    # Initialize database tables (for development)
    if settings.debug or settings.enable_in_memory_db:
        from app.database.session import app_engine, ro_engine
        from app.database.models import Base
        async with app_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # If in-memory database is active, build business tables structure inside RAM ro_engine database
        if settings.enable_in_memory_db:
            async with ro_engine.begin() as ro_conn:
                await ro_conn.run_sync(Base.metadata.create_all)
            
            # Seed the newly initialized in-memory read-only business tables
            from app.database.seed import seed_data
            from app.database.session import AsyncReadOnlySessionFactory
            async with AsyncReadOnlySessionFactory() as seed_session:
                await seed_data(seed_session)
                
        logger.info("nexus.database", status="tables_created_and_initialized")

    # Initialize Telegram Bot
    from app.services.telegram import TelegramService
    tg_service = TelegramService.get_instance()
    await tg_service.initialize()

    yield

    # Shutdown Telegram Bot
    from app.services.telegram import TelegramService
    tg_service = TelegramService.get_instance()
    await tg_service.shutdown()

    # Shutdown database engines
    from app.database.session import app_engine, ro_engine
    await app_engine.dispose()
    if ro_engine:
        await ro_engine.dispose()
    logger.info("nexus.shutdown", status="complete")



def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=f"{settings.app_name} — NL-to-SQL Analytics",
        description=(
            "Enterprise-grade Natural Language to SQL Analytics Platform. "
            "Ask business questions in plain English, get instant data insights."
        ),
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request Logging Middleware ────────────────────────────
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        request_id = str(uuid4())[:8]
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start_time = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "http.request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(duration_ms, 2),
            client=request.client.host if request.client else "unknown",
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        return response

    # ── Global Exception Handler ─────────────────────────────
    @app.exception_handler(NexusError)
    async def nexus_error_handler(request: Request, exc: NexusError):
        logger.warning(
            "nexus.error",
            error=exc.message,
            status_code=exc.status_code,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.message,
                "details": exc.details,
                "status_code": exc.status_code,
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        logger.error(
            "nexus.unhandled_error",
            error=str(exc),
            path=request.url.path,
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "An unexpected error occurred",
                "status_code": 500,
            },
        )

    # ── Register API Routes ──────────────────────────────────
    from app.api.routes import health, auth, query, saved_queries, export, telegram
    app.include_router(health.router, prefix="/api/v1", tags=["Health"])
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(query.router, prefix="/api/v1/query", tags=["Queries"])
    app.include_router(saved_queries.router, prefix="/api/v1/saved-queries", tags=["Saved Queries"])
    app.include_router(export.router, prefix="/api/v1/export", tags=["Export"])
    app.include_router(telegram.router, prefix="/api/v1/telegram", tags=["Telegram"])


    # ── Serve Frontend Static Files ──────────────────────────
    import os
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    frontend_dist = os.path.join(root_dir, "frontend", "dist")
    frontend_legacy = os.path.join(root_dir, "frontend_legacy")
    frontend_source = os.path.join(root_dir, "frontend")
    
    if os.path.exists(frontend_dist):
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
    elif os.path.exists(frontend_legacy):
        app.mount("/", StaticFiles(directory=frontend_legacy, html=True), name="frontend")
    elif os.path.exists(frontend_source):
        app.mount("/", StaticFiles(directory=frontend_source, html=True), name="frontend")


    return app


# Application instance
app = create_app()
