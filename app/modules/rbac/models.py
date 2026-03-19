from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, IDMixin, TimestampMixin


class AdminRole(IDMixin, TimestampMixin, Base):
    __tablename__ = 'admin_role'

    name: Mapped[str] = mapped_column(String(64), unique=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    data_scope: Mapped[str] = mapped_column(String(32), default='SELF')
    status: Mapped[int] = mapped_column(default=1)


class AdminMenu(IDMixin, TimestampMixin, Base):
    __tablename__ = 'admin_menu'

    parent_id: Mapped[int | None] = mapped_column(ForeignKey('admin_menu.id'), nullable=True)
    name: Mapped[str] = mapped_column(String(64))
    type: Mapped[str] = mapped_column(String(16))
    path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    component: Mapped[str | None] = mapped_column(String(255), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(64), nullable=True)
    permission_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sort: Mapped[int] = mapped_column(default=0)


class AdminPermission(IDMixin, TimestampMixin, Base):
    __tablename__ = 'admin_permission'

    code: Mapped[str] = mapped_column(String(128), unique=True)
    name: Mapped[str] = mapped_column(String(64))
    group_name: Mapped[str] = mapped_column(String(64))
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)


class AdminUserRole(IDMixin, TimestampMixin, Base):
    __tablename__ = 'admin_user_role'

    user_id: Mapped[int] = mapped_column(index=True)
    role_id: Mapped[int] = mapped_column(ForeignKey('admin_role.id'), index=True)


class AdminRolePermission(IDMixin, TimestampMixin, Base):
    __tablename__ = 'admin_role_permission'

    role_id: Mapped[int] = mapped_column(ForeignKey('admin_role.id'), index=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey('admin_permission.id'), index=True)


class AdminRoleMenu(IDMixin, TimestampMixin, Base):
    __tablename__ = 'admin_role_menu'

    role_id: Mapped[int] = mapped_column(ForeignKey('admin_role.id'), index=True)
    menu_id: Mapped[int] = mapped_column(ForeignKey('admin_menu.id'), index=True)
