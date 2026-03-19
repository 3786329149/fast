from fastapi import APIRouter

from app.core.response import success
from app.modules.cms.service import service

router = APIRouter(prefix='/cms', tags=['CMS Admin'])


@router.get('/banners')
async def admin_list_banners() -> dict:
    return success(service.list_banners())


@router.get('/notices')
async def admin_list_notices() -> dict:
    return success(service.list_notices())
