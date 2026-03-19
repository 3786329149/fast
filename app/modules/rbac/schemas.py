from __future__ import annotations

from pydantic import BaseModel, Field


class RoleBase(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    code: str = Field(min_length=1, max_length=64)
    data_scope: str = 'SELF'
    status: str = 'active'
    description: str | None = None
    permission_codes: list[str] = Field(default_factory=list)


class RoleCreate(RoleBase):
    pass


class RoleUpdate(RoleBase):
    pass


class RoleOut(RoleBase):
    id: int


class MenuBase(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    type: str = Field(min_length=1, max_length=16)
    path: str | None = None
    permission_code: str | None = None
    parent_id: int | None = None
    sort: int = 0
    status: str = 'active'
    component: str | None = None
    icon: str | None = None
    remark: str | None = None


class MenuCreate(MenuBase):
    pass


class MenuUpdate(MenuBase):
    pass


class MenuOut(MenuBase):
    id: int


class PermissionBase(BaseModel):
    code: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=64)
    module: str | None = Field(default=None, max_length=64)
    description: str | None = None


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(PermissionBase):
    pass


class PermissionOut(PermissionBase):
    id: int
