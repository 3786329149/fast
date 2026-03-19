from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.enums import TokenScene
from app.core.security import Principal, decode_token

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db(session: AsyncSession = Depends(get_db_session)) -> AsyncSession:
    return session


async def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> Principal:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='缺少访问令牌')
    try:
        payload = decode_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='访问令牌无效') from exc
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='非客户端令牌')
    return principal


async def get_current_admin_user(principal: Principal = Depends(get_current_principal)) -> Principal:
    if principal.scene != TokenScene.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='非后台令牌')
    return principal


def require_permission(code: str):
    async def checker(principal: Principal = Depends(get_current_admin_user)) -> Principal:
        if code not in principal.permissions and '*' not in principal.permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'缺少权限: {code}')
        return principal

    return checker
