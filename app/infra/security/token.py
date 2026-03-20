from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

from app.config import get_config
from app.core.constants import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_MINUTES
from app.core.enums import TokenScene

ALGORITHM = 'HS256'
pwd_context = CryptContext(schemes=['pbkdf2_sha256'], deprecated='auto')


class TokenPayload(BaseModel):
    sub: str
    scene: TokenScene
    username: str
    org_id: int | None = None
    dept_id: int | None = None
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    token_type: Literal['access', 'refresh'] = 'access'
    exp: int


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60


class Principal(BaseModel):
    user_id: int
    username: str
    scene: TokenScene
    org_id: int | None = None
    dept_id: int | None = None
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def _encode_token(payload: dict, expires_minutes: int) -> str:
    config = get_config()
    expire_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload.update({'exp': int(expire_at.timestamp())})
    return jwt.encode(payload, config.APP_SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(principal: Principal) -> str:
    payload = principal.model_dump()
    payload['sub'] = str(principal.user_id)
    payload['token_type'] = 'access'
    return _encode_token(payload, ACCESS_TOKEN_EXPIRE_MINUTES)


def create_refresh_token(principal: Principal) -> str:
    payload = principal.model_dump()
    payload['sub'] = str(principal.user_id)
    payload['token_type'] = 'refresh'
    return _encode_token(payload, REFRESH_TOKEN_EXPIRE_MINUTES)


def issue_token_pair(principal: Principal) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(principal),
        refresh_token=create_refresh_token(principal),
    )


def decode_token(token: str) -> TokenPayload:
    config = get_config()
    try:
        data = jwt.decode(token, config.APP_SECRET_KEY, algorithms=[ALGORITHM])
        return TokenPayload(**data)
    except JWTError as exc:
        raise ValueError('invalid token') from exc
