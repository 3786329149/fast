from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response
from typer.testing import CliRunner

from app import cli
from app.bootstrap import diagnostics, logging as logging_bootstrap, middleware

runner = CliRunner()


class FakeLogger:
    def __init__(self) -> None:
        self.records: list[tuple[str, str, dict]] = []

    def info(self, event: str, **kwargs) -> None:
        self.records.append(("info", event, kwargs))

    def error(self, event: str, **kwargs) -> None:
        self.records.append(("error", event, kwargs))

    def exception(self, event: str, **kwargs) -> None:
        self.records.append(("exception", event, kwargs))


@pytest.mark.asyncio
async def test_run_startup_diagnostics_success(monkeypatch) -> None:
    async def fake_probe_database() -> dict:
        return {
            "connected": True,
            "latency_ms": 1.2,
            "driver": "postgresql+asyncpg",
            "host": "127.0.0.1",
            "port": 5432,
            "database": "mall_enterprise",
        }

    async def fake_probe_redis(*, keep_client: bool) -> dict:
        assert keep_client is False
        return {
            "connected": True,
            "latency_ms": 0.8,
            "host": "127.0.0.1",
            "port": 6379,
            "db": 0,
        }

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/api/admin/v1/ping")
    async def admin_ping() -> dict:
        return {"status": "ok"}

    @app.get("/api/client/v1/ping")
    async def client_ping() -> dict:
        return {"status": "ok"}

    @app.get("/api/open/v1/ping")
    async def open_ping() -> dict:
        return {"status": "ok"}

    monkeypatch.setattr(diagnostics, "probe_database", fake_probe_database)
    monkeypatch.setattr(diagnostics, "probe_redis", fake_probe_redis)

    result = await diagnostics.run_startup_diagnostics(
        app,
        include_details=True,
        keep_redis_client=False,
    )

    assert result["status"] == "ok"
    assert result["database"]["connected"] is True
    assert result["redis"]["connected"] is True
    assert result["tables"]["count"] > 0
    assert result["tables"]["names"]
    assert result["routes"]["count"] == 3
    assert result["routes"]["domains"] == {
        "admin": 1,
        "client": 1,
        "wechat": 0,
        "open": 1,
        "other": 0,
    }


@pytest.mark.asyncio
async def test_run_startup_diagnostics_fails_fast_on_database(monkeypatch) -> None:
    called = False

    async def fake_probe_database() -> dict:
        raise RuntimeError("db down")

    async def fake_probe_redis(*, keep_client: bool) -> dict:
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(diagnostics, "probe_database", fake_probe_database)
    monkeypatch.setattr(diagnostics, "probe_redis", fake_probe_redis)

    with pytest.raises(RuntimeError, match="db down"):
        await diagnostics.run_startup_diagnostics(FastAPI(), keep_redis_client=False)

    assert called is False


@pytest.mark.asyncio
async def test_run_startup_diagnostics_fails_fast_on_redis(monkeypatch) -> None:
    async def fake_probe_database() -> dict:
        return {
            "connected": True,
            "latency_ms": 1.2,
            "driver": "postgresql+asyncpg",
            "host": "127.0.0.1",
            "port": 5432,
            "database": "mall_enterprise",
        }

    async def fake_probe_redis(*, keep_client: bool) -> dict:
        raise RuntimeError("redis down")

    monkeypatch.setattr(diagnostics, "probe_database", fake_probe_database)
    monkeypatch.setattr(diagnostics, "probe_redis", fake_probe_redis)

    with pytest.raises(RuntimeError, match="redis down"):
        await diagnostics.run_startup_diagnostics(FastAPI(), keep_redis_client=False)


def test_build_renderer_switches_by_format() -> None:
    assert logging_bootstrap.build_renderer("pretty").__class__.__name__ == "ConsoleRenderer"
    assert logging_bootstrap.build_renderer("json").__class__.__name__ == "JSONRenderer"


