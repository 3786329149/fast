from fastapi import APIRouter

from app.core.response import success
from app.modules.cms.service import service

router = APIRouter(tags=['CMS Client'])


@router.get('/banners')
async def list_banners() -> dict:
    return success(service.list_banners())


@router.get('/notices')
async def list_notices() -> dict:
    return success(service.list_notices())
