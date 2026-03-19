## 一、最终架构判断

### 1）架构形态

采用：

- **模块化单体**
    
- **前后台 API 分域**
    
- **统一用户主体**
    
- **组织架构 + RBAC + 数据权限**
    
- **商城业务模块化**
    
- **微信能力单独封装**
    
- **异步任务独立 worker**
    

也就是说，不是一开始拆微服务，而是先把边界拆清楚：：
```bash
客户端层
├─ 微信小程序
├─ Web 用户端
├─ 原生 App
└─ Web 管理后台

接入层
├─ Nginx / Gateway
└─ FastAPI

API 分域
├─ /api/admin/v1    后台
├─ /api/client/v1   Web/App 用户端
├─ /api/wechat/v1   小程序/微信专属能力
└─ /api/open/v1     回调/开放接口

业务模块
├─ iam（账号/登录/绑定）
├─ org（组织/部门/员工）
├─ rbac（角色/菜单/按钮/数据权限）
├─ mall（商品/库存/购物车/订单/售后）
├─ payment（支付/退款/对账）
├─ notify（短信/微信消息/App Push）
├─ cms（Banner/公告/内容）
├─ file（上传/媒体/对象存储）
├─ system（配置/字典/审计）
└─ stats（统计/报表）
```

## 二、推荐技术栈

建议这套：
```bash
Python 3.12  
FastAPI  
Pydantic v2 + pydantic-settings  
SQLAlchemy 2.x async  
Alembic  
PostgreSQL  
Redis  
Celery / ARQ  
对象存储（OSS/COS/S3 三选一）  
Nginx + Uvicorn  
Docker
```

理由是：

- FastAPI 适合按 `APIRouter` 拆大型应用，安全这块也有官方的 OAuth2/JWT 组织方式；
    
- 配置层建议直接用 `pydantic-settings`；
    
- 数据层用 SQLAlchemy asyncio；
    
- 迁移继续用 Alembic；
    
- 应用启动/关闭资源初始化建议走 `lifespan`；
    
- 短信、推送、延迟关单、支付补单、报表这些任务不要只靠简单后台任务，应该走队列 worker。

部署上建议：

- `api` 容器
    
- `worker` 容器
    
- `postgres` 容器
    
- `redis` 容器
    

FastAPI 官方文档也明确有 worker/容器化部署思路；在容器场景里，通常更适合每个容器跑单个进程，再靠副本扩容

## 三、最关键的设计：统一账号，但前后台令牌隔离

这是你项目能不能后期不烂掉的关键。

### 设计原则

- **一个人，系统里尽量只有一个 `user_id`**
    
- 小程序、App、Web 用户端，共用一个账号主体
    
- 后台权限不要直接和 C 端用户权限混为一谈
    
- 同一个人可以既是商城用户，也是企业员工/后台管理员
    
- 但是：
    
    - **C 端 token 独立**
        
    - **后台 token 独立**
        
    - 权限体系独立
        

### 推荐模型
```bash
user                  统一用户主表
user_profile          用户资料
user_identity         登录身份表
employee_profile      企业员工资料
admin_role            后台角色
admin_permission      权限点
admin_user_role       用户-后台角色关系
```
### `user_identity` 建议支持这些类型
```bash
mobile_code  
password  
wechat_miniapp  
wechat_app  
web_account
```
### 为什么这样设计

因为你的登录方式是：

- 小程序：微信登录 + 手机号绑定
    
- App：验证码 / 密码 / 可绑定微信
    
- Web：手机号 / 账号密码 / 小程序扫码登录
    

如果不做 `identity` 拆分，后面会非常乱。
## 四、登录方案，按端拆开

## 1）微信小程序登录

建议流程：

1. 小程序拿微信登录凭证
    
2. 后端建立或识别微信身份
    
3. 如果未绑定手机号，进入绑定流程
    
4. 绑定手机号后，归并到统一 `user_id`
    
5. 下发 **client token**
    

后端要有这些状态：

- 未绑定手机号的“半登录态”
    
- 已完成绑定的正式登录态
    
- 微信身份与内部账号绑定关系
    

### 小程序接口建议
```bash
POST /api/wechat/v1/auth/login  
POST /api/wechat/v1/auth/bind-mobile  
POST /api/wechat/v1/auth/unbind  
GET /api/wechat/v1/auth/me
```

## 2）原生 App 登录

支持三种：

- 手机验证码登录
    
- 账号密码登录
    
- 绑定微信后快捷登录
    

