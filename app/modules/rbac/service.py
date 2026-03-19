from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Principal
from app.modules.audit.service import service as audit_service
from app.modules.rbac.models import (
    AdminMenu,
    AdminPermission,
    AdminRole,
    AdminRoleMenu,
    AdminRolePermission,
    AdminUserRole,
)
from app.modules.rbac.schemas import MenuCreate, MenuUpdate, PermissionCreate, PermissionUpdate, RoleCreate, RoleUpdate
from app.utils.crud import active_to_int, int_to_active, normalize_text, unique_ordered


class RBACService:
    async def list_roles(self, session: AsyncSession) -> list[dict]:
        roles = list((await session.scalars(select(AdminRole).order_by(AdminRole.id.asc()))).all())
        role_ids = [role.id for role in roles]
        mapping: dict[int, list[str]] = {role_id: [] for role_id in role_ids}
        if role_ids:
            rels = list(
                (
                    await session.execute(
                        select(AdminRolePermission.role_id, AdminPermission.code)
                        .join(AdminPermission, AdminPermission.id == AdminRolePermission.permission_id)
                        .where(AdminRolePermission.role_id.in_(role_ids))
                    )
                ).all()
            )
            for role_id, code in rels:
                mapping.setdefault(role_id, []).append(code)
        return [self.serialize_role(role, mapping.get(role.id, [])) for role in roles]

    def serialize_role(self, role: AdminRole, permission_codes: list[str]) -> dict:
        return {
            'id': role.id,
            'name': role.name,
            'code': role.code,
            'data_scope': role.data_scope,
            'status': int_to_active(role.status),
            'description': role.description,
            'permission_codes': unique_ordered(permission_codes),
        }

    async def _sync_role_permissions(self, session: AsyncSession, role_id: int, permission_codes: list[str]) -> None:
        await session.execute(delete(AdminRolePermission).where(AdminRolePermission.role_id == role_id))
        if not permission_codes:
            return
        permissions = list((await session.scalars(select(AdminPermission).where(AdminPermission.code.in_(permission_codes)))).all())
        for permission in permissions:
            session.add(AdminRolePermission(role_id=role_id, permission_id=permission.id))
        await session.flush()

    async def create_role(self, session: AsyncSession, payload: RoleCreate, current_user: Principal) -> dict:
        exists = await session.scalar(select(AdminRole).where(AdminRole.code == payload.code.strip()))
        if exists is not None:
            raise HTTPException(status_code=400, detail='角色编码已存在')
        role = AdminRole(
            name=payload.name.strip(),
            code=payload.code.strip(),
            data_scope=payload.data_scope,
            status=active_to_int(payload.status),
            description=normalize_text(payload.description),
        )
        session.add(role)
        await session.flush()
        await self._sync_role_permissions(session, role.id, payload.permission_codes)
        await audit_service.log_operation(
            session,
            module='rbac',
            action='create_role',
            path='/api/admin/v1/rbac/roles',
            user_id=current_user.user_id,
            detail=role.code,
        )
        await session.commit()
        return self.serialize_role(role, payload.permission_codes)

    async def update_role(self, session: AsyncSession, role_id: int, payload: RoleUpdate, current_user: Principal) -> dict:
        role = await session.get(AdminRole, role_id)
        if role is None:
            raise HTTPException(status_code=404, detail='角色不存在')
        exists = await session.scalar(select(AdminRole).where(AdminRole.code == payload.code.strip(), AdminRole.id != role_id))
        if exists is not None:
            raise HTTPException(status_code=400, detail='角色编码已存在')
        role.name = payload.name.strip()
        role.code = payload.code.strip()
        role.data_scope = payload.data_scope
        role.status = active_to_int(payload.status)
        role.description = normalize_text(payload.description)
        await self._sync_role_permissions(session, role.id, payload.permission_codes)
        await audit_service.log_operation(
            session,
            module='rbac',
            action='update_role',
            path=f'/api/admin/v1/rbac/roles/{role_id}',
            user_id=current_user.user_id,
            detail=role.code,
        )
        await session.commit()
        return self.serialize_role(role, payload.permission_codes)

    async def delete_role(self, session: AsyncSession, role_id: int, current_user: Principal) -> dict:
        role = await session.get(AdminRole, role_id)
        if role is None:
            raise HTTPException(status_code=404, detail='角色不存在')
        await session.execute(delete(AdminRolePermission).where(AdminRolePermission.role_id == role_id))
        await session.execute(delete(AdminRoleMenu).where(AdminRoleMenu.role_id == role_id))
        await session.execute(delete(AdminUserRole).where(AdminUserRole.role_id == role_id))
        code = role.code
        await session.delete(role)
        await audit_service.log_operation(
            session,
            module='rbac',
            action='delete_role',
            path=f'/api/admin/v1/rbac/roles/{role_id}',
            user_id=current_user.user_id,
            detail=code,
        )
        await session.commit()
        return {'id': role_id}

    async def list_menus(self, session: AsyncSession) -> list[dict]:
        rows = list((await session.scalars(select(AdminMenu).order_by(AdminMenu.sort.asc(), AdminMenu.id.asc()))).all())
        return [self.serialize_menu(item) for item in rows]

    def serialize_menu(self, item: AdminMenu) -> dict:
        return {
            'id': item.id,
            'name': item.name,
            'type': item.type,
            'path': item.path,
            'permission_code': item.permission_code,
            'parent_id': item.parent_id,
            'sort': item.sort,
            'status': int_to_active(item.status),
            'component': item.component,
            'icon': item.icon,
            'remark': item.remark,
        }

    async def create_menu(self, session: AsyncSession, payload: MenuCreate, current_user: Principal) -> dict:
        if payload.parent_id is not None and await session.get(AdminMenu, payload.parent_id) is None:
            raise HTTPException(status_code=404, detail='上级菜单不存在')
        menu = AdminMenu(
            name=payload.name.strip(),
            type=payload.type,
            path=normalize_text(payload.path),
            permission_code=normalize_text(payload.permission_code),
            parent_id=payload.parent_id,
            sort=payload.sort,
            status=active_to_int(payload.status),
            component=normalize_text(payload.component),
            icon=normalize_text(payload.icon),
            remark=normalize_text(payload.remark),
        )
        session.add(menu)
        await session.flush()
        await audit_service.log_operation(
            session,
            module='rbac',
            action='create_menu',
            path='/api/admin/v1/rbac/menus',
            user_id=current_user.user_id,
            detail=menu.name,
        )
        await session.commit()
        return self.serialize_menu(menu)

    async def update_menu(self, session: AsyncSession, menu_id: int, payload: MenuUpdate, current_user: Principal) -> dict:
        menu = await session.get(AdminMenu, menu_id)
        if menu is None:
            raise HTTPException(status_code=404, detail='菜单不存在')
        if payload.parent_id == menu_id:
            raise HTTPException(status_code=400, detail='上级菜单不能是自己')
        if payload.parent_id is not None and await session.get(AdminMenu, payload.parent_id) is None:
            raise HTTPException(status_code=404, detail='上级菜单不存在')
        menu.name = payload.name.strip()
        menu.type = payload.type
        menu.path = normalize_text(payload.path)
        menu.permission_code = normalize_text(payload.permission_code)
        menu.parent_id = payload.parent_id
        menu.sort = payload.sort
        menu.status = active_to_int(payload.status)
        menu.component = normalize_text(payload.component)
        menu.icon = normalize_text(payload.icon)
        menu.remark = normalize_text(payload.remark)
        await audit_service.log_operation(
            session,
            module='rbac',
            action='update_menu',
            path=f'/api/admin/v1/rbac/menus/{menu_id}',
            user_id=current_user.user_id,
            detail=menu.name,
        )
        await session.commit()
        return self.serialize_menu(menu)

    async def delete_menu(self, session: AsyncSession, menu_id: int, current_user: Principal) -> dict:
        menu = await session.get(AdminMenu, menu_id)
        if menu is None:
            raise HTTPException(status_code=404, detail='菜单不存在')
        child = await session.scalar(select(AdminMenu).where(AdminMenu.parent_id == menu_id))
        if child is not None:
            raise HTTPException(status_code=400, detail='请先删除子菜单')
        await session.execute(delete(AdminRoleMenu).where(AdminRoleMenu.menu_id == menu_id))
        name = menu.name
        await session.delete(menu)
        await audit_service.log_operation(
            session,
            module='rbac',
            action='delete_menu',
            path=f'/api/admin/v1/rbac/menus/{menu_id}',
            user_id=current_user.user_id,
            detail=name,
        )
        await session.commit()
        return {'id': menu_id}

    async def list_permissions(self, session: AsyncSession) -> list[dict]:
        rows = list((await session.scalars(select(AdminPermission).order_by(AdminPermission.id.asc()))).all())
        return [self.serialize_permission(item) for item in rows]

    def serialize_permission(self, item: AdminPermission) -> dict:
        return {
            'id': item.id,
            'code': item.code,
            'name': item.name,
            'module': item.group_name,
            'description': item.remark,
        }

    async def create_permission(
        self,
        session: AsyncSession,
        payload: PermissionCreate,
        current_user: Principal,
    ) -> dict:
        exists = await session.scalar(select(AdminPermission).where(AdminPermission.code == payload.code.strip()))
        if exists is not None:
            raise HTTPException(status_code=400, detail='权限码已存在')
        permission = AdminPermission(
            code=payload.code.strip(),
            name=payload.name.strip(),
            group_name=normalize_text(payload.module) or 'general',
            remark=normalize_text(payload.description),
        )
        session.add(permission)
        await session.flush()
        await audit_service.log_operation(
            session,
            module='rbac',
            action='create_permission',
            path='/api/admin/v1/rbac/permissions',
            user_id=current_user.user_id,
            detail=permission.code,
        )
        await session.commit()
        return self.serialize_permission(permission)

    async def update_permission(
        self,
        session: AsyncSession,
        permission_id: int,
        payload: PermissionUpdate,
        current_user: Principal,
    ) -> dict:
        permission = await session.get(AdminPermission, permission_id)
        if permission is None:
            raise HTTPException(status_code=404, detail='权限点不存在')
        exists = await session.scalar(
            select(AdminPermission).where(AdminPermission.code == payload.code.strip(), AdminPermission.id != permission_id)
        )
        if exists is not None:
            raise HTTPException(status_code=400, detail='权限码已存在')
        permission.code = payload.code.strip()
        permission.name = payload.name.strip()
        permission.group_name = normalize_text(payload.module) or 'general'
        permission.remark = normalize_text(payload.description)
        await audit_service.log_operation(
            session,
            module='rbac',
            action='update_permission',
            path=f'/api/admin/v1/rbac/permissions/{permission_id}',
            user_id=current_user.user_id,
            detail=permission.code,
        )
        await session.commit()
        return self.serialize_permission(permission)

    async def delete_permission(self, session: AsyncSession, permission_id: int, current_user: Principal) -> dict:
        permission = await session.get(AdminPermission, permission_id)
        if permission is None:
            raise HTTPException(status_code=404, detail='权限点不存在')
        await session.execute(delete(AdminRolePermission).where(AdminRolePermission.permission_id == permission_id))
        code = permission.code
        await session.delete(permission)
        await audit_service.log_operation(
            session,
            module='rbac',
            action='delete_permission',
            path=f'/api/admin/v1/rbac/permissions/{permission_id}',
            user_id=current_user.user_id,
            detail=code,
        )
        await session.commit()
        return {'id': permission_id}


service = RBACService()
