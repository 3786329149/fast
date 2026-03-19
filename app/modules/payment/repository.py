from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.payment.models import PaymentOrder


class PaymentRepository:
    async def get_payment_by_pay_order_no(self, session: AsyncSession, pay_order_no: str) -> PaymentOrder | None:
        stmt = select(PaymentOrder).where(PaymentOrder.pay_order_no == pay_order_no)
        return await session.scalar(stmt)

    async def get_latest_payment_by_biz_order_no(
        self,
        session: AsyncSession,
        *,
        biz_order_no: str,
        channel: str,
    ) -> PaymentOrder | None:
        stmt = (
            select(PaymentOrder)
            .where(PaymentOrder.biz_order_no == biz_order_no, PaymentOrder.channel == channel)
            .order_by(desc(PaymentOrder.id))
            .limit(1)
        )
        return await session.scalar(stmt)

    async def create_payment_order(
        self,
        session: AsyncSession,
        *,
        biz_order_no: str,
        pay_order_no: str,
        channel: str,
        amount: Decimal,
        currency: str,
        description: str | None,
        payer_openid: str | None,
    ) -> PaymentOrder:
        order = PaymentOrder(
            biz_order_no=biz_order_no,
            pay_order_no=pay_order_no,
            channel=channel,
            amount=amount,
            currency=currency,
            description=description,
            payer_openid=payer_openid,
            status='pending',
        )
        session.add(order)
        await session.flush()
        return order

    async def update_payment_prepare(
        self,
        session: AsyncSession,
        *,
        payment_order: PaymentOrder,
        appid: str,
        mch_id: str,
        prepay_id: str | None,
        response_payload: dict,
    ) -> PaymentOrder:
        payment_order.appid = appid
        payment_order.mch_id = mch_id
        payment_order.prepay_id = prepay_id
        payment_order.channel_response = json.dumps(response_payload, ensure_ascii=False)
        await session.flush()
        return payment_order

    async def mark_payment_success(
        self,
        session: AsyncSession,
        *,
        payment_order: PaymentOrder,
        transaction_id: str | None,
        paid_at: datetime | None,
        raw_payload: dict,
    ) -> PaymentOrder:
        payment_order.status = 'success'
        payment_order.transaction_id = transaction_id
        payment_order.paid_at = paid_at
        payment_order.notify_payload = json.dumps(raw_payload, ensure_ascii=False)
        await session.flush()
        return payment_order

    async def mark_payment_state(
        self,
        session: AsyncSession,
        *,
        payment_order: PaymentOrder,
        status_value: str,
        raw_payload: dict,
    ) -> PaymentOrder:
        payment_order.status = status_value
        payment_order.notify_payload = json.dumps(raw_payload, ensure_ascii=False)
        await session.flush()
        return payment_order


repository = PaymentRepository()
