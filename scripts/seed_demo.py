from __future__ import annotations

import asyncio
import json
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import ProgrammingError

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.modules.iam.models import User, UserIdentity, UserProfile
from app.modules.mall.models import MallCategory, MallOrder, MallSku, MallSpu
from app.modules.org.models import EmployeeProfile, OrgCompany, OrgDepartment
from app.modules.rbac.models import AdminRole, AdminUserRole


async def get_or_create(session, model, defaults: dict | None = None, **filters):
    instance = await session.scalar(select(model).filter_by(**filters))
    if instance is not None:
        return instance, False
    params = {**filters, **(defaults or {})}
    instance = model(**params)
    session.add(instance)
    await session.flush()
    return instance, True


async def main() -> None:
    async with AsyncSessionLocal() as session:
        try:
            org, _ = await get_or_create(session, OrgCompany, name='演示企业', code='DEMO')
            dept, _ = await get_or_create(session, OrgDepartment, org_id=org.id, name='电商事业部', parent_id=None)

            admin_user, _ = await get_or_create(
                session,
                User,
                username='admin',
                defaults={'mobile': '13900000000', 'is_admin': True},
            )
            await get_or_create(session, UserProfile, user_id=admin_user.id, defaults={'nickname': '系统管理员'})
            await get_or_create(
                session,
                UserIdentity,
                identity_type='password',
                identity_key='admin',
                defaults={
                    'user_id': admin_user.id,
                    'credential_hash': get_password_hash('Admin@123456'),
                    'is_verified': True,
                },
            )
            admin_role, _ = await get_or_create(
                session,
                AdminRole,
                code='super_admin',
                defaults={'name': '超级管理员', 'data_scope': 'ALL'},
            )
            await get_or_create(session, AdminUserRole, user_id=admin_user.id, role_id=admin_role.id)
            await get_or_create(
                session,
                EmployeeProfile,
                user_id=admin_user.id,
                defaults={
                    'org_id': org.id,
                    'dept_id': dept.id,
                    'employee_no': 'EMP-ADMIN',
                    'job_title': '平台管理员',
                },
            )

            client_user, _ = await get_or_create(
                session,
                User,
                username='13800000000',
                defaults={'mobile': '13800000000', 'is_admin': False},
            )
            await get_or_create(session, UserProfile, user_id=client_user.id, defaults={'nickname': '演示用户'})
            await get_or_create(
                session,
                UserIdentity,
                identity_type='password',
                identity_key='13800000000',
                defaults={
                    'user_id': client_user.id,
                    'credential_hash': get_password_hash('User@123456'),
                    'is_verified': True,
                },
            )
            await get_or_create(
                session,
                UserIdentity,
                identity_type='mobile_code',
                identity_key='13800000000',
                defaults={'user_id': client_user.id, 'is_verified': True},
            )
            await get_or_create(
                session,
                UserIdentity,
                identity_type='wechat_miniapp',
                identity_key='union_demo_user',
                defaults={
                    'user_id': client_user.id,
                    'is_verified': True,
                    'extra_json': json.dumps({'openid': 'mini_demo_user', 'unionid': 'union_demo_user'}, ensure_ascii=False),
                },
            )

            category, _ = await get_or_create(
                session, MallCategory, name='默认分类', parent_id=None, defaults={'sort': 1}
            )
            spu, _ = await get_or_create(
                session,
                MallSpu,
                name='演示商品',
                category_id=category.id,
                defaults={'subtitle': '用于联调支付的演示商品', 'org_id': org.id},
            )
            sku, _ = await get_or_create(
                session,
                MallSku,
                sku_code='DEMO-SKU-001',
                defaults={
                    'spu_id': spu.id,
                    'spec_json': json.dumps({'颜色': '黑色', '容量': '标准版'}, ensure_ascii=False),
                    'sale_price': Decimal('99.00'),
                    'market_price': Decimal('129.00'),
                    'stock': 999,
                },
            )
            await get_or_create(
                session,
                MallOrder,
                order_no='DEMO202603180001',
                defaults={
                    'user_id': client_user.id,
                    'org_id': org.id,
                    'status': 'pending',
                    'pay_status': 'unpaid',
                    'refund_status': 'none',
                    'source_type': 'miniapp',
                    'total_amount': Decimal('99.00'),
                    'pay_amount': Decimal('99.00'),
                    'created_by': client_user.id,
                },
            )

            await session.commit()
        except ProgrammingError as exc:
            await session.rollback()
            if 'UndefinedTableError' in str(exc) or 'does not exist' in str(exc) or '不存在' in str(exc):
                raise SystemExit(
                    'Seed failed: PostgreSQL 已连接成功，但业务表不存在。请先执行 `alembic upgrade head` 初始化数据库。'
                ) from exc
            raise
        print('Seed completed.')
        print('Admin login: admin / Admin@123456')
        print('Client login: 13800000000 / User@123456 or SMS code mock')
        print('Demo order: DEMO202603180001')
        print('Mock miniapp openid: mini_demo_user')


if __name__ == '__main__':
    asyncio.run(main())