@pytest.mark.asyncio
async def test_request_middleware_logs_request_details(monkeypatch) -> None:
    fake_logger = FakeLogger()
    monkeypatch.setattr(middleware, "logger", fake_logger)

    app = FastAPI()
    request_middleware = middleware.RequestContextMiddleware(app)
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/hello",
            "raw_path": b"/hello",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "scheme": "http",
            "server": ("testserver", 80),
            "query_string": b"",
            "root_path": "",
        }
    )

    async def call_next(_: Request) -> Response:
        return Response("ok", status_code=200)

    response = await request_middleware.dispatch(request, call_next)

    assert response.headers["X-Request-ID"]
    assert response.headers["X-Process-Time"]
    assert fake_logger.records[0][0] == "info"
    assert fake_logger.records[0][1] == "request_completed"
    assert fake_logger.records[0][2]["method"] == "GET"
    assert fake_logger.records[0][2]["path"] == "/hello"
    assert fake_logger.records[0][2]["status_code"] == 200
    assert fake_logger.records[0][2]["client_ip"] == "127.0.0.1"
    assert "duration_ms" in fake_logger.records[0][2]


def test_doctor_returns_non_zero_on_failure(monkeypatch) -> None:
    async def fake_run_startup_diagnostics(app, **_: object) -> dict:
        raise RuntimeError("boom")

    monkeypatch.setattr(cli, "configure_logging", lambda: None)
    monkeypatch.setattr(cli, "create_app", lambda: SimpleNamespace())
    monkeypatch.setattr(cli, "run_startup_diagnostics", fake_run_startup_diagnostics)

    with pytest.raises(SystemExit) as exc_info:
        cli.doctor()

    assert exc_info.value.code == 1


def test_cli_help() -> None:
    result = runner.invoke(cli.app, ["--help"])

    assert result.exit_code == 0
    assert "Project development commands" in result.stdout
    assert "db" in result.stdout
    assert "demo" in result.stdout


def test_db_help() -> None:
    result = runner.invoke(cli.app, ["db", "--help"])

    assert result.exit_code == 0
    assert "Database commands" in result.stdout
    assert "migrate" in result.stdout
    assert "revision" in result.stdout


def test_demo_help() -> None:
    result = runner.invoke(cli.app, ["demo", "--help"])

    assert result.exit_code == 0
    assert "Demo data commands" in result.stdout
    assert "seed" in result.stdout
    assert "init" in result.stdout


def test_cli_dev_routes_to_existing_handler(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: list[str]) -> None:
        calls.append(cmd)

    monkeypatch.setattr(cli, "_run", fake_run)
    monkeypatch.setattr(cli, "_print_dev_banner", lambda: None)

    result = runner.invoke(cli.app, ["dev"])

    assert result.exit_code == 0
    assert calls == [
        [
            cli.sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--reload",
            "--host",
            cli.DEV_HOST,
            "--port",
            str(cli.DEV_PORT),
            "--no-access-log",
        ]
    ]


def test_db_commands_route_to_existing_handlers(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: list[str]) -> None:
        calls.append(cmd)

    monkeypatch.setattr(cli, "_run", fake_run)

    migrate_result = runner.invoke(cli.app, ["db", "migrate"])
    revision_result = runner.invoke(cli.app, ["db", "revision"])

    assert migrate_result.exit_code == 0
    assert revision_result.exit_code == 0
    assert calls == [
        [cli.sys.executable, "-m", "alembic", "upgrade", "head"],
        [cli.sys.executable, "-m", "alembic", "revision", "--autogenerate", "-m", "init"],
    ]


def test_demo_commands_route_to_existing_handlers(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: list[str]) -> None:
        calls.append(cmd)

    monkeypatch.setattr(cli, "_run", fake_run)

    seed_result = runner.invoke(cli.app, ["demo", "seed"])
    init_result = runner.invoke(cli.app, ["demo", "init"])

    assert seed_result.exit_code == 0
    assert init_result.exit_code == 0
    assert calls == [
        [cli.sys.executable, "scripts/seed_demo.py"],
        [cli.sys.executable, "-m", "alembic", "upgrade", "head"],
        [cli.sys.executable, "scripts/seed_demo.py"],
    ]


def test_demo_init_runs_migrate_and_seed(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: list[str]) -> None:
        calls.append(cmd)

    monkeypatch.setattr(cli, "_run", fake_run)

    cli.init_demo()

    assert calls == [
        [cli.sys.executable, "-m", "alembic", "upgrade", "head"],
        [cli.sys.executable, "scripts/seed_demo.py"],
    ]


def test_cli_run_exits_cleanly_on_keyboard_interrupt(monkeypatch) -> None:
    def fake_run(*args, **kwargs) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    with pytest.raises(SystemExit) as exc_info:
        cli._run(["python", "-V"])

    assert exc_info.value.code == 130
