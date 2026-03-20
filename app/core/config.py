import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASE_ENV_FILE = PROJECT_ROOT / ".env"
APP_ENV_ALIASES = {
    "local": "local",
    "dev": "local",
    "development": "local",
    "test": "test",
    "testing": "test",
    "prod": "prod",
    "production": "prod",
}


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _env_file_name(env_name: str) -> str:
    return f".env.{env_name}"


def _env_file_chain(env_name: str) -> tuple[str, ...]:
    return (str(BASE_ENV_FILE), str(PROJECT_ROOT / _env_file_name(env_name)))


def _settings_config_for(env_name: str) -> SettingsConfigDict:
    return SettingsConfigDict(
        env_file=_env_file_chain(env_name),
        env_file_encoding="utf-8",
        extra="ignore",
    )


def _read_env_value(path: Path, key: str) -> str | None:
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


def normalize_app_env(value: str) -> str:
    normalized = APP_ENV_ALIASES.get(value.strip().lower())
    if normalized is None:
        allowed = ", ".join(sorted(APP_ENV_ALIASES))
        raise ValueError(f"Unsupported APP_ENV={value!r}. Expected one of: {allowed}")
    return normalized


def resolve_app_env() -> str:
    raw_env = os.getenv("APP_ENV") or _read_env_value(BASE_ENV_FILE, "APP_ENV") or "local"
    return normalize_app_env(raw_env)


class Settings(BaseSettings):
    APP_NAME: str = "FastAPI Mall Enterprise Starter"
    APP_ENV: str = "local"
    APP_DEBUG: bool = True
    APP_VERSION: str = "0.1.0"
    APP_SECRET_KEY: str = "change-this-secret-key"
    APP_TIMEZONE: str = "Asia/Shanghai"
    APP_API_PREFIX: str = "/api"

    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 5100

    CORS_ALLOW_ORIGINS: str = ""
    CORS_ALLOW_METHODS: str = "*"
    CORS_ALLOW_HEADERS: str = "*"
    CORS_ALLOW_CREDENTIALS: bool = False

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: Literal["pretty", "json"] | None = None
    SQL_ECHO: bool = False

    DATABASE_URL_OVERRIDE: str | None = None

    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "mall_enterprise"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"

    REDIS_URL_OVERRIDE: str | None = None
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    WECHAT_API_MOCK: bool = True
    WECHAT_API_BASE_URL: str = "https://api.weixin.qq.com"
    WECHAT_PAY_API_BASE_URL: str = "https://api.mch.weixin.qq.com"
    WECHAT_MINIAPP_APPID: str = "replace-me"
    WECHAT_MINIAPP_SECRET: str = "replace-me"
    WECHAT_MCH_ID: str = "replace-me"
    WECHAT_MCH_SERIAL_NO: str = ""
    WECHAT_MCH_API_V3_KEY: str = "replace-me"
    WECHAT_MCH_PRIVATE_KEY_PATH: str = "./certs/apiclient_key.pem"
    WECHAT_PAY_PLATFORM_PUBLIC_KEY_PATH: str = "./certs/wechatpay_public_key.pem"
    WECHAT_NOTIFY_URL: str = "https://example.com/api/open/v1/pay/wechat/callback"
    WECHAT_PAY_CURRENCY: str = "CNY"
    WECHAT_HTTP_TIMEOUT_SECONDS: int = 8
    WECHAT_ACCESS_TOKEN_CACHE_SECONDS: int = 7000
    WECHAT_PAY_VERIFY_CALLBACK_SIGNATURE: bool = False

    SMS_PROVIDER: str = "mock"
    STORAGE_PROVIDER: str = "mock"
    PUSH_PROVIDER: str = "mock"

    model_config = _settings_config_for("local")

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        if self.DATABASE_URL_OVERRIDE:
            return self.DATABASE_URL_OVERRIDE
        return URL.create(
            "postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        ).render_as_string(hide_password=False)

    @computed_field
    @property
    def DATABASE_SYNC_URL(self) -> str:
        return URL.create(
            "postgresql+psycopg2",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        ).render_as_string(hide_password=False)

    @computed_field
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_URL_OVERRIDE:
            return self.REDIS_URL_OVERRIDE
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def IS_LOCAL_ENV(self) -> bool:
        return self.APP_ENV == "local"

    @property
    def IS_TEST_ENV(self) -> bool:
        return self.APP_ENV == "test"

    @property
    def IS_PROD_ENV(self) -> bool:
        return self.APP_ENV == "prod"

    @property
    def RESOLVED_LOG_FORMAT(self) -> str:
        if self.LOG_FORMAT is not None:
            return self.LOG_FORMAT
        return "pretty" if self.IS_LOCAL_ENV else "json"

    @property
    def CORS_ORIGINS_LIST(self) -> list[str]:
        return _split_csv(self.CORS_ALLOW_ORIGINS)

    @property
    def CORS_METHODS_LIST(self) -> list[str]:
        methods = _split_csv(self.CORS_ALLOW_METHODS)
        return methods or ["*"]

    @property
    def CORS_HEADERS_LIST(self) -> list[str]:
        headers = _split_csv(self.CORS_ALLOW_HEADERS)
        return headers or ["*"]

    @property
    def CORS_ENABLED(self) -> bool:
        return bool(self.CORS_ORIGINS_LIST)

    @property
    def WECHAT_PAYMENT_ENABLED(self) -> bool:
        return not self.WECHAT_API_MOCK and all(
            [
                self.WECHAT_MINIAPP_APPID != "replace-me",
                self.WECHAT_MCH_ID != "replace-me",
                self.WECHAT_MCH_API_V3_KEY != "replace-me",
                bool(self.WECHAT_MCH_SERIAL_NO),
            ]
        )


class LocalSettings(Settings):
    APP_ENV: str = "local"

    model_config = _settings_config_for("local")


class TestSettings(Settings):
    APP_ENV: str = "test"
    APP_DEBUG: bool = False
    LOG_FORMAT: Literal["pretty", "json"] | None = "json"

    model_config = _settings_config_for("test")

    def model_post_init(self, __context) -> None:
        self.APP_DEBUG = False
        self.LOG_FORMAT = "json"


class ProdSettings(Settings):
    APP_ENV: str = "prod"
    APP_DEBUG: bool = False
    LOG_FORMAT: Literal["pretty", "json"] | None = "json"

    model_config = _settings_config_for("prod")

    def model_post_init(self, __context) -> None:
        self.APP_DEBUG = False
        self.LOG_FORMAT = "json"


SETTINGS_BY_ENV: dict[str, type[Settings]] = {
    "local": LocalSettings,
    "test": TestSettings,
    "prod": ProdSettings,
}


@lru_cache
def get_settings() -> Settings:
    env_name = resolve_app_env()
    settings_cls = SETTINGS_BY_ENV[env_name]
    return settings_cls(APP_ENV=env_name)
