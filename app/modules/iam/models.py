from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base, IDMixin, SoftDeleteMixin, TimestampMixin


class User(IDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = 'user'

    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    mobile: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    status: Mapped[int] = mapped_column(default=1)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)


class UserProfile(IDMixin, TimestampMixin, Base):
    __tablename__ = 'user_profile'

    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), index=True)
    nickname: Mapped[str | None] = mapped_column(String(64), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(16), nullable=True)
    region: Mapped[str | None] = mapped_column(String(128), nullable=True)


class UserIdentity(IDMixin, TimestampMixin, Base):
    __tablename__ = 'user_identity'
    __table_args__ = (UniqueConstraint('identity_type', 'identity_key', name='uq_user_identity_type_key'),)

    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), index=True)
    identity_type: Mapped[str] = mapped_column(String(32), index=True)
    identity_key: Mapped[str] = mapped_column(String(128), index=True)
    credential_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    extra_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class UserSession(IDMixin, TimestampMixin, Base):
    __tablename__ = 'user_session'

    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), index=True)
    scene: Mapped[str] = mapped_column(String(16), index=True)
    refresh_token: Mapped[str] = mapped_column(Text)
    client_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)


class UserDevice(IDMixin, TimestampMixin, Base):
    __tablename__ = 'user_device'
    __table_args__ = (UniqueConstraint('user_id', 'device_id', name='uq_user_device_user_device'),)

    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), index=True)
    device_id: Mapped[str] = mapped_column(String(128), index=True)
    platform: Mapped[str] = mapped_column(String(32))
    app_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    push_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
