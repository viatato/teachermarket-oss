from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import get_settings, validate_runtime_settings
from app.database import check_database_connection
from app.modules.admin.router import router as admin_router
from app.modules.auth.router import router as auth_router
from app.modules.contact_requests.router import router as contact_requests_router
from app.modules.files.router import router as files_router
from app.modules.favorites.router import router as favorites_router
from app.modules.products.router import router as products_router
from app.modules.reports.router import router as reports_router
from app.modules.reviews.router import router as reviews_router
from app.modules.sellers.router import router as sellers_router
from app.modules.subscriptions.router import router as subscriptions_router

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("X-Frame-Options", "DENY")
        return response


async def health() -> dict[str, object]:
    current_settings = get_settings()
    database_ok = await check_database_connection()
    return {
        "status": "ok" if database_ok else "degraded",
        "app": current_settings.app_name,
        "environment": current_settings.app_env,
        "database": "ok" if database_ok else "unavailable",
    }


def create_app() -> FastAPI:
    current_settings = get_settings()
    validate_runtime_settings(current_settings)
    is_production = current_settings.app_env == "production"
    app = FastAPI(
        title="ТічерМаркет API",
        description="Backend для Telegram-каталогу навчальних матеріалів.",
        version="0.1.0",
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
        openapi_url=None if is_production else "/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=current_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)

    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(sellers_router)
    app.include_router(files_router)
    app.include_router(products_router)
    app.include_router(reviews_router)
    app.include_router(reports_router)
    app.include_router(favorites_router)
    app.include_router(contact_requests_router)
    app.include_router(subscriptions_router)
    app.add_api_route("/health", health, methods=["GET"])
    return app


app = create_app()
