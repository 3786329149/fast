---
name: fastapi-mall-enterprise
description: 在当前 FastAPI 商城加企业管理后台脚手架仓库中开发、调试、重构或排障时使用。适用于定位和修改 app/api、app/modules、app/config、app/infra、alembic、scripts、tests 下的代码，新增或调整管理端、客户端、微信端、开放接口，处理鉴权、配置、数据库迁移、演示数据与 uv 工作流。
---

# FastAPI Mall Enterprise

## 快速进入

- 先读 `README.md` 与 `docs/uv-usage.md`，确认任务属于哪个接口域、哪个业务模块。
- 优先使用 `uv run fast ...` 执行开发、测试、迁移和诊断命令，不要绕开项目 CLI 另起一套入口。
- 修改前先看工作区状态，避免覆盖用户已有改动。

## 按任务定位代码

- 读 `references/project-map.md`，快速确认目录、路由分域和关键文件位置。
- 读 `references/task-playbook.md`，按任务类型选择进入点和验证命令。
- 先判断接口属于 `/api/admin/v1`、`/api/client/v1`、`/api/wechat/v1` 还是 `/api/open/v1`，再去对应 `app/api/*/v1/router.py` 挂载模块路由。
- 进入业务模块后，优先沿用现有拆分：`models.py`、`schemas.py`、`repository.py`、`service.py`、`routers_*.py`。

## 保持现有约定

- 复用 `app.api.deps` 中的数据库会话、当前用户与权限依赖。
- 复用 `app.core.response.success` 与 `app.core.response.failure` 统一返回结构。
- 复用 `AppException`、枚举、常量和现有 token scene，不要在模块里重复发明一套鉴权或响应协议。
- 新增常用研发命令时，优先补到 `app/cli.py`，保持 `uv run fast ...` 为统一入口。
- 配置项变更时，同时更新 `.env.example` 和相应的示例环境文件。

## 处理数据相关改动

- 变更数据表时，同时检查 SQLAlchemy 模型、Alembic 迁移、演示数据脚本和受影响测试。
- 生成或调整迁移后，确认迁移文件放在 `alembic/versions/`，命名与内容可读。
- 演示账号、订单、微信 mock 相关改动时，同步检查 `scripts/seed_demo.py` 与 README 中的说明是否仍然一致。

## 验证顺序

- 改动接口、依赖注入或业务逻辑后，至少执行对应测试；没有精确测试时执行 `uv run fast test`。
- 改动导入、格式或静态问题后，执行 `uv run fast lint`；需要统一格式时执行 `uv run fast format`。
- 改动配置、启动链路、数据库或 Redis 依赖时，先执行 `uv run fast doctor`。
- 改动迁移或演示数据时，执行 `uv run fast db migrate`、`uv run fast demo seed` 或 `uv run fast demo init` 做最小闭环验证。
