from __future__ import annotations

from pydantic import BaseModel, Field


class DepartmentBase(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    parent_id: int | None = None
    leader_user_id: int | None = None
    code: str | None = Field(default=None, max_length=64)
    status: str = 'active'
    description: str | None = None
    member_count: int = Field(default=0, ge=0)


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(DepartmentBase):
    pass


class DepartmentOut(DepartmentBase):
    id: int
    org_id: int
    tree_path: str


class EmployeeBase(BaseModel):
    user_id: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=128)
    dept_id: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=128)
    status: str = 'active'
    phone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=128)
    role_code: str | None = Field(default=None, max_length=64)
    joined_at: str | None = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(EmployeeBase):
    pass


class EmployeeOut(EmployeeBase):
    id: int
    org_id: int
    employee_no: str
    leader_user_id: int | None = None
    remark: str | None = None
