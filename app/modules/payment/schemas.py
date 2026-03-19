from pydantic import BaseModel


class CreatePaymentRequest(BaseModel):
    order_no: str
    channel: str = 'wechat_miniapp'


class RefundRequest(BaseModel):
    order_no: str
    amount: float
