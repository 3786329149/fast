from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.security import Principal
from app.modules.audit.service import service as audit_service
from app.modules.cms.models import CmsBanner, CmsNotice
from app.modules.cms.schemas import BannerCreate, BannerUpdate, NoticeCreate, NoticeUpdate
from app.utils.crud import active_to_int, dt_to_iso, int_to_active, normalize_text


class CMSService:
    async def list_banners(self, session: AsyncSession) -> list[dict]:
        rows = list((await session.scalars(select(CmsBanner).order_by(CmsBanner.sort.asc(), CmsBanner.id.asc()))).all())
        return [self.serialize_banner(item) for item in rows]

    def serialize_banner(self, item: CmsBanner) -> dict:
        return {
            'id': item.id,
            'title': item.title,
            'image_url': item.image_url,
            'link_url': item.link_url,
            'status': int_to_active(item.status),
            'sort': item.sort,
        }

    async def create_banner(self, session: AsyncSession, payload: BannerCreate, current_user: Principal) -> dict:
        item = CmsBanner(
            title=payload.title.strip(),
            image_url=payload.image_url.strip(),
            link_url=normalize_text(payload.link_url),
            sort=payload.sort,
            status=active_to_int(payload.status),
        )
        session.add(item)
        await session.flush()
        await audit_service.log_operation(session, module='cms', action='create_banner',
                                          path='/api/admin/v1/cms/banners', user_id=current_user.user_id,
                                          detail=item.title)
        await session.commit()
        return self.serialize_banner(item)

    async def update_banner(self, session: AsyncSession, banner_id: int, payload: BannerUpdate,
                            current_user: Principal) -> dict:
        item = await session.get(CmsBanner, banner_id)
        if item is None:
            raise AppException('Banner 不存在', status_code=404)
        item.title = payload.title.strip()
        item.image_url = payload.image_url.strip()
        item.link_url = normalize_text(payload.link_url)
        item.sort = payload.sort
        item.status = active_to_int(payload.status)
        await audit_service.log_operation(session, module='cms', action='update_banner',
                                          path=f'/api/admin/v1/cms/banners/{banner_id}', user_id=current_user.user_id,
                                          detail=item.title)
        await session.commit()
        return self.serialize_banner(item)

    async def delete_banner(self, session: AsyncSession, banner_id: int, current_user: Principal) -> dict:
        item = await session.get(CmsBanner, banner_id)
        if item is None:
            raise AppException('Banner 不存在', status_code=404)
        title = item.title
        await session.delete(item)
        await audit_service.log_operation(session, module='cms', action='delete_banner',
                                          path=f'/api/admin/v1/cms/banners/{banner_id}', user_id=current_user.user_id,
                                          detail=title)
        await session.commit()
        return {'id': banner_id}

    async def list_notices(self, session: AsyncSession) -> list[dict]:
        rows = list((await session.scalars(select(CmsNotice).order_by(CmsNotice.pinned.desc(), CmsNotice.id.desc()))).all())
        return [self.serialize_notice(item) for item in rows]

    def serialize_notice(self, item: CmsNotice) -> dict:
        return {
            'id': item.id,
            'title': item.title,
            'content': item.content,
            'status': int_to_active(item.status),
            'pinned': bool(item.pinned),
            'updated_at': dt_to_iso(item.updated_at),
        }

    async def create_notice(self, session: AsyncSession, payload: NoticeCreate, current_user: Principal) -> dict:
        item = CmsNotice(
            title=payload.title.strip(),
            content=payload.content.strip(),
            status=active_to_int(payload.status),
            pinned=payload.pinned,
        )
        session.add(item)
        await session.flush()
        await audit_service.log_operation(session, module='cms', action='create_notice', path='/api/admin/v1/cms/notices', user_id=current_user.user_id, detail=item.title)
        await session.commit()
        return self.serialize_notice(item)

    async def update_notice(self, session: AsyncSession, notice_id: int, payload: NoticeUpdate, current_user: Principal) -> dict:
        item = await session.get(CmsNotice, notice_id)
        if item is None:
            raise AppException('公告不存在', status_code=404)
        item.title = payload.title.strip()
        item.content = payload.content.strip()
        item.status = active_to_int(payload.status)
        item.pinned = payload.pinned
        await audit_service.log_operation(session, module='cms', action='update_notice', path=f'/api/admin/v1/cms/notices/{notice_id}', user_id=current_user.user_id, detail=item.title)
        await session.commit()
        return self.serialize_notice(item)

    async def delete_notice(self, session: AsyncSession, notice_id: int, current_user: Principal) -> dict:
        item = await session.get(CmsNotice, notice_id)
        if item is None:
            raise AppException('公告不存在', status_code=404)
        title = item.title
        await session.delete(item)
        await audit_service.log_operation(session, module='cms', action='delete_notice', path=f'/api/admin/v1/cms/notices/{notice_id}', user_id=current_user.user_id, detail=title)
        await session.commit()
        return {'id': notice_id}


service = CMSService()
