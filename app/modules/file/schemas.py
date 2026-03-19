from __future__ import annotations

from pydantic import BaseModel, Field


class UploadTokenRequest(BaseModel):
    file_name: str
    content_type: str


class UploadTokenResponse(BaseModel):
    provider: str
    upload_url: str
    object_key: str
    content_type: str | None = None

class FileAssetBase(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    object_key: str = Field(min_length=1, max_length=255)
    storage_provider: str = 'mock'
    bucket: str | None = Field(default=None, max_length=128)
    mime_type: str | None = Field(default=None, max_length=128)
    file_size: int | None = Field(default=None, ge=0)
    file_url: str | None = None


class FileAssetCreate(FileAssetBase):
    pass


class FileAssetUpdate(FileAssetBase):
    pass


class FileAssetOut(FileAssetBase):
    id: int
    file_ext: str | None = None
    created_at: str | None = None