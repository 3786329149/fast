from pydantic import BaseModel

from app.core.config.types import Environment


class AppSettings(BaseModel):
    APP_NAME: str = "FastAPI Mall Enterprise Starter"
    APP_ENV: Environment = Environment.LOCAL
    APP_DEBUG: bool = True
    APP_VERSION: str = "0.1.0"
    APP_SECRET_KEY: str = "change-this-secret-key"
    APP_TIMEZONE: str = "Asia/Shanghai"
    APP_API_PREFIX: str = "/api"

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str | None = None
    SQL_ECHO: bool = False

    @property
    def IS_LOCAL_ENV(self) -> bool:
        return self.APP_ENV == Environment.LOCAL

    @property
    def IS_TEST_ENV(self) -> bool:
        return self.APP_ENV == Environment.TEST

    @property
    def IS_PROD_ENV(self) -> bool:
        return self.APP_ENV == Environment.PROD

    @property
    def RESOLVED_LOG_FORMAT(self) -> str:
        if self.LOG_FORMAT is not None:
            return self.LOG_FORMAT
        return "pretty" if self.IS_LOCAL_ENV else "json"
