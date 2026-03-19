from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Principal
from app.modules.audit.service import service as audit_service
from app.modules.org.models import EmployeeProfile, OrgCompany, OrgDepartment
from app.modules.org.schemas import DepartmentCreate, DepartmentUpdate, EmployeeCreate, EmployeeUpdate
from app.utils.crud import active_to_int, date_to_iso, dt_to_iso, int_to_active, normalize_text, parse_iso_date


class OrgService:
    async def _get_default_org_id(self, session: AsyncSession, current_user: Principal | None = None) -> int:
        if current_user and current_user.org_id:
            return current_user.org_id
        org = await session.scalar(select(OrgCompany).order_by(OrgCompany.id.asc()))
        if org is None:
            org = OrgCompany(name='默认企业', code='DEFAULT', status=1)
            session.add(org)
            await session.flush()
        return org.id

    async def _build_tree_path(self, session: AsyncSession, parent_id: int | None) -> str:
        if parent_id is None:
            return '/'
        parent = await session.get(OrgDepartment, parent_id)
        if parent is None:
            raise HTTPException(status_code=404, detail='上级部门不存在')
        return f"{parent.tree_path}{parent.id}/"

    async def list_departments(self, session: AsyncSession) -> list[dict]:
        stmt = select(OrgDepartment).order_by(OrgDepartment.sort.asc(), OrgDepartment.id.asc())
        rows = list((await session.scalars(stmt)).all())
        return [self.serialize_department(item) for item in rows]

    def serialize_department(self, item: OrgDepartment) -> dict:
        return {
            'id': item.id,
            'org_id': item.org_id,
            'name': item.name,
            'parent_id': item.parent_id,
            'leader_user_id': item.leader_user_id,
            'code': item.code,
            'status': int_to_active(item.status),
            'description': item.description,
            'member_count': item.member_count,
            'tree_path': item.tree_path,
        }

    async def create_department(self, session: AsyncSession, payload: DepartmentCreate, current_user: Principal) -> dict:
        org_id = await self._get_default_org_id(session, current_user)
        department = OrgDepartment(
            org_id=org_id,
            parent_id=payload.parent_id,
            name=payload.name.strip(),
            code=normalize_text(payload.code),
            leader_user_id=payload.leader_user_id,
            sort=0,
            status=active_to_int(payload.status),
            description=normalize_text(payload.description),
            member_count=payload.member_count,
            tree_path=await self._build_tree_path(session, payload.parent_id),
        )
        session.add(department)
        await session.flush()
        await audit_service.log_operation(
            session,
            module='org',
            action='create_department',
            path='/api/admin/v1/org/departments',
            user_id=current_user.user_id,
            detail=department.name,
        )
        await session.commit()
        await session.refresh(department)
        return self.serialize_department(department)

    async def update_department(
        self,
        session: AsyncSession,
        department_id: int,
        payload: DepartmentUpdate,
        current_user: Principal,
    ) -> dict:
        department = await session.get(OrgDepartment, department_id)
        if department is None:
            raise HTTPException(status_code=404, detail='部门不存在')
        if payload.parent_id == department.id:
            raise HTTPException(status_code=400, detail='上级部门不能是自己')
        department.parent_id = payload.parent_id
        department.name = payload.name.strip()
        department.code = normalize_text(payload.code)
        department.leader_user_id = payload.leader_user_id
        department.status = active_to_int(payload.status)
        department.description = normalize_text(payload.description)
        department.member_count = payload.member_count
        department.tree_path = await self._build_tree_path(session, payload.parent_id)
        await audit_service.log_operation(
            session,
            module='org',
            action='update_department',
            path=f'/api/admin/v1/org/departments/{department_id}',
            user_id=current_user.user_id,
            detail=department.name,
        )
        await session.commit()
        await session.refresh(department)
        return self.serialize_department(department)

    async def delete_department(self, session: AsyncSession, department_id: int, current_user: Principal) -> dict:
        department = await session.get(OrgDepartment, department_id)
        if department is None:
            raise HTTPException(status_code=404, detail='部门不存在')
        child = await session.scalar(select(OrgDepartment).where(OrgDepartment.parent_id == department_id))
        if child is not None:
            raise HTTPException(status_code=400, detail='请先删除子部门')
        employee = await session.scalar(select(EmployeeProfile).where(EmployeeProfile.dept_id == department_id))
        if employee is not None:
            raise HTTPException(status_code=400, detail='请先迁移该部门下员工')
        name = department.name
        await session.delete(department)
        await audit_service.log_operation(
            session,
            module='org',
            action='delete_department',
            path=f'/api/admin/v1/org/departments/{department_id}',
            user_id=current_user.user_id,
            detail=name,
        )
        await session.commit()
        return {'id': department_id}

    async def list_employees(self, session: AsyncSession) -> list[dict]:
        stmt = select(EmployeeProfile).order_by(EmployeeProfile.id.asc())
        rows = list((await session.scalars(stmt)).all())
        return [self.serialize_employee(item) for item in rows]

    def serialize_employee(self, item: EmployeeProfile) -> dict:
        return {
            'id': item.id,
            'user_id': item.user_id,
            'name': item.full_name or f'员工{item.user_id}',
            'dept_id': item.dept_id,
            'title': item.job_title or '',
            'status': int_to_active(item.status),
            'phone': item.phone,
            'email': item.email,
            'role_code': item.role_code,
            'joined_at': date_to_iso(item.joined_at),
            'org_id': item.org_id,
            'employee_no': item.employee_no,
            'leader_user_id': item.leader_user_id,
            'remark': item.remark,
            'created_at': dt_to_iso(item.created_at),
        }

    async def create_employee(self, session: AsyncSession, payload: EmployeeCreate, current_user: Principal) -> dict:
        dept = await session.get(OrgDepartment, payload.dept_id)
        if dept is None:
            raise HTTPException(status_code=404, detail='部门不存在')
        employee = EmployeeProfile(
            user_id=payload.user_id,
            org_id=dept.org_id,
            dept_id=payload.dept_id,
            employee_no=f'EMP-{payload.user_id:04d}-{payload.dept_id}',
            full_name=payload.name.strip(),
            job_title=payload.title.strip(),
            status=active_to_int(payload.status),
            phone=normalize_text(payload.phone),
            email=normalize_text(payload.email),
            role_code=normalize_text(payload.role_code),
            joined_at=parse_iso_date(payload.joined_at),
        )
        session.add(employee)
        if dept.member_count is not None:
            dept.member_count = int(dept.member_count or 0) + 1
        await session.flush()
        await audit_service.log_operation(
            session,
            module='org',
            action='create_employee',
            path='/api/admin/v1/org/employees',
            user_id=current_user.user_id,
            detail=employee.full_name,
        )
        await session.commit()
        await session.refresh(employee)
        return self.serialize_employee(employee)

    async def update_employee(
        self,
        session: AsyncSession,
        employee_id: int,
        payload: EmployeeUpdate,
        current_user: Principal,
    ) -> dict:
        employee = await session.get(EmployeeProfile, employee_id)
        if employee is None:
            raise HTTPException(status_code=404, detail='员工不存在')
        dept = await session.get(OrgDepartment, payload.dept_id)
        if dept is None:
            raise HTTPException(status_code=404, detail='部门不存在')
        if employee.dept_id != payload.dept_id:
            old_dept = await session.get(OrgDepartment, employee.dept_id)
            if old_dept and old_dept.member_count is not None and old_dept.member_count > 0:
                old_dept.member_count -= 1
            if dept.member_count is not None:
                dept.member_count = int(dept.member_count or 0) + 1
        employee.user_id = payload.user_id
        employee.org_id = dept.org_id
        employee.dept_id = payload.dept_id
        employee.full_name = payload.name.strip()
        employee.job_title = payload.title.strip()
        employee.status = active_to_int(payload.status)
        employee.phone = normalize_text(payload.phone)
        employee.email = normalize_text(payload.email)
        employee.role_code = normalize_text(payload.role_code)
        employee.joined_at = parse_iso_date(payload.joined_at)
        await audit_service.log_operation(
            session,
            module='org',
            action='update_employee',
            path=f'/api/admin/v1/org/employees/{employee_id}',
            user_id=current_user.user_id,
            detail=employee.full_name,
        )
        await session.commit()
        await session.refresh(employee)
        return self.serialize_employee(employee)

    async def delete_employee(self, session: AsyncSession, employee_id: int, current_user: Principal) -> dict:
        employee = await session.get(EmployeeProfile, employee_id)
        if employee is None:
            raise HTTPException(status_code=404, detail='员工不存在')
        dept = await session.get(OrgDepartment, employee.dept_id)
        if dept and dept.member_count is not None and dept.member_count > 0:
            dept.member_count -= 1
        name = employee.full_name or f'员工{employee.user_id}'
        await session.delete(employee)
        await audit_service.log_operation(
            session,
            module='org',
            action='delete_employee',
            path=f'/api/admin/v1/org/employees/{employee_id}',
            user_id=current_user.user_id,
            detail=name,
        )
        await session.commit()
        return {'id': employee_id}


service = OrgService()
