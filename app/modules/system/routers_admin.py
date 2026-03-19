from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user, get_db, require_permission
from app.core.response import success
from app.core.security import Principal
from app.modules.system.schemas import ConfigCreate, ConfigUpdate, DictCreate, DictUpdate
from app.modules.system.service import service

router = APIRouter(prefix='/system', tags=['System'])


@router.get('/configs', dependencies=[Depends(require_permission('system:config:list'))])
async def list_configs(session: AsyncSession = Depends(get_db)) -> dict:
    return success(await service.list_configs(session))


@router.post('/configs', dependencies=[Depends(require_permission('system:config:create'))])
async def create_config(
    payload: ConfigCreate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.create_config(session, payload, current_user))


@router.put('/configs/{config_id}', dependencies=[Depends(require_permission('system:config:update'))])
async def update_config(
    config_id: int,
    payload: ConfigUpdate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.update_config(session, config_id, payload, current_user))


@router.delete('/configs/{config_id}', dependencies=[Depends(require_permission('system:config:delete'))])
async def delete_config(
    config_id: int,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.delete_config(session, config_id, current_user))


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
