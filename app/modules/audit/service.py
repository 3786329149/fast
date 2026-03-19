from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import OperationLog
from app.utils.crud import dt_to_iso


class AuditService:
    async def log_operation(
        self,
        session: AsyncSession,
        *,
        module: str,
        action: str,
        path: str,
        user_id: int | None = None,
        detail: str | None = None,
    ) -> None:
        session.add(
            OperationLog(
                user_id=user_id,
                module=module,
                action=action,
                path=path,
                detail=detail,
            )
        )
        await session.flush()

    async def list_operation_logs(self,session: AsyncSession) -> list[dict]:
        stmt = select(OperationLog).order_by(OperationLog.created_at.desc(), OperationLog.id.desc())
        rows = list((await session.scalars(stmt)).all())
        return [
            {
                'id': row.id,
                'module': row.module,
                'action': row.action,
                'path': row.path or '',
                'operator': f'#{row.user_id}' if row.user_id else 'system',
                'detail': row.detail,
                'created_at': dt_to_iso(row.created_at),
            }
            for row in rows
        ]

    async def delete_operation_log(self, session: AsyncSession, log_id: int) -> dict:
        row = await session.get(OperationLog, log_id)
        if row is None:
            raise ValueError('操作日志不存在')
        await session.delete(row)
        await session.commit()
        return {'id': log_id}

    async def clear_operation_logs(self, session: AsyncSession, module: str | None = None) -> dict:
        stmt = delete(OperationLog)
        if module:
            stmt = stmt.where(OperationLog.module == module)
        result = await session.execute(stmt)
        await session.commit()
        return {'deleted_count': int(result.rowcount or 0)}


service = AuditService()
