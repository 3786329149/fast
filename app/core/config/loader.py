import os
from functools import lru_cache

from app.core.config.helpers import BASE_ENV_FILE, read_env_value
from app.core.config.settings import ProdSettings, Settings, SETTINGS_BY_ENV, TestSettings
from app.core.config.types import Environment


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
def get_settings() -> Settings:
    env_name = resolve_app_env()
    settings_cls = SETTINGS_BY_ENV[env_name]
    settings = settings_cls(APP_ENV=env_name)
    if isinstance(settings, (TestSettings, ProdSettings)):
        settings.APP_DEBUG = False
        settings.LOG_FORMAT = "json"
    return settings
