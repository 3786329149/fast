from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user, get_db
from app.core.response import success
from app.infra.security.token import Principal
from app.modules.iam.schemas import AdminLoginRequest
from app.modules.iam.service import service

router = APIRouter(prefix='/auth', tags=['Admin Auth'])


@router.post('/login')
async def admin_login(payload: AdminLoginRequest, session: AsyncSession = Depends(get_db)) -> dict:
    result = await service.admin_login(session, payload.account, payload.password)
    return success(result.to_dict())


@router.get('/me')
async def admin_me(current_user: Principal = Depends(get_current_admin_user)) -> dict:
    return success(current_user.model_dump())
