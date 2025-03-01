import ipaddress
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Callable, List, Optional, Set

from cryptography.fernet import Fernet
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.datastructures import MutableHeaders
from starlette.middleware.base import BaseHTTPMiddleware

from .monitoring import monitor_requests


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        headers = MutableHeaders(response.headers)

        # Security Headers
        headers["X-Content-Type-Options"] = "nosniff"
        headers["X-Frame-Options"] = "DENY"
        headers["X-XSS-Protection"] = "1; mode=block"
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
        )
        headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
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


class EncryptionMiddleware:
    def __init__(self):
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            raise ValueError("ENCRYPTION_KEY environment variable not set")
        self.fernet = Fernet(key.encode())

    def encrypt(self, data: str) -> str:
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, data: str) -> str:
        return self.fernet.decrypt(data.encode()).decode()


def setup_security_middleware(app: FastAPI):
    """Configure security middleware for the application."""

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Trusted Host middleware
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])

    # Gzip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Request monitoring
    app.middleware("http")(monitor_requests)


# Usage example:
# from middleware.security import setup_security_middleware, EncryptionMiddleware
#
# app = FastAPI()
# setup_security_middleware(app)
# encryption = EncryptionMiddleware()
#
# @app.post("/api/secure-endpoint")
# async def secure_endpoint(data: str):
#     encrypted_data = encryption.encrypt(data)
#     # Store encrypted_data in database
#     return {"status": "success"}

# Load environment variables
ALLOWED_IPS = os.getenv("ALLOWED_ADMIN_IPS", "").split(",")
MAX_REQUEST_SIZE = int(os.getenv("MAX_REQUEST_SIZE_BYTES", 1024 * 1024))  # Default 1MB
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", 100))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", 60))  # seconds


@lru_cache()
def get_allowed_ips() -> Set[ipaddress.IPv4Network]:
    """Convert string IP addresses to IPv4Network objects."""
    allowed = set()
    for ip in ALLOWED_IPS:
        try:
            if "/" in ip:
                allowed.add(ipaddress.IPv4Network(ip.strip()))
            else:
                allowed.add(ipaddress.IPv4Network(f"{ip.strip()}/32"))
        except ValueError:
            continue
    return allowed


def is_ip_allowed(ip: str) -> bool:
    """Check if an IP is in the allowed list."""
    if not ALLOWED_IPS:  # If no IPs specified, allow all
        return True

    try:
        client_ip = ipaddress.IPv4Address(ip)
        return any(client_ip in network for network in get_allowed_ips())
    except ValueError:
        return False


async def security_middleware(request: Request, call_next):
    """Main security middleware."""
    # Check request size
    if request.headers.get("content-length"):
        content_length = int(request.headers["content-length"])
        if content_length > MAX_REQUEST_SIZE:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "Request too large"},
            )

    # IP allowlisting for admin endpoints
    if request.url.path.startswith("/admin"):
        client_ip = request.client.host
        if not is_ip_allowed(client_ip):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "IP not allowed"},
            )

    # Add security headers
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' https:;"
    )

    return response


# Rate limiting implementation
class RateLimiter:
    def __init__(self, requests: int, window: int):
        self.requests = requests
        self.window = window
        self.clients = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        now = datetime.now()
        self.clients[client_ip] = [
            timestamp
            for timestamp in self.clients[client_ip]
            if timestamp > now - timedelta(seconds=self.window)
        ]

        if len(self.clients[client_ip]) >= self.requests:
            return False

        self.clients[client_ip].append(now)
        return True


rate_limiter = RateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW)


async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware."""
    client_ip = request.client.host

    if not rate_limiter.is_allowed(client_ip):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many requests"},
        )

    return await call_next(request)


# WAF-like rules
async def waf_middleware(request: Request, call_next):
    """Basic WAF-like protection."""
    # Check for common SQL injection patterns
    path = request.url.path.lower()
    query = str(request.query_params).lower()

    sql_patterns = ["union", "select", "drop", "delete", "--", ";", "' or '1'='1"]
    xss_patterns = ["<script>", "javascript:", "onerror=", "onload="]

    for pattern in sql_patterns:
        if pattern in path or pattern in query:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Potential SQL injection detected"},
            )

    for pattern in xss_patterns:
        if pattern in path or pattern in query:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Potential XSS attack detected"},
            )

    return await call_next(request)
