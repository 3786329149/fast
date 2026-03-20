from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.security import Principal
from app.modules.audit.service import service as audit_service
from app.modules.mall.models import MallCart, MallCategory, MallOrder, MallOrderItem, MallSku, MallSpu
from app.modules.mall.schemas import CartAddRequest, OrderAdminCreate, OrderAdminUpdate, OrderCreateRequest, ProductCreate, ProductUpdate
from app.utils.crud import (
    date_to_iso,
    decimal_to_float,
    dt_to_iso,
    int_to_product_status,
    normalize_text,
    parse_iso_date,
    product_status_to_int,
)





class MallService:
    async def _get_or_create_category(self, session: AsyncSession, name: str | None) -> MallCategory:
        category_name = normalize_text(name) or '默认分类'
        category = await session.scalar(select(MallCategory).where(MallCategory.name == category_name))
        if category is None:
            category = MallCategory(name=category_name, parent_id=None, sort=0, status=1)
            session.add(category)
            await session.flush()
        return category

    async def _get_primary_sku(self, session: AsyncSession, spu_id: int) -> MallSku | None:
        stmt = select(MallSku).where(MallSku.spu_id == spu_id).order_by(MallSku.id.asc())
        return await session.scalar(stmt)

    async def list_products(self, session: AsyncSession) -> list[dict]:
        spus = list((await session.scalars(select(MallSpu).order_by(MallSpu.id.asc()))).all())
        result: list[dict] = []
        for spu in spus:
            sku = await self._get_primary_sku(session, spu.id)
            category = await session.get(MallCategory, spu.category_id)
            result.append(self.serialize_product(spu, sku, category.name if category else None))
        return result

    def serialize_product(self, spu: MallSpu, sku: MallSku | None, category: str | None) -> dict:
        return {
            'id': spu.id,
            'name': spu.name,
            'price': decimal_to_float(sku.sale_price if sku else 0),
            'cover_url': spu.cover_url,
            'original_price': decimal_to_float(sku.market_price if sku and sku.market_price is not None else None) if sku else None,
            'stock': int(sku.stock if sku else 0),
            'category': category,
            'status': int_to_product_status(spu.status),
            'summary': spu.subtitle,
            'updated_at': dt_to_iso(spu.updated_at),
        }

    async def get_product(self, session: AsyncSession, product_id: int) -> dict | None:
        spu = await session.get(MallSpu, product_id)
        if spu is None:
            return None
        sku = await self._get_primary_sku(session, spu.id)
        category = await session.get(MallCategory, spu.category_id)
        return self.serialize_product(spu, sku, category.name if category else None)

    async def create_product(self, session: AsyncSession, payload: ProductCreate, current_user: Principal) -> dict:
        category = await self._get_or_create_category(session, payload.category)
        spu = MallSpu(
            category_id=category.id,
            org_id=current_user.org_id,
            name=payload.name.strip(),
            subtitle=normalize_text(payload.summary),
            cover_url=normalize_text(payload.cover_url),
            status=product_status_to_int(payload.status),
        )
        session.add(spu)
        await session.flush()
        sku = MallSku(
            spu_id=spu.id,
            sku_code=f'SKU-{uuid4().hex[:10].upper()}',
            spec_json=None,
            sale_price=Decimal(str(payload.price)),
            market_price=Decimal(str(payload.original_price)) if payload.original_price is not None else None,
            stock=payload.stock,
        )
        session.add(sku)
        await session.flush()
        await audit_service.log_operation(
            session,
            module='mall',
            action='create_product',
            path='/api/admin/v1/mall/products',
            user_id=current_user.user_id,
            detail=spu.name,
        )
        await session.commit()
        return self.serialize_product(spu, sku, category.name)

    async def update_product(
        self,
        session: AsyncSession,
        product_id: int,
        payload: ProductUpdate,
        current_user: Principal,
    ) -> dict:
        spu = await session.get(MallSpu, product_id)
        if spu is None:
            raise AppException('商品不存在', status_code=404)
        category = await self._get_or_create_category(session, payload.category)
        sku = await self._get_primary_sku(session, spu.id)
        if sku is None:
            sku = MallSku(
                spu_id=spu.id,
                sku_code=f'SKU-{uuid4().hex[:10].upper()}',
                spec_json=None,
                sale_price=Decimal(str(payload.price)),
                market_price=Decimal(str(payload.original_price)) if payload.original_price is not None else None,
                stock=payload.stock,
            )
            session.add(sku)
            await session.flush()
        spu.category_id = category.id
        spu.name = payload.name.strip()
        spu.subtitle = normalize_text(payload.summary)
        spu.cover_url = normalize_text(payload.cover_url)
        spu.status = product_status_to_int(payload.status)
        sku.sale_price = Decimal(str(payload.price))
        sku.market_price = Decimal(str(payload.original_price)) if payload.original_price is not None else None
        sku.stock = payload.stock
        await audit_service.log_operation(
            session,
            module='mall',
            action='update_product',
            path=f'/api/admin/v1/mall/products/{product_id}',
            user_id=current_user.user_id,
            detail=spu.name,
        )
        await session.commit()
        return self.serialize_product(spu, sku, category.name)

    async def delete_product(self, session: AsyncSession, product_id: int, current_user: Principal) -> dict:
        spu = await session.get(MallSpu, product_id)
        if spu is None:
            raise AppException('商品不存在', status_code=404)
        sku_ids = list((await session.scalars(select(MallSku.id).where(MallSku.spu_id == product_id))).all())
        if sku_ids:
            used = await session.scalar(select(MallOrderItem.id).where(MallOrderItem.sku_id.in_(sku_ids)).limit(1))
            if used is not None:
                raise AppException('商品已产生订单，不能删除', status_code=400)
            await session.execute(delete(MallSku).where(MallSku.spu_id == product_id))
        name = spu.name
        await session.delete(spu)
        await audit_service.log_operation(
            session,
            module='mall',
            action='delete_product',
            path=f'/api/admin/v1/mall/products/{product_id}',
            user_id=current_user.user_id,
            detail=name,
        )
        await session.commit()
        return {'id': product_id}

    async def add_cart_item(self, session: AsyncSession, user_id: int, sku_id: int, quantity: int) -> dict:
        sku = await session.get(MallSku, sku_id)
        if sku is None:
            raise AppException('SKU 不存在', status_code=404)
        cart = await session.scalar(select(MallCart).where(MallCart.user_id == user_id, MallCart.sku_id == sku_id))
        if cart is None:
            cart = MallCart(user_id=user_id, sku_id=sku_id, quantity=quantity, checked=True)
            session.add(cart)
        else:
            cart.quantity += quantity
        await session.commit()
        return {'user_id': user_id, 'sku_id': sku_id, 'quantity': cart.quantity, 'added': True}

    async def create_order(self, session: AsyncSession, user_id: int, items: list[dict], source_type: str) -> dict:
        if not items:
            raise AppException('订单项不能为空', status_code=400)
        sku_ids = [int(item.get('sku_id')) for item in items]
        skus = list((await session.scalars(select(MallSku).where(MallSku.id.in_(sku_ids)))).all())
        sku_map = {sku.id: sku for sku in skus}
        total = Decimal('0.00')
        for item in items:
            sku = sku_map.get(int(item.get('sku_id')))
            if sku is None:
                raise AppException('存在无效的 SKU', status_code=404)
            qty = int(item.get('quantity', 1) or 1)
            total += Decimal(str(sku.sale_price)) * qty
        order = MallOrder(
            order_no=f'ORD{uuid4().hex[:16].upper()}',
            user_id=user_id,
            org_id=None,
            status='pending',
            pay_status='unpaid',
            refund_status='none',
            source_type=source_type,
            total_amount=total,
            pay_amount=total,
            created_by=user_id,
            items_count=sum(int(item.get('quantity', 1) or 1) for item in items),
        )
        session.add(order)
        await session.flush()
        for item in items:
            sku = sku_map[int(item.get('sku_id'))]
            qty = int(item.get('quantity', 1) or 1)
            spu = await session.get(MallSpu, sku.spu_id)
            session.add(
                MallOrderItem(
                    order_id=order.id,
                    sku_id=sku.id,
                    spu_name=spu.name if spu else f'SPU-{sku.spu_id}',
                    sku_name=sku.sku_code,
                    quantity=qty,
                    sale_price=sku.sale_price,
                )
            )
        await session.commit()
        return await self._serialize_order_with_items(session, order)

    async def list_orders(self, session: AsyncSession, user_id: int | None = None) -> list[dict]:
        stmt = select(MallOrder).order_by(MallOrder.created_at.desc(), MallOrder.id.desc())
        if user_id is not None:
            stmt = stmt.where(MallOrder.user_id == user_id)
        rows = list((await session.scalars(stmt)).all())
        result: list[dict] = []
        for row in rows:
            result.append(await self._serialize_order_with_items(session, row))
        return result

    async def _serialize_order_with_items(self, session: AsyncSession, row: MallOrder) -> dict:
        items_count = row.items_count
        if not items_count:
            items_count = int(
                (await session.scalar(select(func.coalesce(func.sum(MallOrderItem.quantity), 0)).where(MallOrderItem.order_id == row.id)))
                or 0
            )
        return {
            'id': row.id,
            'order_no': row.order_no,
            'user_id': row.user_id,
            'status': row.status,
            'pay_status': row.pay_status,
            'pay_amount': decimal_to_float(row.pay_amount),
            'source_type': row.source_type,
            'receiver_name': row.receiver_name,
            'phone': row.receiver_phone,
            'items_count': items_count,
            'created_at': dt_to_iso(row.created_at),
        }

    async def create_admin_order(self, session: AsyncSession, payload: OrderAdminCreate, current_user: Principal) -> dict:
        exists = await session.scalar(select(MallOrder).where(MallOrder.order_no == payload.order_no.strip()))
        if exists is not None:
            raise AppException('订单号已存在', status_code=400)
        order = MallOrder(
            order_no=payload.order_no.strip(),
            user_id=payload.user_id,
            org_id=current_user.org_id,
            status=payload.status,
            pay_status=payload.pay_status,
            refund_status='none',
            source_type=payload.source_type,
            total_amount=Decimal(str(payload.pay_amount)),
            pay_amount=Decimal(str(payload.pay_amount)),
            created_by=current_user.user_id,
            receiver_name=normalize_text(payload.receiver_name),
            receiver_phone=normalize_text(payload.phone),
            items_count=payload.items_count,
        )
        session.add(order)
        await session.flush()
        await audit_service.log_operation(
            session,
            module='mall',
            action='create_order',
            path='/api/admin/v1/mall/orders',
            user_id=current_user.user_id,
            detail=order.order_no,
        )
        await session.commit()
        return await self._serialize_order_with_items(session, order)

    async def update_admin_order(
        self,
        session: AsyncSession,
        order_id: int,
        payload: OrderAdminUpdate,
        current_user: Principal,
    ) -> dict:
        order = await session.get(MallOrder, order_id)
        if order is None:
            raise AppException('订单不存在', status_code=404)
        exists = await session.scalar(select(MallOrder).where(MallOrder.order_no == payload.order_no.strip(), MallOrder.id != order_id))
        if exists is not None:
            raise AppException('订单号已存在', status_code=400)
        order.order_no = payload.order_no.strip()
        order.user_id = payload.user_id
        order.status = payload.status
        order.pay_status = payload.pay_status
        order.source_type = payload.source_type
        order.total_amount = Decimal(str(payload.pay_amount))
        order.pay_amount = Decimal(str(payload.pay_amount))
        order.receiver_name = normalize_text(payload.receiver_name)
        order.receiver_phone = normalize_text(payload.phone)
        order.items_count = payload.items_count
        await audit_service.log_operation(
            session,
            module='mall',
            action='update_order',
            path=f'/api/admin/v1/mall/orders/{order_id}',
            user_id=current_user.user_id,
            detail=order.order_no,
        )
        await session.commit()
        return await self._serialize_order_with_items(session, order)

    async def delete_admin_order(self, session: AsyncSession, order_id: int, current_user: Principal) -> dict:
        order = await session.get(MallOrder, order_id)
        if order is None:
            raise AppException('订单不存在', status_code=404)
        if order.pay_status == 'paid':
            raise AppException('已支付订单不支持直接删除', status_code=400)
        await session.execute(delete(MallOrderItem).where(MallOrderItem.order_id == order_id))
        order_no = order.order_no
        await session.delete(order)
        await audit_service.log_operation(
            session,
            module='mall',
            action='delete_order',
            path=f'/api/admin/v1/mall/orders/{order_id}',
            user_id=current_user.user_id,
            detail=order_no,
        )
        await session.commit()
        return {'id': order_id}



service = MallService()
