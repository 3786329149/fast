from fastapi import APIRouter

from app.modules.cms.routers_client import router as cms_router
from app.modules.file.routers_client import router as file_router
from app.modules.iam.routers_client import router as iam_router
from app.modules.mall.routers_client import router as mall_router
from app.modules.payment.routers_client import router as payment_router

router = APIRouter()
router.include_router(iam_router)
router.include_router(cms_router)
router.include_router(file_router)
router.include_router(mall_router)
router.include_router(payment_router)
