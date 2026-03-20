from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.security import Principal
from app.modules.audit.service import service as audit_service
from app.modules.system.models import SystemConfig, SystemDict
from app.modules.system.schemas import ConfigCreate, ConfigUpdate, DictCreate, DictUpdate
from app.utils.crud import normalize_text


class SystemService:
    async def list_configs(self, session: AsyncSession) -> list[dict]:
        rows = list((await session.scalars(select(SystemConfig).order_by(SystemConfig.id.asc()))).all())
        return [self.serialize_config(item) for item in rows]

    def serialize_config(self, item: SystemConfig) -> dict:
        return {
            'id': item.id,
            'key': item.config_key,
            'value': item.config_value,
            'remark': item.remark,
        }

    async def create_config(self, session: AsyncSession, payload: ConfigCreate, current_user: Principal) -> dict:
        exists = await session.scalar(select(SystemConfig).where(SystemConfig.config_key == payload.key.strip()))
        if exists is not None:
            raise AppException('配置 Key 已存在', status_code=400)
        item = SystemConfig(config_key=payload.key.strip(), config_value=payload.value, remark=normalize_text(payload.remark))
        session.add(item)
        await session.flush()
        await audit_service.log_operation(session, module='system', action='create_config', path='/api/admin/v1/system/configs', user_id=current_user.user_id, detail=item.config_key)
        await session.commit()
        return self.serialize_config(item)

    async def update_config(self, session: AsyncSession, config_id: int, payload: ConfigUpdate, current_user: Principal) -> dict:
        item = await session.get(SystemConfig, config_id)
        if item is None:
            raise AppException('配置不存在', status_code=404)
        exists = await session.scalar(select(SystemConfig).where(SystemConfig.config_key == payload.key.strip(), SystemConfig.id != config_id))
        if exists is not None:
            raise AppException('配置 Key 已存在', status_code=400)
        item.config_key = payload.key.strip()
        item.config_value = payload.value
        item.remark = normalize_text(payload.remark)
        await audit_service.log_operation(session, module='system', action='update_config', path=f'/api/admin/v1/system/configs/{config_id}', user_id=current_user.user_id, detail=item.config_key)
        await session.commit()
        return self.serialize_config(item)

    async def delete_config(self, session: AsyncSession, config_id: int, current_user: Principal) -> dict:
        item = await session.get(SystemConfig, config_id)
        if item is None:
            raise AppException('配置不存在', status_code=404)
        key = item.config_key
        await session.delete(item)
        await audit_service.log_operation(session, module='system', action='delete_config', path=f'/api/admin/v1/system/configs/{config_id}', user_id=current_user.user_id, detail=key)
        await session.commit()
        return {'id': config_id}

    async def list_dicts(self, session: AsyncSession) -> list[dict]:
        rows = list((await session.scalars(select(SystemDict).order_by(SystemDict.dict_type.asc(), SystemDict.sort.asc(), SystemDict.id.asc()))).all())
        return [self.serialize_dict(item) for item in rows]

    def serialize_dict(self, item: SystemDict) -> dict:
        return {
            'id': item.id,
            'type': item.dict_type,
            'label': item.dict_label,
            'value': item.dict_value,
            'sort': item.sort,
        }

    async def create_dict(self, session: AsyncSession, payload: DictCreate, current_user: Principal) -> dict:
        item = SystemDict(dict_type=payload.type.strip(), dict_label=payload.label.strip(), dict_value=payload.value.strip(), sort=payload.sort)
        session.add(item)
        await session.flush()
        await audit_service.log_operation(session, module='system', action='create_dict', path='/api/admin/v1/system/dicts', user_id=current_user.user_id, detail=f'{item.dict_type}:{item.dict_value}')
        await session.commit()
        return self.serialize_dict(item)

    async def update_dict(self, session: AsyncSession, dict_id: int, payload: DictUpdate, current_user: Principal) -> dict:
        item = await session.get(SystemDict, dict_id)
        if item is None:
            raise AppException('字典项不存在', status_code=404)
        item.dict_type = payload.type.strip()
        item.dict_label = payload.label.strip()
        item.dict_value = payload.value.strip()
        item.sort = payload.sort
        await audit_service.log_operation(session, module='system', action='update_dict', path=f'/api/admin/v1/system/dicts/{dict_id}', user_id=current_user.user_id, detail=f'{item.dict_type}:{item.dict_value}')
        await session.commit()
        return self.serialize_dict(item)

    async def delete_dict(self, session: AsyncSession, dict_id: int, current_user: Principal) -> dict:
        item = await session.get(SystemDict, dict_id)
        if item is None:
            raise AppException('字典项不存在', status_code=404)
        detail = f'{item.dict_type}:{item.dict_value}'
        await session.delete(item)
        await audit_service.log_operation(session, module='system', action='delete_dict', path=f'/api/admin/v1/system/dicts/{dict_id}', user_id=current_user.user_id, detail=detail)
        await session.commit()
        return {'id': dict_id}


service = SystemService()
