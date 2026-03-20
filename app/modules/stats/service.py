from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_config
from app.modules.iam.models import User
from app.modules.mall.models import MallOrder


class StatsService:
    async def dashboard(self, session: AsyncSession) -> dict:
        tz = ZoneInfo(get_config().APP_TIMEZONE or 'Asia/Shanghai')
        start_of_day = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
        today_order_count = int(
            (await session.scalar(select(func.count(MallOrder.id)).where(MallOrder.created_at >= start_of_day))) or 0
        )
        today_gmv = float(
            (await session.scalar(select(func.coalesce(func.sum(MallOrder.pay_amount), 0)).where(MallOrder.created_at >= start_of_day)))
            or 0
        )
        total_user_count = int((await session.scalar(select(func.count(User.id)))) or 0)
        pending_refund_count = int((await session.scalar(select(func.count(MallOrder.id)).where(MallOrder.refund_status == 'refunding'))) or 0)
        return {
            'today_order_count': today_order_count,
            'today_gmv': today_gmv,
            'total_user_count': total_user_count,
            'pending_refund_count': pending_refund_count,
        }


service = StatsService()
