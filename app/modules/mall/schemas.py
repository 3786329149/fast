from __future__ import annotations

from pydantic import BaseModel, Field



class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    price: float = Field(gt=0)
    cover_url: str | None = None
    original_price: float | None = Field(default=None, ge=0)
    stock: int = Field(default=0, ge=0)
    category: str | None = Field(default=None, max_length=128)
    status: str = 'active'
    summary: str | None = None
    updated_at: str | None = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    pass


class ProductOut(ProductBase):
    id: int

class CartAddRequest(BaseModel):
    sku_id: int
    quantity: int = 1


class OrderCreateRequest(BaseModel):
    items: list[CartAddRequest]
    source_type: str = 'miniapp'


class OrderAdminBase(BaseModel):
    order_no: str = Field(min_length=1, max_length=64)
    user_id: int = Field(ge=1)
    status: str = 'pending'
    pay_status: str = 'unpaid'
    pay_amount: float = Field(gt=0)
    source_type: str = 'admin'
    receiver_name: str | None = Field(default=None, max_length=128)
    phone: str | None = Field(default=None, max_length=32)
    items_count: int = Field(default=1, ge=0)
    created_at: str | None = None


class OrderAdminCreate(OrderAdminBase):
    pass


class OrderAdminUpdate(OrderAdminBase):
    pass

class OrderOut(BaseModel):
    id: int
    order_no: str
    user_id: int
    status: str
    pay_status: str
    pay_amount: float
    source_type: str
    receiver_name: str | None = None
    phone: str | None = None
    items_count: int = 0
    created_at: str | None = None
