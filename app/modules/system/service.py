from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.infra.security.token import Principal
from app.modules.audit.service import service as audit_service
from app.modules.system.models import SystemDict, SystemSetting
from app.modules.system.schemas import DictCreate, DictUpdate, SettingCreate, SettingUpdate
from app.utils.crud import normalize_text


class SystemService:
    async def list_settings(self, session: AsyncSession) -> list[dict]:
        rows = list((await session.scalars(select(SystemSetting).order_by(SystemSetting.id.asc()))).all())
        return [self.serialize_setting(item) for item in rows]

    def serialize_setting(self, item: SystemSetting) -> dict:
        return {
            'id': item.id,
            'key': item.config_key,
            'value': item.config_value,
            'remark': item.remark,
        }

    async def create_setting(self, session: AsyncSession, payload: SettingCreate, current_user: Principal) -> dict:
        exists = await session.scalar(select(SystemSetting).where(SystemSetting.config_key == payload.key.strip()))
        if exists is not None:
            raise AppException('设置 Key 已存在', status_code=400)
        item = SystemSetting(config_key=payload.key.strip(), config_value=payload.value, remark=normalize_text(payload.remark))
        session.add(item)
        await session.flush()
        await audit_service.log_operation(session, module='system', action='create_setting', path='/api/admin/v1/system/settings', user_id=current_user.user_id, detail=item.config_key)
        await session.commit()
        return self.serialize_setting(item)

    async def update_setting(self, session: AsyncSession, setting_id: int, payload: SettingUpdate, current_user: Principal) -> dict:
        item = await session.get(SystemSetting, setting_id)
        if item is None:
            raise AppException('设置不存在', status_code=404)
        exists = await session.scalar(select(SystemSetting).where(SystemSetting.config_key == payload.key.strip(), SystemSetting.id != setting_id))
        if exists is not None:
            raise AppException('设置 Key 已存在', status_code=400)
        item.config_key = payload.key.strip()
        item.config_value = payload.value
        item.remark = normalize_text(payload.remark)
        await audit_service.log_operation(session, module='system', action='update_setting', path=f'/api/admin/v1/system/settings/{setting_id}', user_id=current_user.user_id, detail=item.config_key)
        await session.commit()
        return self.serialize_setting(item)

    async def delete_setting(self, session: AsyncSession, setting_id: int, current_user: Principal) -> dict:
        item = await session.get(SystemSetting, setting_id)
        if item is None:
            raise AppException('设置不存在', status_code=404)
        key = item.config_key
        await session.delete(item)
        await audit_service.log_operation(session, module='system', action='delete_setting', path=f'/api/admin/v1/system/settings/{setting_id}', user_id=current_user.user_id, detail=key)
        await session.commit()
        return {'id': setting_id}

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
