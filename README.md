# FastAPI 商城 + 企业管理后台起步项目

这是一个可直接作为开发起点的 **FastAPI 后端骨架**，面向以下场景：

- 微信小程序
- Web 用户端
- 原生 App
- Web 管理后台
- 商城业务 + 企业组织管理
- 统一账号体系 + 微信绑定 + 手机验证码/密码登录
- 菜单权限 + 按钮权限 + 数据权限 + 部门组织架构

> 当前版本是 **Starter Scaffold**：重点是目录、模块边界、鉴权方式、数据模型示例、Docker 与文档，不是完整业务实现。

---

## 一、整体设计

### 架构形态
- 模块化单体（优先保证边界清晰和交付效率）
- 多端统一用户主体 `user`
- 前后台分域鉴权（`client` 与 `admin` token 分离）
- 微信能力独立封装
- 商城、权限、组织、消息、文件模块化
- Redis + PostgreSQL + Celery Worker

### API 分域
- `/api/admin/v1`：管理后台接口
- `/api/client/v1`：Web/App 用户端接口
- `/api/wechat/v1`：微信小程序专属接口
- `/api/open/v1`：第三方回调/开放接口

---

## 二、目录说明

```text
app/
├── api/                # 多端路由入口
├── bootstrap/          # 启动、日志、中间件、异常处理
├── core/               # 配置、数据库、Redis、安全、通用响应
├── db/                 # Alembic 配置与模型聚合
├── integrations/       # 微信、短信、对象存储、Push 适配层
├── modules/            # 业务模块
│   ├── iam             # 统一账号、登录、绑定、扫码登录
│   ├── org             # 公司、部门、员工
│   ├── rbac            # 角色、菜单、按钮、数据权限
│   ├── mall            # 商品、购物车、订单
│   ├── payment         # 支付、退款、回调
│   ├── notify          # 消息模板、发送记录
│   ├── cms             # Banner、公告
│   ├── file            # 文件、上传凭证
│   ├── system          # 系统配置、字典
│   ├── audit           # 操作日志、接口日志
│   └── stats           # 仪表盘统计
├── tasks/              # Celery 任务示例
└── main.py             # FastAPI 入口
```

补充文档：

- `docs/uv-usage.md`：`uv` 依赖管理与常用命令说明

---

## 三、快速启动

### 1. 准备环境变量
```bash
cp .env.example .env
```

### 2. 安装依赖
```bash
uv sync
```

### 3. 初始化数据库
```bash
uv run fast db migrate
```

### 4. 导入演示数据
```bash
uv run fast demo seed
```

也可以一键执行：

```bash
uv run fast demo init
```

### 5. 本地启动 API
```bash
uv run fast dev
```

### 6. 访问文档
- Swagger UI: `http://127.0.0.1:5100/docs`
- ReDoc: `http://127.0.0.1:5100/redoc`

### 7. Docker 启动
```bash
docker compose up -d --build
```

---

## 四、演示账号与联调数据

执行 `python scripts/seed_demo.py` 后，会生成：

- 后台账号：`admin / Admin@123456`
- C 端账号：`13800000000 / User@123456`
- 演示订单号：`DEMO202603180001`
- 演示小程序 openid：`mini_demo_user`

### 本地 Mock 行为
当 `.env` 中 `WECHAT_API_MOCK=true` 时：

- 小程序 `code2Session` 使用本地 mock 响应
- 小程序手机号换取使用本地 mock 响应
- JSAPI 下单不会真实调用微信支付，而是返回可联调结构
- 支付回调签名默认不强制校验

把 `WECHAT_API_MOCK=false` 并补齐商户参数后，就会切换到真实微信接口请求模式。

---

## 五、默认路由示例

### 管理后台
- `POST /api/admin/v1/auth/login`
- `GET /api/admin/v1/auth/me`
- `GET /api/admin/v1/org/departments`
- `GET /api/admin/v1/rbac/roles`
- `GET /api/admin/v1/mall/products`
- `GET /api/admin/v1/mall/orders`

### 用户端
- `POST /api/client/v1/auth/send-code`
- `POST /api/client/v1/auth/login-by-code`
- `POST /api/client/v1/auth/login-by-password`
- `GET /api/client/v1/auth/me`
- `GET /api/client/v1/products`
- `POST /api/client/v1/orders`

### 微信小程序
- `POST /api/wechat/v1/auth/login`
- `POST /api/wechat/v1/auth/bind-mobile`
- `POST /api/wechat/v1/qr-login/scan`
- `POST /api/wechat/v1/qr-login/confirm`
- `POST /api/wechat/v1/pay/create`

### 开放接口
- `POST /api/open/v1/pay/wechat/callback`

---

## 六、核心设计规则

### 1. 同一人多身份，统一到一个 user_id
- 手机号登录
- 密码登录
- 微信小程序登录
- Web 账号密码

都映射到统一的 `user` 主表，通过 `user_identity` 保存不同登录源。

### 2. 后台权限独立但可与统一用户打通
同一个用户既可以是商城用户，也可以是企业员工/后台管理员；
但 `admin` 与 `client` 的 token 独立签发，避免权限串用。

### 3. 数据权限预留字段
业务表建议统一预留：
- `org_id`
- `dept_id`
- `created_by`
- `updated_by`
- `owner_user_id`

---

## 七、后续建议

这个 Starter 比较适合先完成：

1. 统一登录注册与微信绑定
2. 组织架构 + RBAC
3. 商品与订单一期
4. 微信支付 + 退款
5. 消息中心（短信/微信/App Push）
6. 文件上传 + Banner/公告

你接下来可以直接在这套目录上补业务实现，而不用再推翻重来。
