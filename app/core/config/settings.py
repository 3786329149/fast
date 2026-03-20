from pydantic_settings import BaseSettings

from app.core.config.app import AppSettings
from app.core.config.helpers import settings_config_for
from app.core.config.integrations import ProviderSettings, WechatSettings
from app.core.config.server import ServerSettings
from app.core.config.storage import DatabaseSettings, RedisSettings
from app.core.config.types import Environment


class Settings(
    AppSettings,
    ServerSettings,
    DatabaseSettings,
    RedisSettings,
    WechatSettings,
    ProviderSettings,
    BaseSettings,
):
    model_config = settings_config_for(Environment.LOCAL.value)


class LocalSettings(Settings):
    APP_ENV: Environment = Environment.LOCAL

    model_config = settings_config_for(Environment.LOCAL.value)


class TestSettings(Settings):
    APP_ENV: Environment = Environment.TEST
    APP_DEBUG: bool = False
    LOG_FORMAT: str | None = "json"

    model_config = settings_config_for(Environment.TEST.value)

    def model_post_init(self, __context) -> None:
        self.APP_DEBUG = False
        self.LOG_FORMAT = "json"


class ProdSettings(Settings):
    APP_ENV: Environment = Environment.PROD
    APP_DEBUG: bool = False
    LOG_FORMAT: str | None = "json"

    model_config = settings_config_for(Environment.PROD.value)

    def model_post_init(self, __context) -> None:
        self.APP_DEBUG = False
        self.LOG_FORMAT = "json"


SETTINGS_BY_ENV: dict[Environment, type[Settings]] = {
    Environment.LOCAL: LocalSettings,
    Environment.TEST: TestSettings,
    Environment.PROD: ProdSettings,
}
