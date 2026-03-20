from __future__ import annotations

import pytest

from app.core.config import loader
from app.core.config.settings import ProdSettings
from app.core.config.types import Environment


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


def test_get_settings_selects_prod_settings(monkeypatch) -> None:
    loader.get_settings.cache_clear()
    monkeypatch.setattr(loader, "resolve_app_env", lambda: Environment.PROD)

    settings = loader.get_settings()

    assert isinstance(settings, ProdSettings)
    assert settings.APP_ENV == Environment.PROD
    assert settings.APP_DEBUG is False
    assert settings.RESOLVED_LOG_FORMAT == "json"

    loader.get_settings.cache_clear()
