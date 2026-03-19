from fastapi import APIRouter, Depends

from app.api.deps import require_permission
from app.core.response import success
from app.modules.rbac.service import service

router = APIRouter(prefix='/rbac', tags=['RBAC'])


@router.get('/roles', dependencies=[Depends(require_permission('rbac:role:list'))])
async def list_roles() -> dict:
    return success(service.list_roles())


@router.get('/menus', dependencies=[Depends(require_permission('rbac:menu:list'))])
async def list_menus() -> dict:
    return success(service.list_menus())


@router.get('/permissions', dependencies=[Depends(require_permission('rbac:permission:list'))])
async def list_permissions() -> dict:
    return success(service.list_permissions())
