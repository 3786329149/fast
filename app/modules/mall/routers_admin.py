from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user, get_db, require_permission
from app.core.response import success
from app.core.security import Principal
from app.modules.mall.schemas import OrderAdminCreate, OrderAdminUpdate, ProductCreate, ProductUpdate
from app.modules.mall.service import service

router = APIRouter(prefix='/mall', tags=['Mall Admin'])


@router.get('/products', dependencies=[Depends(require_permission('mall:product:list'))])
async def admin_list_products(session: AsyncSession = Depends(get_db)) -> dict:
    return success(await service.list_products(session))


@router.post('/products', dependencies=[Depends(require_permission('mall:product:create'))])
async def admin_create_product(
    payload: ProductCreate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.create_product(session, payload, current_user))


@router.put('/products/{product_id}', dependencies=[Depends(require_permission('mall:product:update'))])
async def admin_update_product(
    product_id: int,
    payload: ProductUpdate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.update_product(session, product_id, payload, current_user))


@router.delete('/products/{product_id}', dependencies=[Depends(require_permission('mall:product:delete'))])
async def admin_delete_product(
    product_id: int,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.delete_product(session, product_id, current_user))


@router.get('/orders', dependencies=[Depends(require_permission('mall:order:list'))])
async def admin_list_orders(session: AsyncSession = Depends(get_db)) -> dict:
    return success(await service.list_orders(session))


@router.post('/orders', dependencies=[Depends(require_permission('mall:order:create'))])
async def admin_create_order(
    payload: OrderAdminCreate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.create_admin_order(session, payload, current_user))


@router.put('/orders/{order_id}', dependencies=[Depends(require_permission('mall:order:update'))])
async def admin_update_order(
    order_id: int,
    payload: OrderAdminUpdate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.update_admin_order(session, order_id, payload, current_user))


@router.delete('/orders/{order_id}', dependencies=[Depends(require_permission('mall:order:delete'))])
async def admin_delete_order(
    order_id: int,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.delete_admin_order(session, order_id, current_user))
