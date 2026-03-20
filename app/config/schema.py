from pydantic_settings import BaseSettings

from app.config.app import AppConfig, Environment
from app.config.cache import RedisConfig
from app.config.database import DatabaseConfig
from app.config.helpers import config_dict_for
from app.config.integrations import ProviderConfig, WechatConfig
from app.config.server import ServerConfig


class RuntimeConfig(
    AppConfig,
    ServerConfig,
    DatabaseConfig,
    RedisConfig,
    WechatConfig,
    ProviderConfig,
    BaseSettings,
):
    model_config = config_dict_for(Environment.LOCAL.value)


class LocalConfig(RuntimeConfig):
    APP_ENV: Environment = Environment.LOCAL

    model_config = config_dict_for(Environment.LOCAL.value)


class TestConfig(RuntimeConfig):
    APP_ENV: Environment = Environment.TEST
    APP_DEBUG: bool = False
    LOG_FORMAT: str | None = "json"

    model_config = config_dict_for(Environment.TEST.value)

    def model_post_init(self, __context) -> None:
        self.APP_DEBUG = False
        self.LOG_FORMAT = "json"


class ProdConfig(RuntimeConfig):
    APP_ENV: Environment = Environment.PROD
    APP_DEBUG: bool = False
    LOG_FORMAT: str | None = "json"

    model_config = config_dict_for(Environment.PROD.value)

    def model_post_init(self, __context) -> None:
        self.APP_DEBUG = False
        self.LOG_FORMAT = "json"


CONFIG_BY_ENV: dict[Environment, type[RuntimeConfig]] = {
    Environment.LOCAL: LocalConfig,
    Environment.TEST: TestConfig,
    Environment.PROD: ProdConfig,
}
