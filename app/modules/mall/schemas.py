from pydantic import BaseModel


class ProductOut(BaseModel):
    id: int
    name: str
    price: float
    cover_url: str


class CartAddRequest(BaseModel):
    sku_id: int
    quantity: int = 1


class OrderCreateRequest(BaseModel):
    items: list[CartAddRequest]
    source_type: str = 'miniapp'


class OrderOut(BaseModel):
    id: int
    order_no: str
    status: str
    pay_status: str
    pay_amount: float
