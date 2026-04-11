import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.limiter import limiter
from app.logging import configure_logging
from app.api.router import api_router

configure_logging(settings.environment)
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("medivault_api_starting", environment=settings.environment)
    yield
    logger.info("medivault_api_shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="MediVault API",
        version="1.0.0",
        docs_url="/docs" if settings.environment == "development" else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate-limit sensitive paths via middleware (NFR-SEC-007).
    # Using middleware avoids decorator/annotation conflicts with FastAPI.
    _RATE_LIMITS = {
        "/api/v1/documents/upload": ("20/minute", {}),
        "/api/v1/auth/provision": ("10/minute", {}),
        "/api/v1/auth/account": ("5/hour", {}),
    }

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        path = request.url.path
        if path in _RATE_LIMITS:
            limit_string, _ = _RATE_LIMITS[path]
            from limits import parse  # noqa: PLC0415
            from limits.storage import MemoryStorage  # noqa: PLC0415
            from limits.strategies import FixedWindowRateLimiter  # noqa: PLC0415
            storage = getattr(app.state, "_rl_storage", None)
            if storage is None:
                app.state._rl_storage = MemoryStorage()
                storage = app.state._rl_storage
            strategy = FixedWindowRateLimiter(storage)
            client_ip = request.client.host if request.client else "unknown"
            item = parse(limit_string)
            if not strategy.hit(item, client_ip, path):
                return JSONResponse(
                    status_code=429,
                    content={"error": "RATE_LIMIT_EXCEEDED", "message": "Too many requests."},
                    headers={"Retry-After": "60"},
                )
        return await call_next(request)

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.error("unhandled_exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred."},
        )

    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
