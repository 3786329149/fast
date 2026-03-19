from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=ROOT, check=True)


def dev() -> None:
    _run([sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "5100"])


def worker() -> None:
    _run([sys.executable, "-m", "celery", "-A", "app.tasks.celery_app.celery_app", "worker", "--loglevel=INFO"])


def lint() -> None:
    _run([sys.executable, "-m", "ruff", "check", "app"])


def format_code() -> None:
    _run([sys.executable, "-m", "black", "app"])
    _run([sys.executable, "-m", "isort", "app"])


def test() -> None:
    _run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests", "app/tests"])


def migrate() -> None:
    _run([sys.executable, "-m", "alembic", "upgrade", "head"])


def revision() -> None:
    _run([sys.executable, "-m", "alembic", "revision", "--autogenerate", "-m", "init"])


def seed_demo() -> None:
    _run([sys.executable, "scripts/seed_demo.py"])


def init_demo() -> None:
    migrate()
    seed_demo()
    print("Init completed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Project development commands")
    parser.add_argument(
        "command",
        choices=[
            "dev",
            "worker",
            "lint",
            "format",
            "test",
            "migrate",
            "revision",
            "seed-demo",
            "init-demo",
        ],
    )
    args = parser.parse_args()

    handlers = {
        "dev": dev,
        "worker": worker,
        "lint": lint,
        "format": format_code,
        "test": test,
        "migrate": migrate,
        "revision": revision,
        "seed-demo": seed_demo,
        "init-demo": init_demo,
    }
    handlers[args.command]()


if __name__ == "__main__":
    main()
