from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any


ACTIVE_STATUS = 'active'
INACTIVE_STATUS = 'inactive'
DRAFT_STATUS = 'draft'


def active_to_int(value: str | None) -> int:
    return 0 if value == INACTIVE_STATUS else 1


def int_to_active(value: int | None) -> str:
    return INACTIVE_STATUS if int(value or 0) == 0 else ACTIVE_STATUS


def product_status_to_int(value: str | None) -> int:
    if value == DRAFT_STATUS:
        return 2
    if value == INACTIVE_STATUS:
        return 0
    return 1


def int_to_product_status(value: int | None) -> str:
    if int(value or 0) == 2:
        return DRAFT_STATUS
    return int_to_active(value)


def decimal_to_float(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def dt_to_iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def date_to_iso(value: date | None) -> str | None:
    return value.isoformat() if value else None


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def unique_ordered(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def pick_truthy(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value not in (None, '', [], {})}
