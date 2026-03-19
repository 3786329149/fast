from functools import lru_cache
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    APP_NAME: str = "FastAPI Mall Enterprise Starter"
    APP_ENV: str = "local"
    APP_DEBUG: bool = True
    APP_VERSION: str = "0.1.0"
    APP_SECRET_KEY: str = "change-this-secret-key"
    APP_TIMEZONE: str = "Asia/Shanghai"
    APP_API_PREFIX: str = "/api"
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
    WECHAT_API_BASE_URL: str = 'https://api.weixin.qq.com'
    WECHAT_PAY_API_BASE_URL: str = 'https://api.mch.weixin.qq.com'
    WECHAT_MINIAPP_APPID: str = 'replace-me'
    WECHAT_MINIAPP_SECRET: str = 'replace-me'
    WECHAT_MCH_ID: str = 'replace-me'
    WECHAT_MCH_SERIAL_NO: str = ''
    WECHAT_MCH_API_V3_KEY: str = 'replace-me'
    WECHAT_MCH_PRIVATE_KEY_PATH: str = './certs/apiclient_key.pem'
    WECHAT_PAY_PLATFORM_PUBLIC_KEY_PATH: str = './certs/wechatpay_public_key.pem'
    WECHAT_NOTIFY_URL: str = 'https://example.com/api/open/v1/pay/wechat/callback'
    WECHAT_PAY_CURRENCY: str = 'CNY'
    WECHAT_HTTP_TIMEOUT_SECONDS: int = 8
    WECHAT_ACCESS_TOKEN_CACHE_SECONDS: int = 7000
    WECHAT_PAY_VERIFY_CALLBACK_SIGNATURE: bool = False

    SMS_PROVIDER: str = "mock"
    STORAGE_PROVIDER: str = "mock"
    PUSH_PROVIDER: str = "mock"

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

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
        """同步数据库 URL，用于 Alembic 迁移"""
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
        return self.APP_ENV.lower() in {"local", "dev", "development"}

    @property
    def RESOLVED_LOG_FORMAT(self) -> str:
        if self.LOG_FORMAT is not None:
            return self.LOG_FORMAT
        return "pretty" if self.IS_LOCAL_ENV else "json"

    @property
    def WECHAT_PAYMENT_ENABLED(self) -> bool:
        return not self.WECHAT_API_MOCK and all(
            [
                self.WECHAT_MINIAPP_APPID != 'replace-me',
                self.WECHAT_MCH_ID != 'replace-me',
                self.WECHAT_MCH_API_V3_KEY != 'replace-me',
                bool(self.WECHAT_MCH_SERIAL_NO),
            ]
        )

@lru_cache
def get_settings() -> Settings:
    return Settings()