### App 接口建议
```bash
POST /api/client/v1/auth/send-code  
POST /api/client/v1/auth/login-by-code  
POST /api/client/v1/auth/login-by-password  
POST /api/client/v1/auth/bind-wechat  
POST /api/client/v1/auth/refresh-token  
POST /api/client/v1/device/register  
POST /api/client/v1/push/register
```
## 3）Web 用户端登录

支持：

- 手机号验证码
    
- 账号密码
    
- 小程序扫码登录
    

### 我建议你把“Web 小程序扫码登录”设计成桥接方案

不要把它硬做成某个第三方登录页面逻辑，而是做成你自己的站内流程：

```bash
Web 端请求一个 login_ticket  
-> 后端生成二维码内容（ticket）  
-> 用户用小程序扫码  
-> 小程序调用“确认登录”接口  
-> 后端把 ticket 标记为 confirmed  
-> Web 端轮询 / SSE / WebSocket 获得确认结果  
-> 后端给 Web 端签发 client token
```
### 这样做的好处

- 完全符合你“账号打通”的目标
    
- Web 登录不依赖额外复杂前置条件
    
- 登录确认发生在你自己的小程序里，体验更统一
    
- 后续还能扩展成：
    
    - PC 登录确认
        
    - 敏感操作二次确认
        
    - 管理员扫码复核
        

### Web 扫码登录接口建议
```bash
POST /api/client/v1/qr-login/create  
GET  /api/client/v1/qr-login/status/{ticket}  
POST /api/wechat/v1/qr-login/scan  
POST /api/wechat/v1/qr-login/confirm  
POST /api/wechat/v1/qr-login/cancel
```
## 4）后台管理登录

后台建议单独一套 session 体系：

- 后台账号密码
    
- 短信验证码二次校验（可选）
    
- 后期可加 Google Authenticator / 企业微信 / 扫码确认
    

### 后台接口建议
```bash
POST /api/admin/v1/auth/login  
POST /api/admin/v1/auth/logout  
POST /api/admin/v1/auth/refresh  
GET  /api/admin/v1/auth/me  
POST /api/admin/v1/auth/change-password
```
### Token 建议区分场景

JWT 里至少加：
```bash
{  
  "sub": "user_id",  
  "scene": "client | admin",  
  "org_id": 1,  
  "dept_id": 10,  
  "roles": ["mall_admin"],  
  "token_type": "access"  
}
```


这样同一个人既能登录 C 端，也能登录后台，但权限不会串。

FastAPI 官方示例本身就是按 OAuth2 + JWT 的方式组织认证流程，这套思路适合你后台这一层
## 五、组织架构 + 菜单权限 + 按钮权限 + 数据权限

你明确说了这四项都要，那就从第一版就建好，不要后补。

## 权限模型建议

### 1）菜单权限

控制左侧菜单、页面可见性。

表：

- `admin_menu`
    

字段建议：

- `id`
    
- `parent_id`
    
- `name`
    
- `type`（directory/menu/button/api）
    
- `path`
    
- `component`
    
- `icon`
    
- `permission_code`
    
- `sort`
    
- `status`
    

---

### 2）按钮权限

本质是权限点，不一定真的对应按钮。

例子：
```bash
mall:order:list  
mall:order:detail  
mall:order:refund  
mall:product:create  
mall:product:publish  
org:employee:update  
system:role:assign
```


前端拿权限码控制按钮显示，后端也按权限码校验接口。

---

### 3）数据权限

建议从一开始就做成角色数据范围：
```bash
ALL             全部数据  
ORG             本组织  
ORG_AND_CHILD   本组织及子组织  
DEPT            本部门  
DEPT_AND_CHILD  本部门及下级部门  
SELF            仅本人  
CUSTOM          自定义范围
```

### 必须在业务表里预留这些字段

- `org_id`
    
- `dept_id`
    
- `created_by`
    
- `updated_by`
    
- `owner_user_id`
    

否则后面数据权限很难补。

---

### 4）组织架构

建议独立成 `org` 模块：

- 公司/组织
    
- 部门
    
- 岗位
    
- 员工
    
- 员工部门关系
    
- 直属上级
    

如果未来可能多公司/多主体，建议现在就把 `org_id` 做成第一公民；  
如果未来可能做 SaaS，多租户先不启用，但表里可以预留 `tenant_id`。

---

## 六、商城模块建议

你是“商城 + 企业管理”，所以商城不要只做 C 端交易，还要兼顾后台运营和组织维度。

### 商城核心模块

- 商品分类
    
- SPU / SKU
    
- 属性与规格
    
