import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from loguru import logger
from starlette.datastructures import MutableHeaders
from starlette.middleware.base import BaseHTTPMiddleware

from .metrics import REQUEST_COUNT, REQUEST_LATENCY


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        headers = MutableHeaders(response.headers)

        # Security Headers
        headers["X-Content-Type-Options"] = "nosniff"
        headers["X-Frame-Options"] = "DENY"
        headers["X-XSS-Protection"] = "1; mode=block"
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval';"
        )
        headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        return response


class RequestMonitoringMiddleware(BaseHTTPMiddleware):
    """Monitor request metrics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        try:
            response = await call_next(request)
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code,
            ).inc()
        except Exception as e:
            REQUEST_COUNT.labels(
                method=request.method, endpoint=request.url.path, status=500
            ).inc()
            raise e
        finally:
            REQUEST_LATENCY.labels(
                method=request.method, endpoint=request.url.path
            ).observe(time.time() - start_time)

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limit requests by client IP."""

    def __init__(self, app: FastAPI, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host
        current_time = time.time()

        # Clean old requests
        self.requests = {
            ip: reqs
            for ip, reqs in self.requests.items()
            if current_time - reqs[-1] < 60
        }

        # Check rate limit
        if client_ip in self.requests:
            if len(self.requests[client_ip]) >= self.requests_per_minute:
                if current_time - self.requests[client_ip][0] < 60:
                    return Response(content="Rate limit exceeded", status_code=429)
                self.requests[client_ip] = self.requests[client_ip][1:]
            self.requests[client_ip].append(current_time)
        else:
            self.requests[client_ip] = [current_time]

        return await call_next(request)


def setup_middleware(app: FastAPI):
    """Configure all middleware for the application."""

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "https://justmaily.com", "https://app.justmaily.com", "https://staging.justmaily.com"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Trusted Host middleware
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])

    # Gzip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Request monitoring
    app.add_middleware(RequestMonitoringMiddleware)

    # Rate limiting
    app.add_middleware(RateLimitMiddleware, requests_per_minute=100)

    logger.info("All middleware configured successfully")
