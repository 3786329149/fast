from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base, IDMixin, TimestampMixin


class FileAsset(IDMixin, TimestampMixin, Base):
    __tablename__ = 'file_asset'

    storage_provider: Mapped[str] = mapped_column(String(32))
    bucket: Mapped[str | None] = mapped_column(String(128), nullable=True)
    object_key: Mapped[str] = mapped_column(String(255), index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    file_ext: Mapped[str | None] = mapped_column(String(32), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    file_size: Mapped[int | None] = mapped_column(nullable=True)
    file_url: Mapped[str | None] = mapped_column(Text, nullable=True)