- 库存
    
- 购物车
    
- 订单
    
- 支付
    
- 退款
    
- 售后
    
- 优惠券
    
- 会员价/等级价（可后补）
    
- Banner / 活动页
    
- 配送地址
    

### 企业管理结合点

建议商城业务表也挂组织维度：

- 商品归属组织
    
- 订单归属组织/门店/业务线
    
- 操作人归属部门
    
- 报表按组织树聚合
    

这会直接影响：

- 数据权限
    
- 业绩统计
    
- 部门看板
    
- 店铺/分公司数据隔离
    

---

## 七、消息能力设计

你说支付和消息都要，那消息不要做成“工具函数”，要做成模块。

### notify 模块

拆成三层：
```bash
notify/  
├─ template      模板  
├─ channel       短信/微信/App Push  
├─ service       发送编排  
└─ record        发送记录/回执
```

### 支持的通道

- 短信
    
- 微信通知
    
- App Push
    
- 邮件（先预留）
    

### 典型异步任务

- 登录验证码发送
    
- 支付成功通知
    
- 发货通知
    
- 退款通知
    
- 后台审批通知
    
- App 推送
    
- 小程序订阅消息补发
    

这类任务适合走 worker，而不是直接阻塞接口响应。FastAPI 官方文档也明确说明：小型后台任务可以用 `BackgroundTasks`，更重的跨进程任务更适合 Celery 这类队列方案。

---

## 八、建议的 FastAPI 项目目录
```bash
backend/  
├── app/  
│   ├── main.py  
│   ├── bootstrap/  
│   │   ├── lifespan.py  
│   │   ├── middleware.py  
│   │   ├── exception_handlers.py  
│   │   └── logging.py  
│   ├── core/  
│   │   ├── config.py  
│   │   ├── security.py  
│   │   ├── database.py  
│   │   ├── redis.py  
│   │   ├── response.py  
│   │   ├── enums.py  
│   │   └── constants.py  
│   ├── api/  
│   │   ├── deps.py  
│   │   ├── admin/v1/  
│   │   ├── client/v1/  
│   │   ├── wechat/v1/  
│   │   └── open/v1/  
│   ├── modules/  
│   │   ├── iam/  
│   │   │   ├── models/  
│   │   │   ├── schemas/  
│   │   │   ├── repositories/  
│   │   │   ├── services/  
│   │   │   └── routers/  
│   │   ├── org/  
│   │   ├── rbac/  
│   │   ├── mall/  
│   │   ├── payment/  
│   │   ├── notify/  
│   │   ├── cms/  
│   │   ├── file/  
│   │   ├── system/  
│   │   ├── audit/  
│   │   └── stats/  
│   ├── integrations/  
│   │   ├── wechat/  
│   │   ├── sms/  
│   │   ├── storage/  
│   │   └── push/  
│   ├── tasks/  
│   │   ├── notify_tasks.py  
│   │   ├── order_tasks.py  
│   │   ├── payment_tasks.py  
│   │   └── report_tasks.py  
│   ├── db/  
│   │   ├── migrations/  
│   │   └── seeds/  
│   ├── tests/  
│   └── utils/  
├── docker/  
├── scripts/  
├── alembic.ini  
├── pyproject.toml  
├── .env.example  
└── docker-compose.yml
```

FastAPI 官方确实支持这种“多文件/多模块”组织方式；配置启动与关闭资源时，推荐用 `lifespan` 而不是继续混用旧的 startup/shutdown 事件。

---

## 九、数据库表初稿

下面这套足够起一期。

## 1）统一账号 / 登录
```bash
user  
user_profile  
user_identity  
user_session  
user_device  
user_bind_log  
captcha_record  
login_log
```


### `user_identity`

建议字段：

- `id`
    
- `user_id`
    
- `identity_type`  
    （mobile_code/password/wechat_miniapp/wechat_app/web_account）
    
- `identity_key`
    
- `credential_hash`
    
- `is_verified`
    
- `extra_json`
    
- `created_at`
    

---

## 2）组织 / 企业管理
```bash
org_company  
org_department  
org_position  
employee_profile  
employee_department_rel  
employee_leader_rel
```

### `org_department`

建议字段：

- `id`
    
- `org_id`
    
- `parent_id`
    
- `name`
    
- `tree_path`
    
- `leader_user_id`
    
- `sort`
    
- `status`
    

`tree_path` 很重要，做“部门及子部门”数据权限会轻松很多。

---

