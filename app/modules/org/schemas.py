from pydantic import BaseModel


class DepartmentOut(BaseModel):
    id: int
    name: str
    parent_id: int | None = None
    leader_user_id: int | None = None


class EmployeeOut(BaseModel):
    id: int
    user_id: int
    name: str
    dept_id: int
    title: str
