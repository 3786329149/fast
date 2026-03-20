from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_client_user, get_db
from app.core.response import success
from app.infra.security.token import Principal
from app.modules.payment.schemas import CreatePaymentRequest
from app.modules.payment.service import service

router = APIRouter(prefix='/pay', tags=['Payment Client'])


@router.post('/create')
async def create_payment(
    payload: CreatePaymentRequest,
    current_user: Principal = Depends(get_current_client_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(
        await service.create_payment(
            session,
            current_user=current_user,
            order_no=payload.order_no,
            channel=payload.channel,
            description=payload.description,
            openid=payload.openid,
        )
    )
