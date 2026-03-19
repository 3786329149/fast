from __future__ import annotations

from pydantic import BaseModel


class OperationLogOut(BaseModel):
    id: int
    module: str
    action: str
    path: str
    operator: str | None = None
    detail: str | None = None
    created_at: str | None = None

class ClearOperationLogsRequest(BaseModel):
    module: str | None = None
