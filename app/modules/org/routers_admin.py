from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user, get_db, require_permission
from app.core.response import success
from app.core.security import Principal
from app.modules.org.schemas import DepartmentCreate, DepartmentUpdate, EmployeeCreate, EmployeeUpdate
from app.modules.org.service import service

router = APIRouter(prefix='/org', tags=['Organization'])


@router.get('/departments', dependencies=[Depends(require_permission('org:department:list'))])
async def list_departments(session: AsyncSession = Depends(get_db)) -> dict:
    return success(await service.list_departments(session))


@router.post('/departments', dependencies=[Depends(require_permission('org:department:create'))])
async def create_department(
    payload: DepartmentCreate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.create_department(session, payload, current_user))


@router.put('/departments/{department_id}', dependencies=[Depends(require_permission('org:department:update'))])
async def update_department(
    department_id: int,
    payload: DepartmentUpdate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.update_department(session, department_id, payload, current_user))


@router.delete('/departments/{department_id}', dependencies=[Depends(require_permission('org:department:delete'))])
async def delete_department(
    department_id: int,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.delete_department(session, department_id, current_user))


@router.get('/employees', dependencies=[Depends(require_permission('org:employee:list'))])
async def list_employees(session: AsyncSession = Depends(get_db)) -> dict:
    return success(await service.list_employees(session))


@router.post('/employees', dependencies=[Depends(require_permission('org:employee:create'))])
async def create_employee(
    payload: EmployeeCreate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.create_employee(session, payload, current_user))


@router.put('/employees/{employee_id}', dependencies=[Depends(require_permission('org:employee:update'))])
async def update_employee(
    employee_id: int,
    payload: EmployeeUpdate,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.update_employee(session, employee_id, payload, current_user))


@router.delete('/employees/{employee_id}', dependencies=[Depends(require_permission('org:employee:delete'))])
async def delete_employee(
    employee_id: int,
    current_user: Principal = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return success(await service.delete_employee(session, employee_id, current_user))
