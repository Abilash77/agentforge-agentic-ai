"""
AgentForge FastAPI Application Factory.

Assembles the full FastAPI application with:
- All routers registered
- CORS middleware
- Request logging middleware
- Exception handlers
- Database initialization on startup
- Task manager lifecycle management
- OpenAPI documentation
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agentforge.api.middleware import RequestLoggingMiddleware
from agentforge.api.routers import agents, auth, monitoring, projects
from agentforge.api.websocket import router as ws_router
from agentforge.config import get_config
from agentforge.database.database import close_db, init_db
from agentforge.monitoring.logger import get_logger
from agentforge.workflows.task_manager import get_task_manager

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # ── Startup ──────────────────────────────────────────────
    logger.info("🚀 AgentForge API starting up...")
    cfg = get_config()

    # Initialize SQLite database
    await init_db()
    logger.info("✓ Database initialized")

    # Start task manager
    task_manager = get_task_manager()
    await task_manager.start()
    logger.info("✓ Task manager started")

    logger.info(f"✓ AgentForge API ready on {cfg.api_host}:{cfg.api_port}")
    logger.info(f"  Environment: {cfg.environment}")
    logger.info(f"  Auth enabled: {cfg.auth.enable_auth}")
    logger.info(f"  LLM: {cfg.llm.api_type}/{cfg.llm.model}")

    yield

    # ── Shutdown ─────────────────────────────────────────────
    logger.info("🛑 AgentForge API shutting down...")
    await task_manager.stop()
    await close_db()
    logger.info("✓ Shutdown complete")


def create_app() -> FastAPI:
    """FastAPI application factory."""
    cfg = get_config()

    app = FastAPI(
        title="AgentForge API",
        description=(
            "🤖 **AgentForge** – Autonomous Multi-Agent Software Engineering Platform\n\n"
            "Transform any idea into production-ready software using 7 specialized AI agents.\n\n"
            "**Agents:** Product Manager → Solution Architect → Developer → QA → "
            "Documentation → DevOps → PPT\n\n"
            "**WebSocket:** Connect to `/ws/{project_id}` for real-time progress streaming."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware ────────────────────────────────────────────
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if not cfg.is_production else ["http://localhost:8501"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception Handlers ───────────────────────────────────
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Resource not found", "path": str(request.url.path)},
        )

    @app.exception_handler(500)
    async def server_error_handler(request: Request, exc):
        logger.error(f"Internal server error: {exc}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Internal server error"},
        )

    # ── Routers ──────────────────────────────────────────────
    app.include_router(projects.router)
    app.include_router(agents.router)
    app.include_router(auth.router)
    app.include_router(monitoring.router)
    app.include_router(ws_router)  # WebSocket endpoint

    # ── Health Check ─────────────────────────────────────────
    @app.get("/health", tags=["system"])
    async def health_check():
        return {
            "status": "healthy",
            "service": "AgentForge API",
            "version": "1.0.0",
            "environment": cfg.environment,
        }

    @app.get("/", tags=["system"])
    async def root():
        return {
            "name": "AgentForge API",
            "version": "1.0.0",
            "description": "Autonomous Multi-Agent Software Engineering Platform",
            "docs": "/docs",
            "health": "/health",
        }

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    cfg = get_config()
    uvicorn.run(
        "agentforge.api.main:app",
        host=cfg.api_host,
        port=cfg.api_port,
        reload=cfg.is_debug,
        workers=cfg.workers,
        log_level=cfg.log_level.lower(),
    )
