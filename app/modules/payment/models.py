from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, IDMixin, TimestampMixin


class PaymentOrder(IDMixin, TimestampMixin, Base):
    __tablename__ = 'payment_order'

    biz_order_no: Mapped[str] = mapped_column(String(64), index=True)
    pay_order_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    appid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mch_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payer_openid: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), default='pending', index=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(16), default='CNY')
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    prepay_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    transaction_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    channel_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    notify_payload: Mapped[str | None] = mapped_column(Text, nullable=True)


class RefundOrder(IDMixin, TimestampMixin, Base):
    __tablename__ = 'refund_order'

    biz_order_no: Mapped[str] = mapped_column(String(64), index=True)
    refund_order_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default='pending', index=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    channel_response: Mapped[str | None] = mapped_column(Text, nullable=True)
