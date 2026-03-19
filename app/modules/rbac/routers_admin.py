from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user, get_db, require_permission
from app.core.response import success
from app.core.security import Principal
from app.modules.rbac.schemas import MenuCreate, MenuUpdate, PermissionCreate, PermissionUpdate, RoleCreate, RoleUpdate
from app.modules.rbac.service import service

router = APIRouter(prefix='/rbac', tags=['RBAC'])


@router.get('/roles', dependencies=[Depends(require_permission('rbac:role:list'))])
async def list_roles(session: AsyncSession = Depends(get_db)) -> dict:
    return success(await service.list_roles(session))


@router.post('/roles', dependencies=[Depends(require_permission('rbac:role:create'))])
async def create_role(
    payload: RoleCreate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.create_role(session, payload, current_user))


@router.put('/roles/{role_id}', dependencies=[Depends(require_permission('rbac:role:update'))])
async def update_role(
    role_id: int,
    payload: RoleUpdate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.update_role(session, role_id, payload, current_user))


@router.delete('/roles/{role_id}', dependencies=[Depends(require_permission('rbac:role:delete'))])
async def delete_role(
    role_id: int,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.delete_role(session, role_id, current_user))


@router.get('/menus', dependencies=[Depends(require_permission('rbac:menu:list'))])
async def list_menus(session: AsyncSession = Depends(get_db)) -> dict:
    return success(await service.list_menus(session))


@router.post('/menus', dependencies=[Depends(require_permission('rbac:menu:create'))])
async def create_menu(
    payload: MenuCreate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.create_menu(session, payload, current_user))


@router.put('/menus/{menu_id}', dependencies=[Depends(require_permission('rbac:menu:update'))])
async def update_menu(
    menu_id: int,
    payload: MenuUpdate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.update_menu(session, menu_id, payload, current_user))


@router.delete('/menus/{menu_id}', dependencies=[Depends(require_permission('rbac:menu:delete'))])
async def delete_menu(
    menu_id: int,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.delete_menu(session, menu_id, current_user))


@router.get('/permissions', dependencies=[Depends(require_permission('rbac:permission:list'))])
async def list_permissions(session: AsyncSession = Depends(get_db)) -> dict:
    return success(await service.list_permissions(session))


@router.post('/permissions', dependencies=[Depends(require_permission('rbac:permission:create'))])
async def create_permission(
    payload: PermissionCreate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.create_permission(session, payload, current_user))


@router.put('/permissions/{permission_id}', dependencies=[Depends(require_permission('rbac:permission:update'))])
async def update_permission(
    permission_id: int,
    payload: PermissionUpdate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.update_permission(session, permission_id, payload, current_user))


@router.delete('/permissions/{permission_id}', dependencies=[Depends(require_permission('rbac:permission:delete'))])
async def delete_permission(
    permission_id: int,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.delete_permission(session, permission_id, current_user))
