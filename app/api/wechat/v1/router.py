from fastapi import APIRouter

from app.modules.iam.routers_wechat import router as iam_router
from app.modules.payment.routers_wechat import router as payment_router

router = APIRouter()
router.include_router(iam_router)
router.include_router(payment_router)
