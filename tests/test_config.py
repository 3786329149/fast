from __future__ import annotations

import pytest

from app.config import loader
from app.config.app import Environment
from app.config.schema import ProdConfig


def test_resolve_app_env_prefers_process_env(monkeypatch) -> None:
    monkeypatch.setattr(loader, "read_env_value", lambda path, key: "prod")
    monkeypatch.setenv("APP_ENV", "test")

    assert loader.resolve_app_env() == Environment.TEST


def test_resolve_app_env_reads_base_env_file(monkeypatch) -> None:
    monkeypatch.setattr(loader, "read_env_value", lambda path, key: "development")
    monkeypatch.delenv("APP_ENV", raising=False)

    assert loader.resolve_app_env() == Environment.LOCAL


def test_normalize_app_env_rejects_unknown_value() -> None:
    with pytest.raises(ValueError, match="Unsupported APP_ENV"):
        loader.normalize_app_env("staging")


def test_get_config_selects_prod_config(monkeypatch) -> None:
    loader.get_config.cache_clear()
    monkeypatch.setattr(loader, "resolve_app_env", lambda: Environment.PROD)

    config = loader.get_config()

    assert isinstance(config, ProdConfig)
    assert config.APP_ENV == Environment.PROD
    assert config.APP_DEBUG is False
    assert config.RESOLVED_LOG_FORMAT == "json"

    loader.get_config.cache_clear()
