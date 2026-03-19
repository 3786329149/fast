from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class AdminLoginRequest(BaseModel):
    account: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)


class SendCodeRequest(BaseModel):
    phone: str = Field(..., min_length=11, max_length=20)
    scene: str = 'login'


class LoginByCodeRequest(BaseModel):
    phone: str
    code: str


class LoginByPasswordRequest(BaseModel):
    account: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str

class BindWechatRequest(BaseModel):
    union_token: str | None = None
    openid: str | None = None


class WechatMiniLoginRequest(BaseModel):
    code: str
    inviter_id: int | None = None


class BindMobileRequest(BaseModel):
    phone: str | None = None
    code: str | None = None
    union_token: str | None = None
    phone_code: str | None = None

    @model_validator(mode='after')
    def validate_binding_mode(self) -> 'BindMobileRequest':
        if self.phone_code:
            return self
        if self.phone and self.code:
            return self
        raise ValueError('需要提供 phone_code，或同时提供 phone 和 code')

class QrLoginCreateRequest(BaseModel):
    scene: str = 'web_login'


class QrLoginConfirmRequest(BaseModel):
    ticket: str


class QrLoginScanRequest(BaseModel):
    ticket: str


class UserProfileResponse(BaseModel):
    user_id: int
    username: str
    scene: str
    roles: list[str] = []
    permissions: list[str] = []
