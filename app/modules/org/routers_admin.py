from fastapi import APIRouter, Depends

from app.api.deps import require_permission
from app.core.response import success
from app.modules.org.service import service

router = APIRouter(prefix='/org', tags=['Organization'])


@router.get('/departments', dependencies=[Depends(require_permission('org:department:list'))])
async def list_departments() -> dict:
    return success(service.list_departments())


@router.get('/employees', dependencies=[Depends(require_permission('org:employee:list'))])
async def list_employees() -> dict:
    return success(service.list_employees())
