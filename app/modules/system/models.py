from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, IDMixin, TimestampMixin


class SystemConfig(IDMixin, TimestampMixin, Base):
    __tablename__ = 'system_config'

    config_key: Mapped[str] = mapped_column(String(128), unique=True)
    config_value: Mapped[str] = mapped_column(Text)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)


class SystemDict(IDMixin, TimestampMixin, Base):
    __tablename__ = 'system_dict'

    dict_type: Mapped[str] = mapped_column(String(64), index=True)
    dict_label: Mapped[str] = mapped_column(String(64))
    dict_value: Mapped[str] = mapped_column(String(64))
    sort: Mapped[int] = mapped_column(default=0)
