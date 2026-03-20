from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.security import Principal
from app.integrations.wechat.client import WeChatApiError, client as wechat_client
from app.modules.iam.repository import repository as iam_repository
from app.modules.mall.models import MallOrder
from app.modules.payment.repository import repository


class PaymentService:
    async def create_payment(
        self,
        session: AsyncSession,
        *,
        current_user: Principal,
        order_no: str,
        channel: str,
        description: str | None = None,
        openid: str | None = None,
    ) -> dict:
        if channel != 'wechat_miniapp':
            raise AppException('当前 Starter 仅内置了微信小程序支付骨架', status_code=status.HTTP_400_BAD_REQUEST)
        return await self.create_wechat_payment(
            session,
            current_user=current_user,
            order_no=order_no,
            description=description,
            openid=openid,
        )

    async def create_wechat_payment(
        self,
        session: AsyncSession,
        *,
        current_user: Principal,
        order_no: str,
        description: str | None = None,
        openid: str | None = None,
    ) -> dict:
        mall_order = await session.scalar(
            select(MallOrder).where(MallOrder.order_no == order_no, MallOrder.user_id == current_user.user_id)
        )
        if mall_order is None:
            raise AppException('订单不存在', status_code=status.HTTP_404_NOT_FOUND)
        if mall_order.pay_status == 'paid':
            raise AppException('订单已支付，无需重复下单', status_code=status.HTTP_400_BAD_REQUEST)

        payer_openid = openid or await self._resolve_user_openid(session, current_user.user_id)
        if not payer_openid:
            raise AppException('当前账号未绑定微信小程序账号，无法发起微信支付', status_code=status.HTTP_400_BAD_REQUEST)

        amount = Decimal(str(mall_order.pay_amount)).quantize(Decimal('0.01'))
        if amount <= 0:
            raise AppException('订单支付金额无效', status_code=status.HTTP_400_BAD_REQUEST)

        latest_order = await repository.get_latest_payment_by_biz_order_no(
            session,
            biz_order_no=order_no,
            channel='wechat_miniapp',
        )
        if latest_order and latest_order.status == 'pending' and latest_order.prepay_id:
            pay_params = wechat_client.build_miniapp_pay_params(latest_order.prepay_id)
            return {
                'biz_order_no': latest_order.biz_order_no,
                'pay_order_no': latest_order.pay_order_no,
                'channel': latest_order.channel,
                'status': latest_order.status,
                'amount': str(latest_order.amount),
                'currency': latest_order.currency,
                'prepay_id': latest_order.prepay_id,
                'pay_params': pay_params,
                'reused': True,
            }

        pay_order_no = f'PAY{uuid4().hex[:20].upper()}'
        payment_order = await repository.create_payment_order(
            session,
            biz_order_no=order_no,
            pay_order_no=pay_order_no,
            channel='wechat_miniapp',
            amount=amount,
            currency=get_settings().WECHAT_PAY_CURRENCY,
            description=description or f'订单 {order_no}',
            payer_openid=payer_openid,
        )

        try:
            response_payload = await wechat_client.create_miniapp_jsapi_order(
                description=payment_order.description or f'订单 {order_no}',
                out_trade_no=payment_order.pay_order_no,
                total_fee_fen=self._amount_to_fen(amount),
                payer_openid=payer_openid,
                attach=order_no,
            )
        except WeChatApiError as exc:
            payment_order.status = 'failed'
            payment_order.channel_response = json.dumps({'error': str(exc)}, ensure_ascii=False)
            await session.commit()
            raise AppException(str(exc), status_code=status.HTTP_502_BAD_GATEWAY) from exc

        await repository.update_payment_prepare(
            session,
            payment_order=payment_order,
            appid=get_settings().WECHAT_MINIAPP_APPID,
            mch_id=get_settings().WECHAT_MCH_ID,
            prepay_id=response_payload.get('prepay_id'),
            response_payload=response_payload,
        )
        await session.commit()
        return {
            'biz_order_no': payment_order.biz_order_no,
            'pay_order_no': payment_order.pay_order_no,
            'channel': payment_order.channel,
            'status': payment_order.status,
            'amount': str(payment_order.amount),
            'currency': payment_order.currency,
            'prepay_id': payment_order.prepay_id,
            'pay_params': response_payload.get('pay_params'),
            'mock': response_payload.get('mock', False),
        }

    async def handle_wechat_callback(self, session: AsyncSession, *, headers: dict[str, str], body: str) -> dict:
        try:
            parsed = wechat_client.parse_payment_callback(headers=headers, body=body)
        except (WeChatApiError, ValueError) as exc:
            raise AppException(f'回调处理失败: {exc}', status_code=status.HTTP_400_BAD_REQUEST) from exc

        resource = parsed.resource
        pay_order_no = resource.get('out_trade_no')
        if not pay_order_no:
            raise AppException('回调数据缺少 out_trade_no', status_code=status.HTTP_400_BAD_REQUEST)

        payment_order = await repository.get_payment_by_pay_order_no(session, pay_order_no)
        if payment_order is None:
            raise AppException('支付单不存在', status_code=status.HTTP_404_NOT_FOUND)

        trade_state = str(resource.get('trade_state', '')).upper()
        if trade_state == 'SUCCESS':
            paid_at = self._parse_datetime(resource.get('success_time'))
            await repository.mark_payment_success(
                session,
                payment_order=payment_order,
                transaction_id=resource.get('transaction_id'),
                paid_at=paid_at,
                raw_payload=parsed.raw,
            )
            mall_order = await session.scalar(select(MallOrder).where(MallOrder.order_no == payment_order.biz_order_no))
            if mall_order is not None:
                mall_order.pay_status = 'paid'
                mall_order.status = 'paid'
            await session.commit()
            return {
                'code': 'SUCCESS',
                'message': '成功',
                'pay_order_no': pay_order_no,
                'trade_state': trade_state,
                'verified': parsed.verified,
            }

        await repository.mark_payment_state(
            session,
            payment_order=payment_order,
            status_value=trade_state.lower() or 'failed',
            raw_payload=parsed.raw,
        )
        await session.commit()
        return {
            'code': 'SUCCESS',
            'message': '成功',
            'pay_order_no': pay_order_no,
            'trade_state': trade_state,
            'verified': parsed.verified,
        }

    async def _resolve_user_openid(self, session: AsyncSession, user_id: int) -> str | None:
        identities = await iam_repository.list_identities_by_user(
            session,
            user_id=user_id,
            identity_type='wechat_miniapp',
        )
        for identity in identities:
            if identity.extra_json:
                try:
                    extra = json.loads(identity.extra_json)
                except json.JSONDecodeError:
                    extra = {}
                openid = extra.get('openid')
                if openid:
                    return openid
        if get_settings().WECHAT_API_MOCK:
            return f'mini_user_{user_id}'
        return None

    @staticmethod
    def _amount_to_fen(amount: Decimal) -> int:
        return int((amount * Decimal('100')).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return None


service = PaymentService()
