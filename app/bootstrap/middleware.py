from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        request.state.request_id = request_id
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        response.headers['X-Request-ID'] = request_id
        response.headers['X-Process-Time'] = f'{duration:.6f}'
        return response


def register_middlewares(app: FastAPI) -> None:
    app.add_middleware(RequestContextMiddleware)
