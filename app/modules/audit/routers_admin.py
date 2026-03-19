from fastapi import APIRouter

from app.core.response import success
from app.modules.audit.service import service

router = APIRouter(prefix='/audit', tags=['Audit'])


@router.get('/operation-logs')
async def list_operation_logs() -> dict:
    return success(service.list_operation_logs())