## 3）后台权限
```bash
admin_role  
admin_permission  
admin_menu  
admin_role_permission  
admin_user_role  
admin_role_menu  
admin_data_scope  
admin_role_data_scope
```


---

## 4）商城
```bash
mall_shop  
mall_category  
mall_spu  
mall_sku  
mall_sku_stock  
mall_sku_price  
mall_cart  
mall_order  
mall_order_item  
mall_coupon_template  
mall_user_coupon  
mall_payment_order  
mall_refund_order  
mall_aftersale_order  
mall_address
```

### 订单表必须预留

- `order_no`
    
- `user_id`
    
- `org_id`
    
- `shop_id`
    
- `status`
    
- `pay_status`
    
- `refund_status`
    
- `total_amount`
    
- `pay_amount`
    
- `created_by`
    
- `source_type`（miniapp/app/web/admin）
    

---

## 5）消息
```bash
notify_template  
notify_message  
sms_record  
wechat_message_record  
push_device_token  
push_record
```

---

## 6）内容 / 文件

```bash
cms_banner  
cms_notice  
cms_article  
file_asset  
file_folder  
file_upload_log
```


---

## 7）系统 / 审计
```bash
system_config  
system_dict  
operation_log  
api_access_log  
job_log
```


---

## 十、API 路由建议

## 后台
```bash
/api/admin/v1/auth/**  
/api/admin/v1/users/**  
/api/admin/v1/employees/**  
/api/admin/v1/org/departments/**  
/api/admin/v1/roles/**  
/api/admin/v1/permissions/**  
/api/admin/v1/menus/**  
/api/admin/v1/mall/products/**  
/api/admin/v1/mall/orders/**  
/api/admin/v1/mall/refunds/**  
/api/admin/v1/cms/**  
/api/admin/v1/files/**  
/api/admin/v1/system/**  
/api/admin/v1/audit/**
```

## 用户端
```bash
/api/client/v1/auth/**  
/api/client/v1/profile/**  
/api/client/v1/address/**  
/api/client/v1/cart/**  
/api/client/v1/products/**  
/api/client/v1/orders/**  
/api/client/v1/pay/**  
/api/client/v1/coupons/**  
/api/client/v1/qr-login/**
```

## 微信专属
```bash
/api/wechat/v1/auth/login  
/api/wechat/v1/auth/bind-mobile  
/api/wechat/v1/qr-login/scan  
/api/wechat/v1/qr-login/confirm  
/api/wechat/v1/pay/create
```

## 回调接口
```bash
/api/open/v1/pay/wechat/callback  
/api/open/v1/sms/callback  
/api/open/v1/storage/callback
```


---

## 十一、几个必须定下来的后端规则

### 1）同一人可多身份，但主账号只有一个

统一主键永远是 `user_id`，不是手机号，也不是微信标识。

### 2）管理员不是单独孤岛

后台管理员本质上也是系统用户，只是在后台域拥有额外角色、组织关系和权限。

### 3）C 端与后台 token 分开

即使是同一个用户，也不能混发同一套 token。

### 4）所有业务表预留数据权限字段

至少：

- `org_id`
    
- `dept_id`
    
- `created_by`
    
- `updated_by`
    
- `deleted_at`
    

### 5）外部能力都走 integration adapter

微信、短信、Push、对象存储，不要直接散落在 service 里。

---

## 十二、还差哪些信息，但现在不阻塞

你前面说 9 和 10 可以先放一下，这没问题。当前不阻塞开发，但后面要补这几项：

- 微信支付是普通支付，还是还要退款、分账、对账
    
- 短信供应商
    
- App Push 供应商
    
- 对象存储厂商
    
- 是否后期要多租户
    
- 商城是否有门店/仓库/配送规则
    

这些不影响现在先把骨架、表结构、鉴权、权限、组织、商城一期先搭起来。

---

## 十三、我对你这个项目的最终建议

这版直接按下面落地最稳：

- **架构**：模块化单体
    
- **账号**：统一 `user` 主体 + 多登录身份
    
- **后台权限**：RBAC + 菜单 + 按钮 + 数据权限 + 部门组织
    
- **多端接口**：`admin / client / wechat / open`
    
- **扫码登录**：Web 登录票据 + 小程序确认桥接
    
- **商城**：订单/支付/退款/优惠券/售后分模块
    
- **消息**：短信 / 微信 / App Push 统一 notify 中台
    
- **部署**：API + Worker + Redis + PostgreSQL
    

下一条我就按这套结构，直接给你一份 **FastAPI 项目骨架目录 + 核心数据模型 + 路由示例代码**。