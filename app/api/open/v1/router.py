from fastapi import APIRouter

from app.modules.payment.routers_open import router as payment_router

router = APIRouter()
router.include_router(payment_router)
