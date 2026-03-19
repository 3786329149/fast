from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, IDMixin, TimestampMixin


class OperationLog(IDMixin, TimestampMixin, Base):
    __tablename__ = 'operation_log'

    user_id: Mapped[int | None] = mapped_column(nullable=True)
    module: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(64))
    path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)


class ApiAccessLog(IDMixin, TimestampMixin, Base):
    __tablename__ = 'api_access_log'

    request_id: Mapped[str] = mapped_column(String(64), index=True)
    method: Mapped[str] = mapped_column(String(16))
    path: Mapped[str] = mapped_column(String(255))
    status_code: Mapped[int] = mapped_column(index=True)
    client_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
