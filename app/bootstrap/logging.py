from __future__ import annotations

import logging.config
import sys
from typing import Any

import structlog

from app.config import get_config


def add_service_metadata(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    config = get_config()
    event_dict.setdefault("env", config.APP_ENV)
    event_dict.setdefault("service", config.APP_NAME)
    event_dict.setdefault("version", config.APP_VERSION)
    return event_dict


def drop_color_message(_: Any, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    event_dict.pop("color_message", None)
    return event_dict


def build_renderer(log_format: str) -> Any:
    if log_format == "json":
        return structlog.processors.JSONRenderer()
    return structlog.dev.ConsoleRenderer(
        colors=True,
        pad_event=0,
        pad_level=False,
    )


def configure_logging() -> None:
    config = get_config()
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
        add_service_metadata,
    ]
    renderer = build_renderer(config.RESOLVED_LOG_FORMAT)
    level = config.LOG_LEVEL.upper()

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "structured": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "foreign_pre_chain": shared_processors,
                    "processors": [
                        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                        drop_color_message,
                        renderer,
                    ],
                }
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "structured",
                    "stream": sys.stdout,
                },
                "null": {
                    "class": "logging.NullHandler",
                },
            },
            "root": {
                "handlers": ["default"],
                "level": level,
            },
            "loggers": {
                "uvicorn": {
                    "handlers": ["default"],
                    "level": level,
                    "propagate": False,
                },
                "uvicorn.error": {
                    "handlers": ["default"],
                    "level": level,
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": ["null"],
                    "level": level,
                    "propagate": False,
                },
            },
        }
    )

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
