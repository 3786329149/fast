from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user, get_db, require_permission
from app.core.response import success
from app.infra.security.token import Principal
from app.modules.file.schemas import FileAssetCreate, FileAssetUpdate, UploadTokenRequest
from app.modules.file.service import service

router = APIRouter(prefix='/files', tags=['File Admin'])



@router.post('/upload-token', dependencies=[Depends(require_permission('file:asset:create'))])
async def create_admin_upload_token(payload: UploadTokenRequest) -> dict:
    return success(service.create_upload_token(payload.file_name, payload.content_type))

@router.get('/assets', dependencies=[Depends(require_permission('file:asset:list'))])
async def list_assets(session: AsyncSession = Depends(get_db)) -> dict:
    return success(await service.list_assets(session))

@router.post('/assets', dependencies=[Depends(require_permission('file:asset:create'))])
async def create_asset(
    payload: FileAssetCreate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.create_asset(session, payload, current_user))

@router.put('/assets/{asset_id}', dependencies=[Depends(require_permission('file:asset:update'))])
async def update_asset(
    asset_id: int,
    payload: FileAssetUpdate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.update_asset(session, asset_id, payload, current_user))

@router.delete('/assets/{asset_id}', dependencies=[Depends(require_permission('file:asset:delete'))])
async def delete_asset(
    asset_id: int,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.delete_asset(session, asset_id, current_user))
