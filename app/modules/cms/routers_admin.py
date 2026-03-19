from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user, get_db, require_permission
from app.core.response import success
from app.core.security import Principal
from app.modules.cms.schemas import BannerCreate, BannerUpdate, NoticeCreate, NoticeUpdate
from app.modules.cms.service import service

router = APIRouter(prefix='/cms', tags=['CMS Admin'])


@router.get('/banners', dependencies=[Depends(require_permission('cms:banner:list'))])
async def admin_list_banners(session: AsyncSession = Depends(get_db)) -> dict:
    return success(await service.list_banners(session))

@router.post('/banners', dependencies=[Depends(require_permission('cms:banner:create'))])
async def admin_create_banner(
    payload: BannerCreate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.create_banner(session, payload, current_user))

@router.put('/banners/{banner_id}', dependencies=[Depends(require_permission('cms:banner:update'))])
async def admin_update_banner(
    banner_id: int,
    payload: BannerUpdate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.update_banner(session, banner_id, payload, current_user))


@router.delete('/banners/{banner_id}', dependencies=[Depends(require_permission('cms:banner:delete'))])
async def admin_delete_banner(
    banner_id: int,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.delete_banner(session, banner_id, current_user))


@router.get('/notices', dependencies=[Depends(require_permission('cms:notice:list'))])
async def admin_list_notices(session: AsyncSession = Depends(get_db)) -> dict:
    return success(await service.list_notices(session))


@router.post('/notices', dependencies=[Depends(require_permission('cms:notice:create'))])
async def admin_create_notice(
    payload: NoticeCreate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.create_notice(session, payload, current_user))


@router.put('/notices/{notice_id}', dependencies=[Depends(require_permission('cms:notice:update'))])
async def admin_update_notice(
    notice_id: int,
    payload: NoticeUpdate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.update_notice(session, notice_id, payload, current_user))


@router.delete('/notices/{notice_id}', dependencies=[Depends(require_permission('cms:notice:delete'))])
async def admin_delete_notice(
    notice_id: int,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.delete_notice(session, notice_id, current_user))

