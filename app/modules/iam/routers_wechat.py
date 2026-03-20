from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_client_user, get_db
from app.core.response import success
from app.infra.security.token import Principal
from app.modules.iam.schemas import BindMobileRequest, QrLoginConfirmRequest, QrLoginScanRequest, WechatMiniLoginRequest
from app.modules.iam.service import service

router = APIRouter(tags=['WeChat Auth'])


@router.post('/auth/login')
async def wechat_login(payload: WechatMiniLoginRequest, session: AsyncSession = Depends(get_db)) -> dict:
    return success(await service.wechat_login(session, payload.code))


@router.post('/auth/bind-mobile')
async def bind_mobile(payload: BindMobileRequest, session: AsyncSession = Depends(get_db)) -> dict:
    result = await service.bind_mobile(
        session,
        phone=payload.phone,
        code=payload.code,
        union_token=payload.union_token,
        phone_code=payload.phone_code,
    )
    return success(result.to_dict())


@router.post('/qr-login/scan')
async def scan_qr_ticket(
    payload: QrLoginScanRequest,
    current_user: Principal = Depends(get_current_client_user),
) -> dict:
    return success(await service.scan_qr_ticket(payload.ticket, user_id=current_user.user_id))


@router.post('/qr-login/confirm')
async def confirm_qr_ticket(
    payload: QrLoginConfirmRequest,
    current_user: Principal = Depends(get_current_client_user),
) -> dict:
    return success(await service.confirm_qr_ticket(payload.ticket, user_id=current_user.user_id))
