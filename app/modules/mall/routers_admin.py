from fastapi import APIRouter, Depends

from app.api.deps import require_permission
from app.core.response import success
from app.modules.mall.service import service

router = APIRouter(prefix='/mall', tags=['Mall Admin'])


@router.get('/products', dependencies=[Depends(require_permission('mall:product:list'))])
async def admin_list_products() -> dict:
    return success(service.list_products())


@router.get('/orders', dependencies=[Depends(require_permission('mall:order:list'))])
async def admin_list_orders() -> dict:
    return success(service.list_orders())
