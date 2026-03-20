from __future__ import annotations

import importlib
import time
from typing import Any

import structlog
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.config import get_config
from app.infra.cache import redis as redis_store
from app.infra.cache.redis import close_redis, init_redis
from app.infra.db.base import Base
from app.infra.db.session import AsyncSessionLocal

logger = structlog.get_logger(__name__)


def ensure_models_registered() -> None:
    importlib.import_module("app.infra.db.registry")


def collect_table_summary(*, include_names: bool) -> dict[str, Any]:
    table_names = sorted(Base.metadata.tables.keys())
    summary: dict[str, Any] = {"count": len(table_names)}
    if include_names:
        summary["names"] = table_names
    return summary


def collect_route_summary(app: FastAPI) -> dict[str, Any]:
    domains = {"admin": 0, "client": 0, "wechat": 0, "open": 0, "other": 0}

    for route in app.routes:
        path = getattr(route, "path", "")
        if path.startswith("/api/admin/"):
            domains["admin"] += 1
        elif path.startswith("/api/client/"):
            domains["client"] += 1
        elif path.startswith("/api/wechat/"):
            domains["wechat"] += 1
        elif path.startswith("/api/open/"):
            domains["open"] += 1
        else:
            domains["other"] += 1

    return {"count": len(app.routes), "domains": domains}


async def probe_database() -> dict[str, Any]:
    config = get_config()
    url = make_url(config.DATABASE_URL)
    started_at = time.perf_counter()

    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        if result.scalar_one() != 1:
            raise RuntimeError("Database ping returned an unexpected result")

    latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
    return {
        "connected": True,
        "latency_ms": latency_ms,
        "driver": url.drivername,
        "host": url.host,
        "port": url.port,
        "database": url.database,
    }


async def probe_redis(*, keep_client: bool) -> dict[str, Any]:
    config = get_config()
    started_at = time.perf_counter()

    await init_redis()
    try:
        if redis_store.redis_client is None:
            raise RuntimeError("Redis client is not initialized")
        if await redis_store.redis_client.ping() is not True:
            raise RuntimeError("Redis ping returned an unexpected result")
        latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
        return {
            "connected": True,
            "latency_ms": latency_ms,
            "host": config.REDIS_HOST,
            "port": config.REDIS_PORT,
            "db": config.REDIS_DB,
        }
    except Exception:
        await close_redis()
        raise
    finally:
        if not keep_client:
            await close_redis()


def build_readiness_payload(app: FastAPI) -> dict[str, Any]:
    diagnostics = getattr(app.state, "startup_diagnostics", None)
    if diagnostics is None:
        tables = collect_table_summary(include_names=False)
        routes = collect_route_summary(app)
        return {
            "status": "unavailable",
            "database": {"connected": False},
            "redis": {"connected": False},
            "tables": {"count": tables["count"]},
            "routes": {"count": routes["count"]},
        }

    return {
        "status": diagnostics["status"],
        "database": {"connected": diagnostics["database"]["connected"]},
        "redis": {"connected": diagnostics["redis"]["connected"]},
        "tables": {"count": diagnostics["tables"]["count"]},
        "routes": {"count": diagnostics["routes"]["count"]},
    }


async def run_startup_diagnostics(
    app: FastAPI,
    *,
    include_details: bool | None = None,
    keep_redis_client: bool = True,
) -> dict[str, Any]:
    config = get_config()
    include_details = config.IS_LOCAL_ENV if include_details is None else include_details

    ensure_models_registered()

    try:
        database = await probe_database()
        logger.info("startup_database_ready", **database)
    except Exception as exc:
        logger.exception("startup_database_failed", error=str(exc))
        raise

    try:
        redis = await probe_redis(keep_client=keep_redis_client)
        logger.info("startup_redis_ready", **redis)
    except Exception as exc:
        logger.exception("startup_redis_failed", error=str(exc))
        raise

    tables = collect_table_summary(include_names=include_details)
    routes = collect_route_summary(app)
    diagnostics = {
        "status": "ok",
        "database": database,
        "redis": redis,
        "tables": tables,
        "routes": routes,
    }
    app.state.startup_diagnostics = diagnostics

    summary_log: dict[str, Any] = {
        "env": config.APP_ENV,
        "table_count": tables["count"],
        "route_count": routes["count"],
        "route_domains": routes["domains"],
        "database_host": database["host"],
        "database_port": database["port"],
        "database_name": database["database"],
        "database_driver": database["driver"],
        "database_latency_ms": database["latency_ms"],
        "redis_host": redis["host"],
        "redis_port": redis["port"],
        "redis_db": redis["db"],
        "redis_latency_ms": redis["latency_ms"],
    }
    if include_details:
        summary_log["table_names"] = tables.get("names", [])

    logger.info("startup_summary", **summary_log)
    return diagnostics
