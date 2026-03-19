from fastapi import APIRouter

from app.modules.audit.routers_admin import router as audit_router
from app.modules.cms.routers_admin import router as cms_router
from app.modules.file.routers_admin import router as file_router
from app.modules.iam.routers_admin import router as iam_router
from app.modules.mall.routers_admin import router as mall_router
from app.modules.org.routers_admin import router as org_router
from app.modules.rbac.routers_admin import router as rbac_router
from app.modules.stats.routers_admin import router as stats_router
from app.modules.system.routers_admin import router as system_router

router = APIRouter()
router.include_router(iam_router)
router.include_router(org_router)
router.include_router(rbac_router)
router.include_router(mall_router)
router.include_router(cms_router)
router.include_router(file_router)
router.include_router(system_router)
router.include_router(audit_router)
router.include_router(stats_router)
