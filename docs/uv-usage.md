# uv 使用说明

本文档说明本项目如何用 `uv` 管理 Python、依赖、虚拟环境与常用开发命令。

## 1. 当前项目状态

当前仓库已经具备 `uv` 管理基础：

- 根目录存在 `pyproject.toml`
- 根目录存在 `uv.lock`
- 依赖声明以 `pyproject.toml` 为准
- 锁定结果以 `uv.lock` 为准

也就是说，这个项目可以按 `uv` 标准方式使用，不必继续以 `pip install -e .[dev]` 作为首选入口。

## 2. 安装 uv

先确认本机已安装：

```bash
uv --version
```

如果没有安装，可参考官方文档：

- [uv 官方文档](https://docs.astral.sh/uv/)

## 3. 初始化项目

推荐在项目根目录执行：

```bash
uv sync
```

如果需要开发依赖，一般直接：

```bash
uv sync
```

如果只装运行依赖：

```bash
uv sync --no-dev
```

如果希望严格按照锁文件安装：

```bash
uv sync --frozen
```

## 4. 运行常用命令

推荐统一使用 `uv run`，这样可以确保命令运行在项目虚拟环境里。

本项目已补充一组项目脚本命令，推荐优先使用：

- `uv run python -m app.cli dev`
- `uv run python -m app.cli worker`
- `uv run python -m app.cli lint`
- `uv run python -m app.cli format`
- `uv run python -m app.cli test`
- `uv run python -m app.cli migrate`
- `uv run python -m app.cli revision`
- `uv run python -m app.cli seed-demo`
- `uv run python -m app.cli init-demo`

### 启动 API

```bash
uv run python -m app.cli dev
```

### 执行数据库迁移

```bash
uv run python -m app.cli migrate
```

### 导入演示数据

```bash
uv run python -m app.cli seed-demo
```

### 一键初始化数据库和演示数据

```bash
uv run python -m app.cli init-demo
```

### 运行测试

```bash
uv run python -m app.cli test
```

该命令会显式运行 `tests` 与 `app/tests`，并关闭 `pytest` 缓存插件，避免 Windows 下临时缓存目录干扰测试收集。

### 运行代码检查

```bash
uv run python -m app.cli lint
```

### 格式化代码

```bash
uv run python -m app.cli format
```

### 启动 Celery Worker

```bash
uv run python -m app.cli worker
```

## 5. 增删依赖

### 添加运行依赖

```bash
uv add httpx
```

### 添加开发依赖

```bash
uv add --dev pytest
```

### 删除依赖

```bash
uv remove httpx
```

添加或删除依赖后，`uv.lock` 会同步更新，需要一起提交。

## 6. 锁文件说明

- `pyproject.toml` 是依赖声明
- `uv.lock` 是精确锁定结果

团队协作时建议遵守：

1. 修改依赖时同时提交 `pyproject.toml` 和 `uv.lock`
2. 拉取代码后优先执行 `uv sync --frozen`
3. 不要手动编辑 `uv.lock`

## 7. Windows 环境注意事项

本项目在当前机器上发现过一个 `uv` 缓存目录异常：

```text
Failed to initialize cache at C:\Users\Administrator\AppData\Local\uv\cache
```

如果你本机也遇到类似问题，可以临时指定项目内缓存目录：

```powershell
$env:UV_CACHE_DIR = ".uv-cache"
uv sync --frozen
```

或者：

```powershell
$env:UV_CACHE_DIR = "D:\\develop\\code\\python\\fast\\.uv-cache"
uv sync --frozen
```

验证结果表明，在显式设置 `UV_CACHE_DIR` 后，本项目的锁文件可以正常工作。

## 8. 推荐工作流

日常开发建议按下面顺序执行：

```bash
uv sync
uv run python -m app.cli migrate
uv run python -m app.cli init-demo
uv run python -m app.cli dev
```

如果已经初始化过数据库，则常用命令通常是：

```bash
uv sync --frozen
uv run python -m app.cli dev
```

## 9. 当前项目里和 uv 相关的注意点

当前仓库已统一补充项目级 `uv run python -m app.cli ...` 命令，后续新增常用脚本时，也建议继续放到同一套入口里维护。
