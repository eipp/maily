"""
Enhanced Security Headers Middleware

Provides middleware for adding comprehensive security headers to all API responses,
implementing protection against common web vulnerabilities.
"""

import time
import logging
import ipaddress
from typing import List, Dict, Any, Optional, Callable, Union
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import re

logger = logging.getLogger(__name__)

class SecurityConfig:
    """Configuration for security middleware."""

    def __init__(
        self,
        # Content Security Policy settings
        csp_enabled: bool = True,
        csp_report_only: bool = False,
        csp_report_uri: Optional[str] = None,

        # Rate limiting settings
        rate_limiting_enabled: bool = True,
        rate_limit_requests: int = 100,
        rate_limit_window: int = 60,  # seconds

        # Request size validation
        max_content_length: int = 10 * 1024 * 1024,  # 10 MB

        # IP allowlisting for admin endpoints
        admin_ip_allowlist: List[str] = None,
        admin_path_pattern: str = r"^/admin|^/v1/admin",

        # Security event logging
        log_security_events: bool = True,

        # Additional custom headers
        custom_headers: Dict[str, str] = None
    ):
        """Initialize security configuration."""
        # CSP settings
        self.csp_enabled = csp_enabled
        self.csp_report_only = csp_report_only
        self.csp_report_uri = csp_report_uri

        # Rate limiting settings
        self.rate_limiting_enabled = rate_limiting_enabled
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_window = rate_limit_window

        # Request size validation
        self.max_content_length = max_content_length

        # IP allowlisting
        self.admin_ip_allowlist = admin_ip_allowlist or []
        self.admin_path_pattern = re.compile(admin_path_pattern)

        # Security event logging
        self.log_security_events = log_security_events

        # Custom headers
        self.custom_headers = custom_headers or {}


class EnhancedSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all responses.

    Features:
    - Comprehensive security headers (CSP, HSTS, etc.)
    - Request size validation to prevent DoS attacks
    - Rate limiting to prevent brute force attempts
    - IP allowlisting for admin endpoints
    - Security event logging
    """

    def __init__(
        self,
        app: ASGIApp,
        config: Optional[SecurityConfig] = None,
        exclude_paths: List[str] = None,
    ):
        """
        Initialize the middleware.

        Args:
            app: ASGI application
            config: Security configuration
            exclude_paths: List of paths to exclude from security headers
        """
        super().__init__(app)
        self.config = config or SecurityConfig()
        self.exclude_paths = exclude_paths or ["/docs", "/redoc", "/openapi.json"]

        # Initialize rate limiting storage
        self.rate_limit_store: Dict[str, List[float]] = {}

        # Compile path exclusion patterns
        self.exclude_patterns = [re.compile(f"^{re.escape(path)}") for path in self.exclude_paths]

        logger.info("Enhanced Security Headers Middleware initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and add security headers to the response.

        Args:
            request: Request object
            call_next: Function to call the next middleware/route handler

        Returns:
            Response with added security headers
        """
        # Skip middleware for excluded paths
        path = request.url.path
        if any(pattern.match(path) for pattern in self.exclude_patterns):
            return await call_next(request)

        # Get client IP
        client_ip = self._get_client_ip(request)

        # Check for admin endpoint access restrictions
        if self.config.admin_path_pattern.match(path):
            if not self._is_ip_allowed(client_ip):
                if self.config.log_security_events:
                    logger.warning(
                        f"Unauthorized admin access attempt: {path} from {client_ip}",
                        extra={"security_event": "admin_access_denied", "ip": client_ip, "path": path}
                    )
                return Response(
                    content='{"error": "Unauthorized", "detail": "IP not allowed"}',
                    status_code=403,
                    media_type="application/json"
                )

        # Check content length for POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.config.max_content_length:
                if self.config.log_security_events:
                    logger.warning(
                        f"Request size exceeded limit: {content_length} bytes from {client_ip}",
                        extra={"security_event": "request_size_limit", "ip": client_ip, "size": content_length}
                    )
                return Response(
                    content='{"error": "Request Entity Too Large", "detail": "Request exceeds size limit"}',
                    status_code=413,
                    media_type="application/json"
                )

        # Apply rate limiting if enabled
        if self.config.rate_limiting_enabled and request.method != "OPTIONS":
            if not self._check_rate_limit(client_ip):
                if self.config.log_security_events:
                    logger.warning(
                        f"Rate limit exceeded for {client_ip}",
                        extra={"security_event": "rate_limit_exceeded", "ip": client_ip}
                    )
                return Response(
                    content='{"error": "Too Many Requests", "detail": "Rate limit exceeded"}',
                    status_code=429,
                    media_type="application/json",
                    headers={"Retry-After": "60"}
                )

        # Process the request
        start_time = time.time()
        response = await call_next(request)
        request_time = time.time() - start_time

        # Add security headers to the response
        response = self._add_security_headers(response, request)

        # Log unusual response timing
        if request_time > 1.0:  # Log requests taking more than 1 second
            logger.info(
                f"Slow request: {request.method} {path} took {request_time:.2f}s",
                extra={"response_time": request_time, "path": path, "method": request.method}
            )

        return response

    def _add_security_headers(self, response: Response, request: Request) -> Response:
        """
        Add security headers to the response.

        Args:
            response: Response object
            request: Request object

        Returns:
            Response with added security headers
        """
        # Basic security headers (applied to all responses)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )

        # Content-Security-Policy
        if self.config.csp_enabled:
            csp_header = "Content-Security-Policy"
            if self.config.csp_report_only:
                csp_header = "Content-Security-Policy-Report-Only"

            csp_value = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "form-action 'self';"
            )

            if self.config.csp_report_uri:
                csp_value += f" report-uri {self.config.csp_report_uri};"

            response.headers[csp_header] = csp_value

        # Cross-Origin-* policies
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        # Cache-Control header for non-static content
        if "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = "no-store, max-age=0"

        # Add any custom headers
        for header, value in self.config.custom_headers.items():
            response.headers[header] = value

        return response

    def _get_client_ip(self, request: Request) -> str:
        """
        Get the client IP address from the request.

        Args:
            request: Request object

        Returns:
            Client IP address
        """
        # Check for X-Forwarded-For header (used by proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Use the first IP in the list (client IP)
            return forwarded_for.split(",")[0].strip()

        # Fall back to the direct client IP
        return request.client.host if request.client else "0.0.0.0"

    def _is_ip_allowed(self, ip: str) -> bool:
        """
        Check if an IP is allowed to access admin endpoints.

        Args:
            ip: IP address to check

        Returns:
            True if allowed, False otherwise
        """
        # If no allowlist is configured, allow all IPs
        if not self.config.admin_ip_allowlist:
            return True

        # Check if the IP is in the allowlist
        try:
            client_ip = ipaddress.ip_address(ip)

            for allowed in self.config.admin_ip_allowlist:
                # Check for IP range (CIDR notation)
                if "/" in allowed:
                    network = ipaddress.ip_network(allowed, strict=False)
                    if client_ip in network:
                        return True
                # Check for exact IP match
                elif ipaddress.ip_address(allowed) == client_ip:
                    return True

            return False
        except ValueError:
            # If IP parsing fails, deny access
            logger.warning(f"Invalid IP address format: {ip}")
            return False

    def _check_rate_limit(self, ip: str) -> bool:
        """
        Check if a client has exceeded the rate limit.

        Args:
            ip: Client IP address

        Returns:
            True if within rate limit, False if exceeded
        """
        if not self.config.rate_limiting_enabled:
            return True

        current_time = time.time()
        window_start = current_time - self.config.rate_limit_window

        # Initialize or get request timestamps for this IP
        if ip not in self.rate_limit_store:
            self.rate_limit_store[ip] = []

        # Filter out timestamps outside the current window
        self.rate_limit_store[ip] = [
            ts for ts in self.rate_limit_store[ip] if ts > window_start
        ]

        # Check if the client has exceeded the rate limit
        if len(self.rate_limit_store[ip]) >= self.config.rate_limit_requests:
            return False

        # Record this request
        self.rate_limit_store[ip].append(current_time)

        # Clean up old entries from other IPs periodically
        # This is a simple approach; a more scalable solution would use Redis
        if current_time % 60 < 1:  # Roughly every minute
            self._cleanup_rate_limit_store(window_start)

        return True

    def _cleanup_rate_limit_store(self, window_start: float) -> None:
        """
        Clean up old entries from the rate limit store.

        Args:
            window_start: Start time of the current window
        """
        # Create a list of IPs to remove (empty lists)
        to_remove = []

        for ip, timestamps in self.rate_limit_store.items():
            # Keep only timestamps in the current window
            valid_timestamps = [ts for ts in timestamps if ts > window_start]

            if valid_timestamps:
                self.rate_limit_store[ip] = valid_timestamps
            else:
                to_remove.append(ip)

        # Remove IPs with no recent requests
        for ip in to_remove:
            del self.rate_limit_store[ip]
