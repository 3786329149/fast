from fastapi import FastAPI

from app.api.admin.v1.router import router as admin_router
from app.api.client.v1.router import router as client_router
from app.api.open.v1.router import router as open_router
from app.api.wechat.v1.router import router as wechat_router
from app.bootstrap.exception_handlers import register_exception_handlers
from app.bootstrap.lifespan import lifespan
from app.bootstrap.middleware import register_middlewares
from app.core.config import get_settings
from app.core.response import success


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.APP_DEBUG,
        lifespan=lifespan,
        docs_url='/docs',
        redoc_url='/redoc',
        openapi_url='/openapi.json',
    )

    register_middlewares(app)
    register_exception_handlers(app)

    @app.get('/')
    async def root() -> dict:
        return success(
            {
                'name': settings.APP_NAME,
                'version': settings.APP_VERSION,
                'env': settings.APP_ENV,
            }
        )

    @app.get('/healthz')
    async def healthz() -> dict:
        return success({'status': 'ok'})

    app.include_router(admin_router, prefix='/api/admin/v1')
    app.include_router(client_router, prefix='/api/client/v1')
    app.include_router(wechat_router, prefix='/api/wechat/v1')
    app.include_router(open_router, prefix='/api/open/v1')
    return app


app = create_app()
