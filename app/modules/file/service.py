from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.security import Principal
from app.modules.audit.service import service as audit_service
from app.modules.file.models import FileAsset
from app.modules.file.schemas import FileAssetCreate, FileAssetUpdate
from app.utils.crud import dt_to_iso, normalize_text


class FileService:
    def create_upload_token(self, file_name: str, content_type: str) -> dict:
        object_key = f'uploads/{uuid4().hex}/{file_name}'
        return {
            'provider': 'mock',
            'upload_url': f'https://storage.example.com/{object_key}',
            'object_key': object_key,
            'content_type': content_type,
        }

    async def list_assets(self, session: AsyncSession) -> list[dict]:
        rows = list((await session.scalars(select(FileAsset).order_by(FileAsset.created_at.desc(), FileAsset.id.desc()))).all())
        return [self.serialize_asset(item) for item in rows]

    def serialize_asset(self, item: FileAsset) -> dict:
        return {
            'id': item.id,
            'file_name': item.file_name,
            'object_key': item.object_key,
            'storage_provider': item.storage_provider,
            'bucket': item.bucket,
            'mime_type': item.mime_type,
            'file_size': item.file_size,
            'file_url': item.file_url,
            'file_ext': item.file_ext,
            'created_at': dt_to_iso(item.created_at),
        }

    async def create_asset(self, session: AsyncSession, payload: FileAssetCreate, current_user: Principal) -> dict:
        item = FileAsset(
            storage_provider=payload.storage_provider,
            bucket=normalize_text(payload.bucket),
            object_key=payload.object_key.strip(),
            file_name=payload.file_name.strip(),
            file_ext=Path(payload.file_name).suffix.lstrip('.') or None,
            mime_type=normalize_text(payload.mime_type),
            file_size=payload.file_size,
            file_url=normalize_text(payload.file_url),
        )
        session.add(item)
        await session.flush()
        await audit_service.log_operation(session, module='file', action='create_asset',
                                          path='/api/admin/v1/files/assets', user_id=current_user.user_id,
                                          detail=item.file_name)
        await session.commit()
        return self.serialize_asset(item)

    async def update_asset(self, session: AsyncSession, asset_id: int, payload: FileAssetUpdate,
                           current_user: Principal) -> dict:
        item = await session.get(FileAsset, asset_id)
        if item is None:
            raise AppException('文件不存在', status_code=404)
        item.storage_provider = payload.storage_provider
        item.bucket = normalize_text(payload.bucket)
        item.object_key = payload.object_key.strip()
        item.file_name = payload.file_name.strip()
        item.file_ext = Path(payload.file_name).suffix.lstrip('.') or None
        item.mime_type = normalize_text(payload.mime_type)
        item.file_size = payload.file_size
        item.file_url = normalize_text(payload.file_url)
        await audit_service.log_operation(session, module='file', action='update_asset',
                                          path=f'/api/admin/v1/files/assets/{asset_id}', user_id=current_user.user_id,
                                          detail=item.file_name)
        await session.commit()
        return self.serialize_asset(item)

    async def delete_asset(self, session: AsyncSession, asset_id: int, current_user: Principal) -> dict:
        item = await session.get(FileAsset, asset_id)
        if item is None:
            raise AppException('文件不存在', status_code=404)
        name = item.file_name
        await session.delete(item)
        await audit_service.log_operation(session, module='file', action='delete_asset',
                                          path=f'/api/admin/v1/files/assets/{asset_id}', user_id=current_user.user_id,
                                          detail=name)
        await session.commit()
        return {'id': asset_id}

service = FileService()
