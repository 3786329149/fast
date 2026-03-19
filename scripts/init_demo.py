from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> None:
    alembic_cmd = shutil.which("alembic")
    if not alembic_cmd:
        raise SystemExit(
            "Init failed: 未找到 `alembic` 命令。请先安装依赖并确认当前环境可执行 Alembic。"
        )

    run([alembic_cmd, "upgrade", "head"])
    run([sys.executable, "scripts/seed_demo.py"])
    print("Init completed.")


if __name__ == "__main__":
    main()
