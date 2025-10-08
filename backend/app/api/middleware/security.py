"""Security middleware for request protection."""

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.cors import CORSMiddleware

from app.config import SecurityConfig
from app.infra.monitoring.logging.logger import logger

# Security headers
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}

# Max request size (10 MB)
MAX_REQUEST_SIZE = 10 * 1024 * 1024


def add_security_middleware(app: FastAPI, config: SecurityConfig) -> None:
    """
    Add security middleware to FastAPI application.

    Args:
        app: FastAPI application
        config: Security configuration
    """
    # Rate limiting
    if config.RATE_LIMIT_ENABLED:
        limiter = Limiter(key_func=get_remote_address, default_limits=[f"{config.RATE_LIMIT_PER_MINUTE}/minute"])
        app.state.limiter = limiter
        app.add_middleware(SlowAPIMiddleware)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_credentials=config.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security headers and request protection
    @app.middleware("http")
    async def security_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_SIZE:
            logger.warning(
                "Request too large",
                content_length=content_length,
                max_size=MAX_REQUEST_SIZE,
                path=request.url.path,
            )
            return JSONResponse(
                status_code=413,
                content={"detail": "Request entity too large"},
            )

        # Process request
        try:
            response = await call_next(request)

            # Add security headers
            for header, value in SECURITY_HEADERS.items():
                response.headers[header] = value

            return response

        except Exception as e:
            logger.exception(
                "Request processing failed",
                error=str(e),
                path=request.url.path,
                method=request.method,
            )
            raise


async def exception_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """
    Global exception handler middleware.

    Catches all unhandled exceptions and returns sanitized error responses.
    """
    try:
        return await call_next(request)

    except Exception as e:
        logger.error(
            "Unhandled exception",
            error=str(e),
            path=request.url.path,
            method=request.method,
            exc_info=True,
        )

        # Return sanitized error response
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "type": "internal_error",
            },
        )
