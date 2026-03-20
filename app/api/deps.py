from __future__ import annotations

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.enums import TokenScene
from app.core.exceptions import AppException
from app.core.security import Principal, decode_token

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db(session: AsyncSession = Depends(get_db_session)) -> AsyncSession:
    return session


async def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> Principal:
    if credentials is None:
        raise AppException('缺少访问令牌', status_code=status.HTTP_401_UNAUTHORIZED)
    try:
        payload = decode_token(credentials.credentials)
    except ValueError as exc:
        raise AppException('访问令牌无效', status_code=status.HTTP_401_UNAUTHORIZED) from exc
    return Principal(
        user_id=int(payload.sub),
        username=payload.username,
        scene=payload.scene,
        org_id=payload.org_id,
        dept_id=payload.dept_id,
        roles=payload.roles,
        permissions=payload.permissions,
    )


async def get_current_client_user(principal: Principal = Depends(get_current_principal)) -> Principal:
    if principal.scene != TokenScene.CLIENT:
        raise AppException('非客户端令牌', status_code=status.HTTP_403_FORBIDDEN)
    return principal


async def get_current_admin_user(principal: Principal = Depends(get_current_principal)) -> Principal:
    if principal.scene != TokenScene.ADMIN:
        raise AppException('非后台令牌', status_code=status.HTTP_403_FORBIDDEN)
    return principal


def require_permission(code: str):
    async def checker(principal: Principal = Depends(get_current_admin_user)) -> Principal:
        if code not in principal.permissions and '*' not in principal.permissions:
            raise AppException(f'缺少权限: {code}', status_code=status.HTTP_403_FORBIDDEN)
        return principal

    return checker
