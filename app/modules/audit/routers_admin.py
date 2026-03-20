from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user, get_db, require_permission
from app.core.exceptions import AppException
from app.core.response import success
from app.infra.security.token import Principal
from app.modules.audit.schemas import ClearOperationLogsRequest
from app.modules.audit.service import service

router = APIRouter(prefix='/audit', tags=['Audit'])


@router.get('/operation-logs', dependencies=[Depends(require_permission('audit:log:list'))])
async def list_operation_logs(session: AsyncSession = Depends(get_db)) -> dict:
    return success(await service.list_operation_logs(session))


@router.delete('/operation-logs/{log_id}', dependencies=[Depends(require_permission('audit:log:delete'))])
async def delete_operation_log(
    log_id: int,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    try:
        result = await service.delete_operation_log(session, log_id)
        return success(result)
    except ValueError as exc:
        raise AppException(str(exc), status_code=404) from exc


@router.post('/operation-logs/clear', dependencies=[Depends(require_permission('audit:log:delete'))])
async def clear_operation_logs(
    payload: ClearOperationLogsRequest,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.clear_operation_logs(session, payload.module))
