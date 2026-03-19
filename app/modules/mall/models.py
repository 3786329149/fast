from __future__ import annotations

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, IDMixin, TimestampMixin


class MallCategory(IDMixin, TimestampMixin, Base):
    __tablename__ = 'mall_category'

    parent_id: Mapped[int | None] = mapped_column(ForeignKey('mall_category.id'), nullable=True)
    name: Mapped[str] = mapped_column(String(128))
    sort: Mapped[int] = mapped_column(default=0)
    status: Mapped[int] = mapped_column(default=1)


class MallSpu(IDMixin, TimestampMixin, Base):
    __tablename__ = 'mall_spu'

    category_id: Mapped[int] = mapped_column(ForeignKey('mall_category.id'), index=True)
    org_id: Mapped[int | None] = mapped_column(nullable=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    subtitle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cover_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[int] = mapped_column(default=1)


class MallSku(IDMixin, TimestampMixin, Base):
    __tablename__ = 'mall_sku'

    spu_id: Mapped[int] = mapped_column(ForeignKey('mall_spu.id'), index=True)
    sku_code: Mapped[str] = mapped_column(String(64), unique=True)
    spec_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    sale_price: Mapped[float] = mapped_column(Numeric(10, 2))
    market_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    stock: Mapped[int] = mapped_column(default=0)


class MallCart(IDMixin, TimestampMixin, Base):
    __tablename__ = 'mall_cart'

    user_id: Mapped[int] = mapped_column(index=True)
    sku_id: Mapped[int] = mapped_column(ForeignKey('mall_sku.id'), index=True)
    quantity: Mapped[int] = mapped_column(default=1)
    checked: Mapped[bool] = mapped_column(default=True)


class MallOrder(IDMixin, TimestampMixin, Base):
    __tablename__ = 'mall_order'

    order_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(index=True)
    org_id: Mapped[int | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(32), default='pending')
    pay_status: Mapped[str] = mapped_column(String(32), default='unpaid')
    refund_status: Mapped[str] = mapped_column(String(32), default='none')
    source_type: Mapped[str] = mapped_column(String(16), default='miniapp')
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2))
    pay_amount: Mapped[float] = mapped_column(Numeric(10, 2))
    created_by: Mapped[int | None] = mapped_column(nullable=True)
    receiver_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    receiver_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    items_count: Mapped[int] = mapped_column(default=0)


class MallOrderItem(IDMixin, TimestampMixin, Base):
    __tablename__ = 'mall_order_item'

    order_id: Mapped[int] = mapped_column(ForeignKey('mall_order.id'), index=True)
    sku_id: Mapped[int] = mapped_column(ForeignKey('mall_sku.id'), index=True)
    spu_name: Mapped[str] = mapped_column(String(128))
    sku_name: Mapped[str] = mapped_column(String(128))
    quantity: Mapped[int] = mapped_column(default=1)
    sale_price: Mapped[float] = mapped_column(Numeric(10, 2))
