from fastapi import APIRouter

from app.core.response import success
from app.modules.stats.service import service

router = APIRouter(prefix='/stats', tags=['Statistics'])


@router.get('/dashboard')
async def dashboard() -> dict:
    return success(service.dashboard())
