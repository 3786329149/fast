from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.response import success
from app.modules.cms.service import service

router = APIRouter(tags=['CMS Client'])


@router.get('/banners')
async def list_banners(session: AsyncSession = Depends(get_db)) -> dict:
    return success(await service.list_banners(session))


@router.get('/notices')
async def list_notices(session: AsyncSession = Depends(get_db)) -> dict:
    return success(await service.list_notices(session))

