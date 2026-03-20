from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_client_user, get_db
from app.core.exceptions import AppException
from app.core.response import success
from app.infra.security.token import Principal
from app.modules.mall.schemas import CartAddRequest, OrderCreateRequest
from app.modules.mall.service import service

router = APIRouter(tags=['Mall Client'])


@router.get('/products')
async def list_products(session: AsyncSession = Depends(get_db)) -> dict:
    return success(await service.list_products(session))


@router.get('/products/{product_id}')
async def get_product(product_id: int, session: AsyncSession = Depends(get_db)) -> dict:
    product = await service.get_product(session, product_id)
    if product is None:
        raise AppException('商品不存在', status_code=404)
    return success(product)


@router.post('/cart/items')
async def add_cart_item(
    payload: CartAddRequest,
    current_user: Principal = Depends(get_current_client_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.add_cart_item(session, current_user.user_id, payload.sku_id, payload.quantity))


@router.post('/orders')
async def create_order(
    payload: OrderCreateRequest,
    current_user: Principal = Depends(get_current_client_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    items = [item.model_dump() for item in payload.items]
    return success(await service.create_order(session, current_user.user_id, items, payload.source_type))


@router.get('/orders')
async def list_orders(
    current_user: Principal = Depends(get_current_client_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.list_orders(session, current_user.user_id))
