from __future__ import annotations

import pytest

from app.core import config


def test_resolve_app_env_prefers_process_env(monkeypatch) -> None:
    monkeypatch.setattr(config, "_read_env_value", lambda path, key: "prod")
    monkeypatch.setenv("APP_ENV", "test")

    assert config.resolve_app_env() == "test"


def test_resolve_app_env_reads_base_env_file(monkeypatch) -> None:
    monkeypatch.setattr(config, "_read_env_value", lambda path, key: "development")
    monkeypatch.delenv("APP_ENV", raising=False)

    assert config.resolve_app_env() == "local"


def test_normalize_app_env_rejects_unknown_value() -> None:
    with pytest.raises(ValueError, match="Unsupported APP_ENV"):
        config.normalize_app_env("staging")


def test_get_settings_selects_prod_settings(monkeypatch) -> None:
    config.get_settings.cache_clear()
    monkeypatch.setattr(config, "resolve_app_env", lambda: "prod")

    settings = config.get_settings()

    assert isinstance(settings, config.ProdSettings)
    assert settings.APP_ENV == "prod"
    assert settings.APP_DEBUG is False
    assert settings.RESOLVED_LOG_FORMAT == "json"

    config.get_settings.cache_clear()
