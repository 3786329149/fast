from pathlib import Path

from pydantic_settings import SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BASE_ENV_FILE = PROJECT_ROOT / ".env"


def split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def env_file_name(env_name: str) -> str:
    return f".env.{env_name}"


def env_file_chain(env_name: str) -> tuple[str, ...]:
    return (str(BASE_ENV_FILE), str(PROJECT_ROOT / env_file_name(env_name)))


def settings_config_for(env_name: str) -> SettingsConfigDict:
    return SettingsConfigDict(
        env_file=env_file_chain(env_name),
        env_file_encoding="utf-8",
        extra="ignore",
    )


def read_env_value(path: Path, key: str) -> str | None:
    if not path.exists():
        return None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        if "=" not in line:
            continue
        current_key, value = line.split("=", 1)
        if current_key.strip() != key:
            continue
        return value.strip().strip("\"'")

    return None
