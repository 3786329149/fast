from __future__ import annotations

import time
import uuid

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings

logger = structlog.get_logger("app.http")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        request.state.request_id = request_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        start = time.perf_counter()
        client_ip = request.client.host if request.client is not None else None

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.exception(
                "request_failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
                client_ip=client_ip,
            )
            raise
        finally:
            structlog.contextvars.unbind_contextvars("request_id")

        duration = time.perf_counter() - start
        response.headers['X-Request-ID'] = request_id
        response.headers['X-Process-Time'] = f'{duration:.6f}'
        duration_ms = round(duration * 1000, 2)
        log = logger.error if response.status_code >= 500 else logger.info
        event = "request_failed" if response.status_code >= 500 else "request_completed"
        log(
            event,
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            client_ip=client_ip,
        )
        return response


def register_middlewares(app: FastAPI) -> None:
    settings = get_settings()
    if settings.CORS_ENABLED:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS_LIST,
            allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
            allow_methods=settings.CORS_METHODS_LIST,
            allow_headers=settings.CORS_HEADERS_LIST,
        )
    app.add_middleware(RequestContextMiddleware)
