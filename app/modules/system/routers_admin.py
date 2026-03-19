from fastapi import APIRouter

from app.core.response import success
from app.modules.system.service import service

router = APIRouter(prefix='/system', tags=['System'])


@router.get('/configs')
async def list_configs() -> dict:
    return success(service.list_configs())


@router.get('/dicts')
async def list_dicts() -> dict:
    return success(service.list_dicts())
