from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_client_user
from app.core.response import success
from app.core.security import Principal
from app.modules.mall.schemas import CartAddRequest, OrderCreateRequest
from app.modules.mall.service import service

router = APIRouter(tags=['Mall Client'])


@router.get('/products')
async def list_products() -> dict:
    return success(service.list_products())


@router.get('/products/{product_id}')
async def get_product(product_id: int) -> dict:
    product = service.get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail='商品不存在')
    return success(product)


@router.post('/cart/items')
async def add_cart_item(
    payload: CartAddRequest,
    current_user: Principal = Depends(get_current_client_user),
) -> dict:
    return success(service.add_cart_item(current_user.user_id, payload.sku_id, payload.quantity))


@router.post('/orders')
async def create_order(
    payload: OrderCreateRequest,
    current_user: Principal = Depends(get_current_client_user),
) -> dict:
    items = [item.model_dump() for item in payload.items]
    return success(service.create_order(current_user.user_id, items, payload.source_type))


@router.get('/orders')
async def list_orders(current_user: Principal = Depends(get_current_client_user)) -> dict:
    return success(service.list_orders(current_user.user_id))
