from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.bootstrap.diagnostics import run_startup_diagnostics
from app.bootstrap.logging import configure_logging
from app.infra.cache.redis import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    await run_startup_diagnostics(app, keep_redis_client=True)
    yield
    await close_redis()
