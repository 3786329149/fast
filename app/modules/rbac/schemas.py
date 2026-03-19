from pydantic import BaseModel


class RoleOut(BaseModel):
    id: int
    name: str
    code: str
    data_scope: str


class MenuOut(BaseModel):
    id: int
    name: str
    type: str
    path: str | None = None
    permission_code: str | None = None


class PermissionOut(BaseModel):
    id: int
    code: str
    name: str
