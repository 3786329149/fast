from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_config


def build_engine() -> AsyncEngine:
    config = get_config()
    return create_async_engine(
        config.DATABASE_URL,
        echo=config.SQL_ECHO,
        future=True,
        pool_pre_ping=True,
    )


engine: AsyncEngine = build_engine()
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


async def ping_database() -> bool:
    async with AsyncSessionLocal() as session:
        result = await session.execute(text('SELECT 1'))
        return result.scalar_one() == 1
