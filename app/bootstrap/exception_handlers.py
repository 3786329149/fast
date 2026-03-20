import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException
from app.core.response import failure

logger = structlog.get_logger("app.exception")


def _request_log_context(request: Request) -> dict[str, object]:
    return {
        "request_id": getattr(request.state, "request_id", None),
        "method": request.method,
        "path": request.url.path,
        "client_ip": request.client.host if request.client is not None else None,
    }


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    logger.info(
        "http_exception",
        status_code=exc.status_code,
        detail=exc.detail,
        **_request_log_context(request),
    )
    return JSONResponse(status_code=exc.status_code, content=failure(message=str(exc.detail), code=exc.status_code))


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.info(
        "app_exception",
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        **_request_log_context(request),
    )
    return JSONResponse(status_code=exc.status_code, content=failure(message=exc.message, code=exc.code, data=exc.data))


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.info(
        "validation_exception",
        errors=exc.errors(),
        **_request_log_context(request),
    )
    return JSONResponse(status_code=422, content=failure(message='参数校验失败', code=422, data=exc.errors()))


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception", **_request_log_context(request))
    return JSONResponse(status_code=500, content=failure(message='服务器内部错误', code=500))


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
