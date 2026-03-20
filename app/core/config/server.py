from pydantic import BaseModel

from app.core.config.helpers import split_csv


class ServerSettings(BaseModel):
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 5100

    CORS_ALLOW_ORIGINS: str = ""
    CORS_ALLOW_METHODS: str = "*"
    CORS_ALLOW_HEADERS: str = "*"
    CORS_ALLOW_CREDENTIALS: bool = False

    @property
    def CORS_ORIGINS_LIST(self) -> list[str]:
        return split_csv(self.CORS_ALLOW_ORIGINS)

    @property
    def CORS_METHODS_LIST(self) -> list[str]:
        methods = split_csv(self.CORS_ALLOW_METHODS)
        return methods or ["*"]

    @property
    def CORS_HEADERS_LIST(self) -> list[str]:
        headers = split_csv(self.CORS_ALLOW_HEADERS)
        return headers or ["*"]

    @property
    def CORS_ENABLED(self) -> bool:
        return bool(self.CORS_ORIGINS_LIST)
