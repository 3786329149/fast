from __future__ import annotations
import json

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.iam.models import User, UserIdentity, UserProfile, UserSession


class IAMRepository:
    """预留统一账号仓储层。"""

    async def get_user_by_id(self, session: AsyncSession, user_id: int) -> User | None:
        return await session.get(User, user_id)

    async def get_user_for_account(self, session: AsyncSession, account: str) -> User | None:
        stmt = select(User).where(or_(User.username == account, User.mobile == account, User.email == account))
        return await session.scalar(stmt)

    async def get_user_by_mobile(self, session: AsyncSession, mobile: str) -> User | None:
        stmt = select(User).where(User.mobile == mobile)
        return await session.scalar(stmt)

    async def get_identity(
            self,
            session: AsyncSession,
            *,
            identity_type: str,
            identity_key: str,
    ) -> UserIdentity | None:
        stmt = select(UserIdentity).where(
            UserIdentity.identity_type == identity_type,
            UserIdentity.identity_key == identity_key,
        )
        return await session.scalar(stmt)

    async def list_identities_by_user(
            self,
            session: AsyncSession,
            *,
            user_id: int,
            identity_type: str | None = None,
    ) -> list[UserIdentity]:
        stmt = select(UserIdentity).where(UserIdentity.user_id == user_id)
        if identity_type:
            stmt = stmt.where(UserIdentity.identity_type == identity_type)
        return list((await session.scalars(stmt)).all())

    async def get_profile(self, session: AsyncSession, *, user_id: int) -> UserProfile | None:
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        return await session.scalar(stmt)

    async def create_user(
            self,
            session: AsyncSession,
            *,
            username: str,
            mobile: str | None = None,
            email: str | None = None,
            is_admin: bool = False,
    ) -> User:
        user = User(username=username, mobile=mobile, email=email, is_admin=is_admin, status=1)
        session.add(user)
        await session.flush()
        return user

    async def ensure_profile(self, session: AsyncSession, *, user_id: int, nickname: str | None = None) -> UserProfile:
        profile = await self.get_profile(session, user_id=user_id)
        if profile is None:
            profile = UserProfile(user_id=user_id, nickname=nickname)
            session.add(profile)
            await session.flush()
        elif nickname and not profile.nickname:
            profile.nickname = nickname
        return profile

    async def upsert_identity(
            self,
            session: AsyncSession,
            *,
            user_id: int,
            identity_type: str,
            identity_key: str,
            credential_hash: str | None = None,
            is_verified: bool = True,
            extra: dict | None = None,
    ) -> UserIdentity:
        identity = await self.get_identity(
            session,
            identity_type=identity_type,
            identity_key=identity_key,
        )
        extra_json = json.dumps(extra, ensure_ascii=False) if extra else None
        if identity is None:
            identity = UserIdentity(
                user_id=user_id,
                identity_type=identity_type,
                identity_key=identity_key,
                credential_hash=credential_hash,
                is_verified=is_verified,
                extra_json=extra_json,
            )
            session.add(identity)
            await session.flush()
            return identity

        identity.user_id = user_id
        identity.credential_hash = credential_hash or identity.credential_hash
        identity.is_verified = is_verified
        identity.extra_json = extra_json or identity.extra_json
        return identity

    async def create_user_session(
            self,
            session: AsyncSession,
            *,
            user_id: int,
            scene: str,
            refresh_token: str,
            client_ip: str | None = None,
            user_agent: str | None = None,
    ) -> UserSession:
        user_session = UserSession(
            user_id=user_id,
            scene=scene,
            refresh_token=refresh_token,
            client_ip=client_ip,
            user_agent=user_agent,
        )
        session.add(user_session)
        await session.flush()
        return user_session


repository = IAMRepository()
