from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, IDMixin, TimestampMixin


class NotifyTemplate(IDMixin, TimestampMixin, Base):
    __tablename__ = 'notify_template'

    name: Mapped[str] = mapped_column(String(64))
    channel: Mapped[str] = mapped_column(String(32))
    template_code: Mapped[str] = mapped_column(String(128))
    content: Mapped[str | None] = mapped_column(Text, nullable=True)


class NotifyMessage(IDMixin, TimestampMixin, Base):
    __tablename__ = 'notify_message'

    channel: Mapped[str] = mapped_column(String(32))
    receiver: Mapped[str] = mapped_column(String(128))
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default='pending')
