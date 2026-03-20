import os
from functools import lru_cache

from app.config.app import Environment
from app.config.helpers import BASE_ENV_FILE, read_env_value
from app.config.schema import CONFIG_BY_ENV, ProdConfig, RuntimeConfig, TestConfig


APP_ENV_ALIASES = {
    "local": Environment.LOCAL,
    "dev": Environment.LOCAL,
    "development": Environment.LOCAL,
    "test": Environment.TEST,
    "testing": Environment.TEST,
    "prod": Environment.PROD,
    "production": Environment.PROD,
}


def normalize_app_env(value: str) -> Environment:
    normalized = APP_ENV_ALIASES.get(value.strip().lower())
    if normalized is None:
        allowed = ", ".join(sorted(APP_ENV_ALIASES))
        raise ValueError(f"Unsupported APP_ENV={value!r}. Expected one of: {allowed}")
    return normalized


def resolve_app_env() -> Environment:
    raw_env = os.getenv("APP_ENV") or read_env_value(BASE_ENV_FILE, "APP_ENV") or Environment.LOCAL.value
    return normalize_app_env(raw_env)


@lru_cache
def get_config() -> RuntimeConfig:
    env_name = resolve_app_env()
    config_cls = CONFIG_BY_ENV[env_name]
    config = config_cls(APP_ENV=env_name)
    if isinstance(config, (TestConfig, ProdConfig)):
        config.APP_DEBUG = False
        config.LOG_FORMAT = "json"
    return config
