from __future__ import annotations

import asyncio
import json
import sys
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.infra.db.session import AsyncSessionLocal
from app.infra.security.token import get_password_hash
from app.modules.audit.models import OperationLog
from app.modules.cms.models import CmsBanner, CmsNotice
from app.modules.file.models import FileAsset
from app.modules.iam.models import User, UserIdentity, UserProfile
from app.modules.mall.models import MallCategory, MallOrder, MallSku, MallSpu
from app.modules.org.models import EmployeeProfile, OrgCompany, OrgDepartment
from app.modules.rbac.models import (
    AdminMenu,
    AdminPermission,
    AdminRole,
    AdminRolePermission,
    AdminUserRole,
)
from app.modules.system.models import SystemDict, SystemSetting


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
        org, _ = await get_or_create(session, OrgCompany, name='演示企业', code='DEMO', defaults={'status': 1})
        root_dept, _ = await get_or_create(
            session,
            OrgDepartment,
            org_id=org.id,
            name='总经办',
            parent_id=None,
            defaults={'code': 'HQ', 'status': 1, 'member_count': 1, 'tree_path': '/', 'description': '总部管理部门'},
        )
        ecommerce_dept, _ = await get_or_create(
            session,
            OrgDepartment,
            org_id=org.id,
            name='电商事业部',
            parent_id=root_dept.id,
            defaults={'code': 'ECOM', 'status': 1, 'member_count': 2, 'tree_path': f'/{root_dept.id}/', 'description': '商城与增长团队'},
        )

        admin_user, _ = await get_or_create(
            session,
            User,
            username='admin',
            defaults={'mobile': '13900000000', 'is_admin': True, 'status': 1},
        )
        await get_or_create(session, UserProfile, user_id=admin_user.id, defaults={'nickname': '系统管理员'})
        await get_or_create(
            session,
            UserIdentity,
            identity_type='password',
            identity_key='admin',
            defaults={'user_id': admin_user.id, 'credential_hash': get_password_hash('Admin@123456'), 'is_verified': True},
        )
        super_role, _ = await get_or_create(
            session,
            AdminRole,
            code='super_admin',
            defaults={'name': '超级管理员', 'data_scope': 'ALL', 'status': 1, 'description': '拥有所有后台权限'},
        )
        ops_role, _ = await get_or_create(
            session,
            AdminRole,
            code='ops_admin',
            defaults={'name': '运营管理员', 'data_scope': 'ORG_AND_CHILD', 'status': 1, 'description': '负责商城和内容运营'},
        )
        await get_or_create(session, AdminUserRole, user_id=admin_user.id, role_id=super_role.id)
        await get_or_create(
            session,
            EmployeeProfile,
            user_id=admin_user.id,
            defaults={
                'org_id': org.id,
                'dept_id': root_dept.id,
                'employee_no': 'EMP-ADMIN',
                'full_name': '系统管理员',
                'job_title': '平台管理员',
                'status': 1,
                'phone': '13900000000',
                'email': 'admin@example.com',
                'role_code': 'super_admin',
            },
        )

        permissions = [
            ('org:department:list', '查看部门', 'org'),
            ('org:department:create', '新建部门', 'org'),
            ('org:department:update', '编辑部门', 'org'),
            ('org:department:delete', '删除部门', 'org'),
            ('org:employee:list', '查看员工', 'org'),
            ('org:employee:create', '新建员工', 'org'),
            ('org:employee:update', '编辑员工', 'org'),
            ('org:employee:delete', '删除员工', 'org'),
            ('rbac:role:list', '查看角色', 'rbac'),
            ('rbac:role:create', '新建角色', 'rbac'),
            ('rbac:role:update', '编辑角色', 'rbac'),
            ('rbac:role:delete', '删除角色', 'rbac'),
            ('rbac:menu:list', '查看菜单', 'rbac'),
            ('rbac:menu:create', '新建菜单', 'rbac'),
            ('rbac:menu:update', '编辑菜单', 'rbac'),
            ('rbac:menu:delete', '删除菜单', 'rbac'),
            ('rbac:permission:list', '查看权限点', 'rbac'),
            ('rbac:permission:create', '新建权限点', 'rbac'),
            ('rbac:permission:update', '编辑权限点', 'rbac'),
            ('rbac:permission:delete', '删除权限点', 'rbac'),
            ('mall:product:list', '查看商品', 'mall'),
            ('mall:product:create', '新建商品', 'mall'),
            ('mall:product:update', '编辑商品', 'mall'),
            ('mall:product:delete', '删除商品', 'mall'),
            ('mall:order:list', '查看订单', 'mall'),
            ('mall:order:create', '新建订单', 'mall'),
            ('mall:order:update', '编辑订单', 'mall'),
            ('mall:order:delete', '删除订单', 'mall'),
            ('cms:banner:list', '查看 Banner', 'cms'),
            ('cms:banner:create', '新建 Banner', 'cms'),
            ('cms:banner:update', '编辑 Banner', 'cms'),
            ('cms:banner:delete', '删除 Banner', 'cms'),
            ('cms:notice:list', '查看公告', 'cms'),
            ('cms:notice:create', '新建公告', 'cms'),
            ('cms:notice:update', '编辑公告', 'cms'),
            ('cms:notice:delete', '删除公告', 'cms'),
            ('file:asset:list', '查看文件', 'file'),
            ('file:asset:create', '新建文件', 'file'),
            ('file:asset:update', '编辑文件', 'file'),
            ('file:asset:delete', '删除文件', 'file'),
            ('system:setting:list', '查看设置', 'system'),
            ('system:setting:create', '新建设置', 'system'),
            ('system:setting:update', '编辑设置', 'system'),
            ('system:setting:delete', '删除设置', 'system'),
            ('system:dict:list', '查看字典', 'system'),
            ('system:dict:create', '新建字典', 'system'),
            ('system:dict:update', '编辑字典', 'system'),
            ('system:dict:delete', '删除字典', 'system'),
            ('audit:log:list', '查看日志', 'audit'),
            ('audit:log:delete', '删除日志', 'audit'),
        ]
        permission_ids = []
        for code, name, group in permissions:
            permission, _ = await get_or_create(session, AdminPermission, code=code, defaults={'name': name, 'group_name': group})
            permission_ids.append(permission.id)
            await get_or_create(session, AdminRolePermission, role_id=super_role.id, permission_id=permission.id)
        for code in ['mall:product:list', 'mall:order:list', 'cms:banner:list', 'cms:notice:list']:
            permission = await session.scalar(select(AdminPermission).where(AdminPermission.code == code))
            if permission is not None:
                await get_or_create(session, AdminRolePermission, role_id=ops_role.id, permission_id=permission.id)

        await get_or_create(
            session,
            AdminMenu,
            name='组织管理',
            type='directory',
            defaults={'path': '/org', 'sort': 10, 'status': 1, 'icon': 'department'},
        )
        await get_or_create(
            session,
            AdminMenu,
            name='商品管理',
            type='menu',
            defaults={'path': '/mall/products', 'sort': 20, 'status': 1, 'icon': 'product', 'permission_code': 'mall:product:list'},
        )
        await get_or_create(
            session,
            AdminMenu,
            name='订单中心',
            type='menu',
            defaults={'path': '/mall/orders', 'sort': 30, 'status': 1, 'icon': 'order', 'permission_code': 'mall:order:list'},
        )

        client_user, _ = await get_or_create(
            session,
            User,
            username='13800000000',
            defaults={'mobile': '13800000000', 'is_admin': False, 'status': 1},
        )
        await get_or_create(session, UserProfile, user_id=client_user.id, defaults={'nickname': '演示用户'})
        await get_or_create(
            session,
            UserIdentity,
            identity_type='password',
            identity_key='13800000000',
            defaults={'user_id': client_user.id, 'credential_hash': get_password_hash('User@123456'), 'is_verified': True},
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
        await get_or_create(
            session,
            EmployeeProfile,
            user_id=client_user.id,
            defaults={
                'org_id': org.id,
                'dept_id': ecommerce_dept.id,
                'employee_no': 'EMP-0002',
                'full_name': '张三',
                'job_title': '运营经理',
                'status': 1,
                'phone': '13800000000',
                'email': 'ops@example.com',
                'role_code': 'ops_admin',
            },
        )

        category_gift, _ = await get_or_create(session, MallCategory, name='企业礼包', parent_id=None, defaults={'sort': 1, 'status': 1})
        category_service, _ = await get_or_create(session, MallCategory, name='数字服务', parent_id=None, defaults={'sort': 2, 'status': 1})
        gift_spu, _ = await get_or_create(
            session,
            MallSpu,
            name='企业联名礼盒',
            category_id=category_gift.id,
            defaults={'subtitle': '用于管理后台 CRUD 联调', 'org_id': org.id, 'cover_url': 'https://example.com/banner1.png', 'status': 1},
        )
        await get_or_create(
            session,
            MallSku,
            sku_code='DEMO-SKU-001',
            defaults={'spu_id': gift_spu.id, 'spec_json': json.dumps({'颜色': '黑色'}, ensure_ascii=False), 'sale_price': Decimal('199.00'), 'market_price': Decimal('239.00'), 'stock': 88},
        )
        service_spu, _ = await get_or_create(
            session,
            MallSpu,
            name='企业数据看板服务',
            category_id=category_service.id,
            defaults={'subtitle': '支持大屏指标与经营分析', 'org_id': org.id, 'cover_url': 'https://example.com/banner2.png', 'status': 2},
        )
        await get_or_create(
            session,
            MallSku,
            sku_code='DEMO-SKU-002',
            defaults={'spu_id': service_spu.id, 'spec_json': json.dumps({'套餐': '季度版'}, ensure_ascii=False), 'sale_price': Decimal('599.00'), 'market_price': Decimal('899.00'), 'stock': 30},
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
                'total_amount': Decimal('199.00'),
                'pay_amount': Decimal('199.00'),
                'created_by': client_user.id,
                'receiver_name': '王小明',
                'receiver_phone': '13800001234',
                'items_count': 2,
            },
        )
        await get_or_create(
            session,
            MallOrder,
            order_no='DEMO202603180002',
            defaults={
                'user_id': client_user.id,
                'org_id': org.id,
                'status': 'paid',
                'pay_status': 'paid',
                'refund_status': 'none',
                'source_type': 'web',
                'total_amount': Decimal('599.00'),
                'pay_amount': Decimal('599.00'),
                'created_by': admin_user.id,
                'receiver_name': '刘晓燕',
                'receiver_phone': '13900004321',
                'items_count': 1,
            },
        )

        await get_or_create(session, CmsBanner, title='首页活动', defaults={'image_url': 'https://example.com/banner1.png', 'link_url': 'https://example.com/promo', 'sort': 10, 'status': 1})
        await get_or_create(session, CmsBanner, title='企业采购节', defaults={'image_url': 'https://example.com/banner2.png', 'link_url': 'https://example.com/purchase', 'sort': 20, 'status': 1})
        await get_or_create(session, CmsNotice, title='系统升级公告', defaults={'content': '本周五凌晨进行系统升级。', 'status': 1, 'pinned': True})
        await get_or_create(session, CmsNotice, title='积分活动', defaults={'content': '下单即送积分。', 'status': 1, 'pinned': False})

        await get_or_create(session, SystemSetting, config_key='mall.order_auto_cancel_minutes', defaults={'config_value': '30', 'remark': '订单自动取消分钟数'})
        await get_or_create(session, SystemSetting, config_key='upload.max_file_size_mb', defaults={'config_value': '20', 'remark': '单文件上传限制'})
        await get_or_create(session, SystemDict, dict_type='order_status', dict_label='待处理', dict_value='pending', defaults={'sort': 10})
        await get_or_create(session, SystemDict, dict_type='order_status', dict_label='已支付', dict_value='paid', defaults={'sort': 20})

        await get_or_create(
            session,
            FileAsset,
            object_key='uploads/demo/banner1.png',
            defaults={
                'storage_provider': 'mock',
                'bucket': 'demo',
                'file_name': 'banner1.png',
                'file_ext': 'png',
                'mime_type': 'image/png',
                'file_size': 204800,
                'file_url': 'https://storage.example.com/uploads/demo/banner1.png',
            },
        )
        await get_or_create(
            session,
            OperationLog,
            module='system',
            action='seed_demo',
            path='/scripts/seed_demo.py',
            defaults={'user_id': admin_user.id, 'detail': '初始化演示数据'},
        )

        await session.commit()
        print('Seed completed.')
        print('Admin login: admin / Admin@123456')
        print('Client login: 13800000000 / User@123456 or SMS code mock')
        print('Demo orders: DEMO202603180001, DEMO202603180002')
        print('Mock miniapp openid: mini_demo_user')


if __name__ == '__main__':
    asyncio.run(main())
