from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.modules.payment.service import service

router = APIRouter(prefix='/pay', tags=['Payment Callback'])


@router.post('/wechat/callback')
async def wechat_payment_callback(request: Request, session: AsyncSession = Depends(get_db)) -> JSONResponse:
    body = (await request.body()).decode('utf-8')
    headers = {key: value for key, value in request.headers.items()}
    try:
        result = await service.handle_wechat_callback(session, headers=headers, body=body)
        return JSONResponse(status_code=200, content={'code': result['code'], 'message': result['message']})
    except Exception as exc:
        return JSONResponse(status_code=200, content={'code': 'FAIL', 'message': str(exc)[:120]})
