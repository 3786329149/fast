from __future__ import annotations

import json
import time
from dataclasses import dataclass
from uuid import uuid4

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_config
from app.core.constants import QR_LOGIN_TICKET_EXPIRE_SECONDS
from app.core.enums import TokenScene
from app.core.exceptions import AppException
from app.infra.cache import redis as redis_store
from app.infra.integrations.wechat.client import WeChatApiError, client as wechat_client
from app.infra.security.token import (
    Principal,
    decode_token,
    get_password_hash,
    issue_token_pair,
    verify_password,
)
from app.modules.iam.repository import repository

_PENDING_CACHE: dict[str, dict] = {}
_QR_CACHE: dict[str, dict] = {}


@dataclass(slots=True)
class LoginResult:
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    profile: dict

    def to_dict(self) -> dict:
        return {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'token_type': self.token_type,
            'expires_in': self.expires_in,
            'profile': self.profile,
        }


class IAMService:
    def _build_principal(self, *, user_id: int, username: str, scene: TokenScene, is_admin: bool = False) -> Principal:
        if scene == TokenScene.ADMIN or is_admin:
            return Principal(
                user_id=user_id,
                username=username,
                scene=TokenScene.ADMIN,
                org_id=1,
                dept_id=10,
                roles=['super_admin'],
                permissions=[
                    '*',
                    'mall:product:list',
                    'mall:product:create',
                    'mall:order:list',
                    'org:department:list',
                    'rbac:role:list',
                    'system:setting:list',
                ],
            )
        return Principal(
            user_id=user_id,
            username=username,
            scene=TokenScene.CLIENT,
            org_id=1,
            dept_id=None,
            roles=['member'],
            permissions=[],
        )

    def _issue_result(self, principal: Principal) -> LoginResult:
        pair = issue_token_pair(principal)
        return LoginResult(
            access_token=pair.access_token,
            refresh_token=pair.refresh_token,
            token_type=pair.token_type,
            expires_in=pair.expires_in,
            profile={
                'user_id': principal.user_id,
                'username': principal.username,
                'scene': principal.scene,
                'roles': principal.roles,
                'permissions': principal.permissions,
            },
        )

    async def _set_cache(self, namespace: str, key: str, payload: dict, expire_seconds: int) -> None:
        record = {'data': payload, 'expires_at': int(time.time()) + expire_seconds}
        raw = json.dumps(record, ensure_ascii=False)
        cache_key = f'{namespace}:{key}'
        try:
            if redis_store.redis_client is not None:
                await redis_store.redis_client.setex(cache_key, expire_seconds, raw)
                return
        except Exception:
            pass
        if namespace == 'pending_bind':
            _PENDING_CACHE[key] = record
        else:
            _QR_CACHE[key] = record

    async def _get_cache(self, namespace: str, key: str) -> dict | None:
        cache_key = f'{namespace}:{key}'
        record: dict | None = None
        try:
            if redis_store.redis_client is not None:
                raw = await redis_store.redis_client.get(cache_key)
                if raw:
                    record = json.loads(raw)
        except Exception:
            record = None

        if record is None:
            memory = _PENDING_CACHE if namespace == 'pending_bind' else _QR_CACHE
            record = memory.get(key)

        if record is None:
            return None
        if int(record.get('expires_at', 0)) < int(time.time()):
            await self._delete_cache(namespace, key)
            return None
        return record.get('data')

    async def _delete_cache(self, namespace: str, key: str) -> None:
        cache_key = f'{namespace}:{key}'
        try:
            if redis_store.redis_client is not None:
                await redis_store.redis_client.delete(cache_key)
        except Exception:
            pass
        memory = _PENDING_CACHE if namespace == 'pending_bind' else _QR_CACHE
        memory.pop(key, None)

    async def admin_login(self, session: AsyncSession, account: str, password: str) -> LoginResult:
        user = await repository.get_user_for_account(session, account)
        if user is None or not user.is_admin:
            raise AppException('账号或密码错误', status_code=status.HTTP_401_UNAUTHORIZED)

        password_identity = await repository.get_identity(
            session,
            identity_type='password',
            identity_key=account,
        )
        if password_identity is None:
            password_identity = await repository.get_identity(
                session,
                identity_type='password',
                identity_key=user.username,
            )

        if password_identity is None or not password_identity.credential_hash:
            raise AppException('账号或密码错误', status_code=status.HTTP_401_UNAUTHORIZED)
        if not verify_password(password, password_identity.credential_hash):
            raise AppException('账号或密码错误', status_code=status.HTTP_401_UNAUTHORIZED)

        principal = self._build_principal(user_id=user.id, username=user.username, scene=TokenScene.ADMIN, is_admin=True)
        result = self._issue_result(principal)
        await repository.create_user_session(
            session,
            user_id=user.id,
            scene=TokenScene.ADMIN.value,
            refresh_token=result.refresh_token,
        )
        await session.commit()
        return result

    def refresh_token(self, refresh_token: str, *, expected_scene: TokenScene) -> LoginResult:
        try:
            payload = decode_token(refresh_token)
        except ValueError as exc:
            raise AppException('刷新令牌无效', status_code=status.HTTP_401_UNAUTHORIZED) from exc
        if payload.token_type != 'refresh':
            raise AppException('刷新令牌无效', status_code=status.HTTP_401_UNAUTHORIZED)
        if payload.scene != expected_scene:
            raise AppException('令牌场景不匹配', status_code=status.HTTP_403_FORBIDDEN)
        principal = Principal(
            user_id=int(payload.sub),
            username=payload.username,
            scene=payload.scene,
            org_id=payload.org_id,
            dept_id=payload.dept_id,
            roles=payload.roles,
            permissions=payload.permissions,
        )
        return self._issue_result(principal)

    async def login_by_code(self, session: AsyncSession, phone: str, code: str) -> LoginResult:
        self._ensure_sms_code(code)
        user = await repository.get_user_by_mobile(session, phone)
        if user is None:
            user = await repository.create_user(session, username=phone, mobile=phone)
            await repository.ensure_profile(session, user_id=user.id, nickname=f'用户{phone[-4:]}')
        await repository.upsert_identity(
            session,
            user_id=user.id,
            identity_type='mobile_code',
            identity_key=phone,
            is_verified=True,
        )
        principal = self._build_principal(user_id=user.id, username=user.username, scene=TokenScene.CLIENT)
        result = self._issue_result(principal)
        await repository.create_user_session(
            session,
            user_id=user.id,
            scene=TokenScene.CLIENT.value,
            refresh_token=result.refresh_token,
        )
        await session.commit()
        return result

    async def login_by_password(self, session: AsyncSession, account: str, password: str) -> LoginResult:
        user = await repository.get_user_for_account(session, account)
        password_identity = await repository.get_identity(
            session,
            identity_type='password',
            identity_key=account,
        )

        if user is None and password_identity is None and get_config().IS_LOCAL_ENV:
            username = account
            user = await repository.create_user(session, username=username, mobile=account if account.isdigit() else None)
            await repository.ensure_profile(session, user_id=user.id, nickname=username)
            password_identity = await repository.upsert_identity(
                session,
                user_id=user.id,
                identity_type='password',
                identity_key=account,
                credential_hash=get_password_hash(password),
                is_verified=True,
            )

        if password_identity is None and user is not None:
            password_identity = await repository.get_identity(
                session,
                identity_type='password',
                identity_key=user.username,
            )

        if user is None or password_identity is None or not password_identity.credential_hash:
            raise AppException('账号或密码错误', status_code=status.HTTP_401_UNAUTHORIZED)

        if not verify_password(password, password_identity.credential_hash):
            raise AppException('账号或密码错误', status_code=status.HTTP_401_UNAUTHORIZED)

        principal = self._build_principal(user_id=user.id, username=user.username, scene=TokenScene.CLIENT)
        result = self._issue_result(principal)
        await repository.create_user_session(
            session,
            user_id=user.id,
            scene=TokenScene.CLIENT.value,
            refresh_token=result.refresh_token,
        )
        await session.commit()
        return result

    async def wechat_login(self, session: AsyncSession, code: str) -> dict:
        try:
            data = await wechat_client.code_to_session(code)
        except WeChatApiError as exc:
            raise AppException(str(exc), status_code=status.HTTP_502_BAD_GATEWAY) from exc

        identity_key = data.get('unionid') or data.get('openid')
        if not identity_key:
            raise AppException('微信登录返回缺少 openid/unionid', status_code=status.HTTP_400_BAD_REQUEST)

        identity = await repository.get_identity(
            session,
            identity_type='wechat_miniapp',
            identity_key=identity_key,
        )
        if identity is not None:
            user = await repository.get_user_by_id(session, identity.user_id)
            if user is None:
                raise AppException('用户不存在', status_code=status.HTTP_404_NOT_FOUND)
            result = self._issue_result(
                self._build_principal(user_id=user.id, username=user.username, scene=TokenScene.CLIENT)
            )
            await repository.create_user_session(
                session,
                user_id=user.id,
                scene=TokenScene.CLIENT.value,
                refresh_token=result.refresh_token,
            )
            await session.commit()
            return {
                'need_bind_mobile': False,
                'wechat_openid': data.get('openid'),
                'wechat_unionid': data.get('unionid'),
                'login_result': result.to_dict(),
            }

        union_token = uuid4().hex
        await self._set_cache(
            'pending_bind',
            union_token,
            {
                'openid': data.get('openid'),
                'unionid': data.get('unionid'),
                'session_key': data.get('session_key'),
            },
            QR_LOGIN_TICKET_EXPIRE_SECONDS,
        )
        return {
            'wechat_openid': data.get('openid'),
            'wechat_unionid': data.get('unionid'),
            'union_token': union_token,
            'need_bind_mobile': True,
            'expires_in': QR_LOGIN_TICKET_EXPIRE_SECONDS,
        }

    async def bind_mobile(
        self,
        session: AsyncSession,
        *,
        phone: str | None,
        code: str | None,
        union_token: str | None,
        phone_code: str | None = None,
    ) -> LoginResult:
        pending = None
        if union_token:
            pending = await self._get_cache('pending_bind', union_token)
            if pending is None:
                raise AppException('微信绑定票据已失效，请重新登录', status_code=status.HTTP_400_BAD_REQUEST)

        if phone_code:
            try:
                phone_resp = await wechat_client.get_user_phone_number(phone_code)
            except WeChatApiError as exc:
                raise AppException(str(exc), status_code=status.HTTP_502_BAD_GATEWAY) from exc
            phone_info = phone_resp.get('phone_info') or {}
            phone = phone_info.get('purePhoneNumber') or phone_info.get('phoneNumber')
            if not phone:
                raise AppException('微信手机号换取失败', status_code=status.HTTP_400_BAD_REQUEST)
        else:
            if not phone or not code:
                raise AppException('缺少手机号绑定参数', status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
            self._ensure_sms_code(code)

        user = await repository.get_user_by_mobile(session, phone)
        if user is None:
            user = await repository.create_user(session, username=phone, mobile=phone)
            await repository.ensure_profile(session, user_id=user.id, nickname=f'用户{phone[-4:]}')

        await repository.upsert_identity(
            session,
            user_id=user.id,
            identity_type='mobile_code',
            identity_key=phone,
            is_verified=True,
        )

        if pending is not None:
            await repository.upsert_identity(
                session,
                user_id=user.id,
                identity_type='wechat_miniapp',
                identity_key=pending.get('unionid') or pending.get('openid'),
                is_verified=True,
                extra={
                    'openid': pending.get('openid'),
                    'unionid': pending.get('unionid'),
                    'session_key': pending.get('session_key'),
                },
            )
            await self._delete_cache('pending_bind', union_token or '')

        principal = self._build_principal(user_id=user.id, username=user.username, scene=TokenScene.CLIENT)
        result = self._issue_result(principal)
        await repository.create_user_session(
            session,
            user_id=user.id,
            scene=TokenScene.CLIENT.value,
            refresh_token=result.refresh_token,
        )
        await session.commit()
        return result

    async def bind_wechat(self, session: AsyncSession, *, current_user: Principal, union_token: str | None, openid: str | None) -> dict:
        pending = await self._get_cache('pending_bind', union_token) if union_token else None
        if pending is None and not openid:
            raise AppException('缺少可绑定的微信凭证', status_code=status.HTTP_400_BAD_REQUEST)

        identity_key = (pending or {}).get('unionid') or openid or (pending or {}).get('openid')
        await repository.upsert_identity(
            session,
            user_id=current_user.user_id,
            identity_type='wechat_miniapp',
            identity_key=identity_key,
            is_verified=True,
            extra=pending or {'openid': openid},
        )
        await session.commit()
        if union_token:
            await self._delete_cache('pending_bind', union_token)
        return {'bound': True, 'identity_key': identity_key}

    async def create_qr_ticket(self, scene: str = 'web_login') -> dict:
        ticket = uuid4().hex
        payload = {
            'ticket': ticket,
            'scene': scene,
            'status': 'pending',
            'scanned_by': None,
            'confirmed_by': None,
        }
        await self._set_cache('qr', ticket, payload, QR_LOGIN_TICKET_EXPIRE_SECONDS)
        return {
            'ticket': ticket,
            'qr_content': f'miniapp://login?ticket={ticket}',
            'status': 'pending',
            'expires_in': QR_LOGIN_TICKET_EXPIRE_SECONDS,
        }

    async def get_qr_status(self, ticket: str) -> dict:
        data = await self._get_cache('qr', ticket)
        if data is None:
            return {'ticket': ticket, 'status': 'expired'}
        return data

    async def scan_qr_ticket(self, ticket: str, *, user_id: int) -> dict:
        data = await self._get_cache('qr', ticket)
        if data is None:
            raise AppException('扫码票据不存在或已过期', status_code=status.HTTP_404_NOT_FOUND)
        data['status'] = 'scanned'
        data['scanned_by'] = user_id
        await self._set_cache('qr', ticket, data, QR_LOGIN_TICKET_EXPIRE_SECONDS)
        return data

    async def confirm_qr_ticket(self, ticket: str, *, user_id: int) -> dict:
        data = await self._get_cache('qr', ticket)
        if data is None:
            raise AppException('扫码票据不存在或已过期', status_code=status.HTTP_404_NOT_FOUND)
        if data.get('scanned_by') not in (None, user_id):
            raise AppException('当前用户不能确认此扫码登录', status_code=status.HTTP_403_FORBIDDEN)
        data['status'] = 'confirmed'
        data['confirmed_by'] = user_id
        principal = self._build_principal(user_id=user_id, username=f'user_{user_id}', scene=TokenScene.CLIENT)
        pair = issue_token_pair(principal)
        data['access_token'] = pair.access_token
        data['refresh_token'] = pair.refresh_token
        await self._set_cache('qr', ticket, data, QR_LOGIN_TICKET_EXPIRE_SECONDS)
        return data

    @staticmethod
    def _ensure_sms_code(code: str) -> None:
        if len(code) < 4:
            raise AppException('验证码格式错误', status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


service = IAMService()
