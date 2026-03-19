from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, IDMixin, TimestampMixin


class CmsBanner(IDMixin, TimestampMixin, Base):
    __tablename__ = 'cms_banner'

    title: Mapped[str] = mapped_column(String(128))
    image_url: Mapped[str] = mapped_column(Text)
    link_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort: Mapped[int] = mapped_column(default=0)
    status: Mapped[int] = mapped_column(default=1)


class CmsNotice(IDMixin, TimestampMixin, Base):
    __tablename__ = 'cms_notice'

    title: Mapped[str] = mapped_column(String(128))
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[int] = mapped_column(default=1)
