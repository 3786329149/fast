from __future__ import annotations

from pydantic import BaseModel, Field


class SettingBase(BaseModel):
    key: str = Field(min_length=1, max_length=128)
    value: str = ''
    remark: str | None = None


class SettingCreate(SettingBase):
    pass


class SettingUpdate(SettingBase):
    pass


class SettingOut(SettingBase):
    id: int


class DictBase(BaseModel):
    type: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=64)
    value: str = Field(min_length=1, max_length=64)
    sort: int = 0


class DictCreate(DictBase):
    pass


class DictUpdate(DictBase):
    pass


class DictOut(DictBase):
    id: int
