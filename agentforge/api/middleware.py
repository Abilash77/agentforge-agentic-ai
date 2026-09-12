"""
AgentForge API Middleware.

Request logging, CORS, rate limiting, and error handling.
"""

from __future__ import annotations

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from agentforge.monitoring.logger import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with timing and status code."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start_time = time.perf_counter()

        # Log incoming request
        logger.info(
            f"→ [{request_id}] {request.method} {request.url.path}"
            + (f"?{request.url.query}" if request.url.query else "")
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error(f"← [{request_id}] UNHANDLED: {type(exc).__name__}: {exc}")
            raise

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        log_fn = logger.warning if response.status_code >= 400 else logger.info
        log_fn(
            f"← [{request_id}] {response.status_code} "
            f"({duration_ms}ms) {request.method} {request.url.path}"
        )

        # Add request ID header
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms}ms"
        return response
