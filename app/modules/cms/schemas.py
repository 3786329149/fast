from __future__ import annotations

from pydantic import BaseModel, Field


class BannerBase(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    image_url: str = Field(min_length=1)
    link_url: str | None = None
    status: str = 'active'
    sort: int = 0

class BannerCreate(BannerBase):
    pass


class BannerUpdate(BannerBase):
    pass

class BannerOut(BaseModel):
    id: int


class NoticeBase(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    content: str = Field(min_length=1)
    status: str = 'active'
    pinned: bool = False
    updated_at: str | None = None

class NoticeCreate(NoticeBase):
    pass


class NoticeUpdate(NoticeBase):
    pass

class NoticeOut(BaseModel):
    id: int

