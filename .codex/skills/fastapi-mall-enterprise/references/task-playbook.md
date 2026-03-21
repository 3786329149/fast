# 任务手册

## 新增或修改接口

1. 判断接口域：管理后台、用户端、微信端或开放接口。
2. 打开对应 `app/api/*/v1/router.py`，确认该域已挂哪些模块路由。
3. 进入目标模块，优先复用现有 `routers_* -> service -> repository` 调用链。
4. 保持返回结构走 `success` / `failure`，鉴权和数据库依赖走 `app.api.deps`。
5. 补最小测试；没有模块级测试时，至少补 `tests/` 下可运行的回归测试。

## 修改登录、权限或用户上下文

1. 先看 `app/api/deps.py`，确认当前用户提取和权限校验入口。
2. 再看 `app/infra/security/token.py` 与相关模块的 `service.py`。
3. 区分 `ADMIN` 和 `CLIENT` scene，不要混用 token。
4. 需要接口鉴权变更时，同时检查调用方路由和测试。

## 修改配置或环境变量

1. 从 `app/config/` 下的 schema、loader、helpers 入手。
2. 补 `.env.example` 和相关示例文件，不要只改本地 `.env`。
3. 如果配置影响启动链路、数据库或 Redis，执行 `uv run fast doctor` 验证。

## 修改数据库模型或迁移

1. 先改 `models.py` 或基础 ORM 定义。
2. 再补或调整 `alembic/versions/` 下的迁移。
3. 如果演示数据依赖该结构，更新 `scripts/seed_demo.py`。
4. 执行 `uv run fast db migrate`，必要时再执行 `uv run fast demo seed`。

## 修改演示数据或联调说明

1. 优先检查 `scripts/seed_demo.py`。
2. 同步核对 `README.md` 中的默认账号、订单号、mock 行为说明。
3. 如果改了示例命令或工作流，同步核对 `docs/uv-usage.md`。

## 排查启动或健康检查问题

1. 先执行 `uv run fast doctor`。
2. 再看 `app/bootstrap/app.py`、`app/bootstrap/lifespan.py`、`app/bootstrap/diagnostics.py`。
3. 如果是基础可用性问题，补或更新 `tests/test_health.py`、`tests/test_observability.py`。

## 日常验证建议

- 小范围 Python 代码改动：`uv run fast lint`
- 接口或业务逻辑改动：`uv run fast test`
- 格式明显不一致：`uv run fast format`
- 启动链路或基础设施改动：`uv run fast doctor`
- 迁移与演示数据改动：`uv run fast db migrate` 和 `uv run fast demo seed`
