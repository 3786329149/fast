from __future__ import annotations

from typing import Any


class AppException(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: int | None = None,
        status_code: int = 400,
        data: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = status_code if code is None else code
        self.status_code = status_code
        self.data = data
