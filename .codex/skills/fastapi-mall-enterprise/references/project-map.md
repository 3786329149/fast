# 项目地图

## 启动与装配

- 应用入口：`app/main.py`
- FastAPI 装配：`app/bootstrap/app.py`
- CLI 命令：`app/cli.py`
- 启动诊断、异常、中间件、日志：`app/bootstrap/`

## 路由分域

- 管理后台：`app/api/admin/v1/router.py`，统一前缀 `/api/admin/v1`
- 用户端：`app/api/client/v1/router.py`，统一前缀 `/api/client/v1`
- 微信端：`app/api/wechat/v1/router.py`，统一前缀 `/api/wechat/v1`
- 开放接口：`app/api/open/v1/router.py`，统一前缀 `/api/open/v1`

先判断请求属于哪个域，再回到对应模块里的 `routers_admin.py`、`routers_client.py` 或 `routers_wechat.py`。

## 关键目录

- `app/config/`：环境变量、配置模型、加载逻辑
- `app/core/`：响应包装、异常、枚举、常量
- `app/infra/`：数据库、缓存、安全、第三方集成
- `app/modules/`：业务模块
- `app/tasks/`：Celery 任务
- `alembic/versions/`：迁移文件
- `scripts/`：演示数据和辅助脚本
- `tests/`：基础测试

## 业务模块现状

当前实际目录以仓库文件为准，包含：

- `audit`
- `cms`
- `file`
- `iam`
- `mall`
- `notify`
- `order`
- `org`
- `payment`
- `rbac`
- `statistices`
- `stats`
- `system`
- `user`
- `wechat`

README 中的模块列表是概览，不一定与当前文件系统完全同步；查目录时优先相信 `app/modules/` 的实际内容。

## 模块内常见分层

多数模块沿用以下结构：

- `models.py`：SQLAlchemy 模型
- `schemas.py`：Pydantic 请求/响应结构
- `repository.py`：数据库访问
- `service.py`：业务编排
- `routers_admin.py` / `routers_client.py` / `routers_wechat.py`：接口层

## 通用依赖与协议

- 数据库依赖：`app.api.deps.get_db`
- 当前用户与权限：`app.api.deps.get_current_*`、`require_permission`
- 统一响应：`app.core.response.success`、`app.core.response.failure`
- ORM 基类与 mixin：`app.infra.db.base`

## 常用命令入口

- 启动开发服务：`uv run fast dev`
- 启动 worker：`uv run fast worker`
- 环境体检：`uv run fast doctor`
- 运行测试：`uv run fast test`
- 代码检查：`uv run fast lint`
- 代码格式化：`uv run fast format`
- 执行迁移：`uv run fast db migrate`
- 生成迁移：`uv run fast db revision`
- 导入演示数据：`uv run fast demo seed`
- 初始化演示环境：`uv run fast demo init`
