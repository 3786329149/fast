from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_client_user, get_db
from app.core.enums import TokenScene
from app.core.response import success
from app.infra.security.token import Principal
from app.modules.iam.schemas import (
    BindWechatRequest,
    LoginByCodeRequest,
    LoginByPasswordRequest,
    QrLoginCreateRequest,
    RefreshTokenRequest,
    SendCodeRequest,
)
from app.modules.iam.service import service

router = APIRouter(tags=['Client Auth'])


@router.post('/auth/send-code')
async def send_code(payload: SendCodeRequest) -> dict:
    return success({'phone': payload.phone, 'scene': payload.scene, 'sent': True, 'provider': 'mock'})


@router.post('/auth/login-by-code')
async def login_by_code(payload: LoginByCodeRequest, session: AsyncSession = Depends(get_db)) -> dict:
    result = await service.login_by_code(session, payload.phone, payload.code)
    return success(result.to_dict())


@router.post('/auth/login-by-password')
async def login_by_password(payload: LoginByPasswordRequest, session: AsyncSession = Depends(get_db)) -> dict:
    result = await service.login_by_password(session, payload.account, payload.password)
    return success(result.to_dict())


@router.post('/auth/refresh')
async def refresh_token(payload: RefreshTokenRequest) -> dict:
    result = service.refresh_token(payload.refresh_token, expected_scene=TokenScene.CLIENT)
    return success(result.to_dict())


@router.post('/auth/bind-wechat')
async def bind_wechat(
    payload: BindWechatRequest,
    current_user: Principal = Depends(get_current_client_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.bind_wechat(session, current_user=current_user, union_token=payload.union_token, openid=payload.openid))


@router.get('/auth/me')
async def client_me(current_user: Principal = Depends(get_current_client_user)) -> dict:
    return success(current_user.model_dump())


@router.post('/qr-login/create')
async def create_qr_ticket(payload: QrLoginCreateRequest) -> dict:
    return success(await service.create_qr_ticket(payload.scene))


@router.get('/qr-login/status/{ticket}')
async def qr_ticket_status(ticket: str) -> dict:
    return success(await service.get_qr_status(ticket))
