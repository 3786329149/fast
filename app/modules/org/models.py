from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, IDMixin, TimestampMixin


class OrgCompany(IDMixin, TimestampMixin, Base):
    __tablename__ = 'org_company'

    name: Mapped[str] = mapped_column(String(128), unique=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    status: Mapped[int] = mapped_column(default=1)


class OrgDepartment(IDMixin, TimestampMixin, Base):
    __tablename__ = 'org_department'

    org_id: Mapped[int] = mapped_column(ForeignKey('org_company.id'), index=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey('org_department.id'), nullable=True)
    name: Mapped[str] = mapped_column(String(128))
    tree_path: Mapped[str] = mapped_column(String(255), default='/')
    leader_user_id: Mapped[int | None] = mapped_column(nullable=True)
    sort: Mapped[int] = mapped_column(default=0)
    status: Mapped[int] = mapped_column(default=1)


class EmployeeProfile(IDMixin, TimestampMixin, Base):
    __tablename__ = 'employee_profile'

    user_id: Mapped[int] = mapped_column(index=True)
    org_id: Mapped[int] = mapped_column(ForeignKey('org_company.id'), index=True)
    dept_id: Mapped[int] = mapped_column(ForeignKey('org_department.id'), index=True)
    employee_no: Mapped[str] = mapped_column(String(64), unique=True)
    job_title: Mapped[str | None] = mapped_column(String(128), nullable=True)
    leader_user_id: Mapped[int | None] = mapped_column(nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
