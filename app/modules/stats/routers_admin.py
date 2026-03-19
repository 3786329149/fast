from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.response import success
from app.modules.stats.service import service

router = APIRouter(prefix='/stats', tags=['Statistics'])


@router.get('/dashboard')
async def dashboard(session: AsyncSession = Depends(get_db)) -> dict:
    return success(await service.dashboard(session))
