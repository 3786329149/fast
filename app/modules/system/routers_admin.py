from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user, get_db, require_permission
from app.core.response import success
from app.infra.security.token import Principal
from app.modules.system.schemas import DictCreate, DictUpdate, SettingCreate, SettingUpdate
from app.modules.system.service import service

router = APIRouter(prefix='/system', tags=['System'])


@router.get('/settings', dependencies=[Depends(require_permission('system:setting:list'))])
async def list_settings(session: AsyncSession = Depends(get_db)) -> dict:
    return success(await service.list_settings(session))


@router.post('/settings', dependencies=[Depends(require_permission('system:setting:create'))])
async def create_setting(
    payload: SettingCreate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.create_setting(session, payload, current_user))


@router.put('/settings/{setting_id}', dependencies=[Depends(require_permission('system:setting:update'))])
async def update_setting(
    setting_id: int,
    payload: SettingUpdate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.update_setting(session, setting_id, payload, current_user))


@router.delete('/settings/{setting_id}', dependencies=[Depends(require_permission('system:setting:delete'))])
async def delete_setting(
    setting_id: int,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.delete_setting(session, setting_id, current_user))


@router.get('/dicts', dependencies=[Depends(require_permission('system:dict:list'))])
async def list_dicts(session: AsyncSession = Depends(get_db)) -> dict:
    return success(await service.list_dicts(session))


@router.post('/dicts', dependencies=[Depends(require_permission('system:dict:create'))])
async def create_dict(
    payload: DictCreate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.create_dict(session, payload, current_user))


@router.put('/dicts/{dict_id}', dependencies=[Depends(require_permission('system:dict:update'))])
async def update_dict(
    dict_id: int,
    payload: DictUpdate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.update_dict(session, dict_id, payload, current_user))


@router.delete('/dicts/{dict_id}', dependencies=[Depends(require_permission('system:dict:delete'))])
async def delete_dict(
    dict_id: int,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.delete_dict(session, dict_id, current_user))
