from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

import typer

from app.bootstrap.app import create_app
from app.bootstrap.diagnostics import run_startup_diagnostics
from app.bootstrap.logging import configure_logging
from app.config import get_config


ROOT = Path(__file__).resolve().parents[1]

app = typer.Typer(
    help="Project development commands",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)
db_app = typer.Typer(help="Database commands", no_args_is_help=True)
demo_app = typer.Typer(help="Demo data commands", no_args_is_help=True)
app.add_typer(db_app, name="db")
app.add_typer(demo_app, name="demo")


def _run(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}")
    try:
        subprocess.run(cmd, cwd=ROOT, check=True)
    except KeyboardInterrupt as exc:
        print("\nInterrupted.")
        raise SystemExit(130) from exc


def _dev_display_host(host: str) -> str:
    return "127.0.0.1" if host in {"0.0.0.0", "::"} else host


def _print_dev_banner() -> None:
    config = get_config()
    base_url = f"http://{_dev_display_host(config.SERVER_HOST)}:{config.SERVER_PORT}"
    print(f"App: {config.APP_NAME}")
    print(f"Env: {config.APP_ENV}")
    print(f"Bind: {config.SERVER_HOST}:{config.SERVER_PORT}")
    print(f"Docs: {base_url}/docs")
    print(f"ReDoc: {base_url}/redoc")
    print(f"Health: {base_url}/healthz")
    print(f"Ready: {base_url}/readyz")


@app.command()
def dev() -> None:
    config = get_config()
    _print_dev_banner()
    _run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--reload",
            "--host",
            config.SERVER_HOST,
            "--port",
            str(config.SERVER_PORT),
            "--no-access-log",
        ]
    )


@app.command()
def worker() -> None:
    _run([sys.executable, "-m", "celery", "-A", "app.tasks.celery_app.celery_app", "worker", "--loglevel=INFO"])


@app.command()
def lint() -> None:
    _run([sys.executable, "-m", "ruff", "check", "app"])


@app.command("format")
def format_code() -> None:
    _run([sys.executable, "-m", "black", "app"])
    _run([sys.executable, "-m", "isort", "app"])


@app.command("test")
def test_command() -> None:
    _run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests", "app/tests"])


@db_app.command("migrate")
def migrate() -> None:
    _run([sys.executable, "-m", "alembic", "upgrade", "head"])


@db_app.command("revision")
def revision() -> None:
    _run([sys.executable, "-m", "alembic", "revision", "--autogenerate", "-m", "init"])


@demo_app.command("seed")
def seed_demo() -> None:
    _run([sys.executable, "scripts/seed_demo.py"])


@demo_app.command("init")
def init_demo() -> None:
    migrate()
    seed_demo()
    print("Init completed.")


@app.command()
def doctor() -> None:
    configure_logging()
    fastapi_app = create_app()
    try:
        diagnostics = asyncio.run(run_startup_diagnostics(fastapi_app, keep_redis_client=False))
    except Exception as exc:
        print(f"Doctor failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    print("Doctor completed.")
    print(f"Database: ok ({diagnostics['database']['latency_ms']} ms)")
    print(f"Redis: ok ({diagnostics['redis']['latency_ms']} ms)")
    print(f"Tables: {diagnostics['tables']['count']}")
    print(f"Routes: {diagnostics['routes']['count']}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
