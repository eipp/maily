"""OWASP vulnerability mitigation middleware."""
import logging
import re
from typing import Dict, Any, List, Callable, Optional

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.datastructures import MutableHeaders
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class OWASPSecurityMiddleware(BaseHTTPMiddleware):
    """Middleware that applies OWASP security best practices."""

    def __init__(
        self,
        app: FastAPI,
        csp_directives: Optional[Dict[str, List[str]]] = None,
        hsts_max_age: int = 31536000,  # 1 year
        allowed_hosts: Optional[List[str]] = None,
        allowed_origins: Optional[List[str]] = None,
        xss_protection: bool = True,
        content_type_options: bool = True,
        frame_options: str = "DENY",
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: Optional[Dict[str, List[str]]] = None
    ):
        """Initialize the OWASP security middleware.

        Args:
            app: The FastAPI application.
            csp_directives: Content Security Policy directives.
            hsts_max_age: Max age for HSTS in seconds.
            allowed_hosts: List of allowed hosts.
            allowed_origins: List of allowed origins for CORS.
            xss_protection: Whether to enable XSS protection.
            content_type_options: Whether to enable content type options.
            frame_options: X-Frame-Options value.
            referrer_policy: Referrer-Policy value.
            permissions_policy: Permissions Policy directives.
        """
        super().__init__(app)

        # Default CSP directives
        self.csp_directives = csp_directives or {
            "default-src": ["'self'"],
            "script-src": ["'self'", "'unsafe-inline'"],
            "style-src": ["'self'", "'unsafe-inline'"],
            "img-src": ["'self'", "data:", "https://cdn.justmaily.com"],
            "connect-src": ["'self'", "https://*.justmaily.com"],
            "font-src": ["'self'", "data:"],
            "object-src": ["'none'"],
            "base-uri": ["'self'"],
            "form-action": ["'self'"]
        }

        self.hsts_max_age = hsts_max_age
        self.allowed_hosts = allowed_hosts or ["localhost", "127.0.0.1"]
        self.allowed_origins = allowed_origins or ["http://localhost:3000"]
        self.xss_protection = xss_protection
        self.content_type_options = content_type_options
        self.frame_options = frame_options
        self.referrer_policy = referrer_policy

        # Default permissions policy
        self.permissions_policy = permissions_policy or {
            "camera": [],
            "microphone": [],
            "geolocation": [],
            "payment": []
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and apply security headers.

        Args:
            request: The request to process.
            call_next: The next middleware to call.

        Returns:
            The response from the next middleware.
        """
        # Check if request has suspicious patterns (basic WAF-like behavior)
        path = request.url.path.lower()
        query = str(request.query_params).lower()
        body = None

        # Check if the request has a body and read it if it does
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
                if body_bytes:
                    body = body_bytes.decode("utf-8").lower()
            except Exception as e:
                logger.warning(f"Failed to read request body: {str(e)}")

        # Combine all request components for scanning
        request_content = f"{path} {query}"
        if body:
            request_content += f" {body}"

        # Check for common attack patterns
        if self._contains_attack_patterns(request_content):
            logger.warning(f"Potential attack detected in request: {request.url}")
            response = Response(
                content={"error": "Request blocked due to security concerns"},
                status_code=403,
                media_type="application/json"
            )
            return response

        # Process the request and get the response
        response = await call_next(request)

        # Add security headers
        self._add_security_headers(response)

        return response

    def _contains_attack_patterns(self, content: str) -> bool:
        """Check if content contains common attack patterns.

        Args:
            content: The content to check.

        Returns:
            True if the content contains attack patterns, False otherwise.
        """
        sql_patterns = [
            r"(\s|;)select\s+.+\s+from\s+",
            r"(\s|;)insert\s+into\s+.+\s+values\s*\(",
            r"(\s|;)update\s+.+\s+set\s+",
            r"(\s|;)delete\s+from\s+",
            r"(\s|;)drop\s+table\s+",
            r"(\s|;)union\s+select\s+",
            r"(\s|')or\s+'?[0-9a-zA-Z]+'?='?[0-9a-zA-Z]+'?",
            r"(\s|')and\s+'?[0-9a-zA-Z]+'?='?[0-9a-zA-Z]+'?"
        ]

        xss_patterns = [
            r"<script\b[^>]*>.*?</script>",
            r"javascript:",
            r"onerror\s*=",
            r"onload\s*=",
            r"eval\s*\(",
            r"document\.cookie",
            r"document\.write\s*\("
        ]

        for pattern in sql_patterns + xss_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True

        return False

    def _add_security_headers(self, response: Response) -> None:
        """Add security headers to the response.

        Args:
            response: The response to add headers to.
        """
        headers = MutableHeaders(response.headers)

        # Content Security Policy
        csp_value = self._build_csp_header()
        headers["Content-Security-Policy"] = csp_value

        # HTTP Strict Transport Security
        headers["Strict-Transport-Security"] = f"max-age={self.hsts_max_age}; includeSubDomains; preload"

        # X-XSS-Protection
        if self.xss_protection:
            headers["X-XSS-Protection"] = "1; mode=block"

        # X-Content-Type-Options
        if self.content_type_options:
            headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options
        headers["X-Frame-Options"] = self.frame_options

        # Referrer-Policy
        headers["Referrer-Policy"] = self.referrer_policy

        # Permissions-Policy
        permissions_value = self._build_permissions_policy()
        headers["Permissions-Policy"] = permissions_value

    def _build_csp_header(self) -> str:
        """Build the Content Security Policy header value.

        Returns:
            The CSP header value.
        """
        directives = []

        for directive, sources in self.csp_directives.items():
            if sources:
                directives.append(f"{directive} {' '.join(sources)}")
            else:
                directives.append(f"{directive} 'none'")

        return "; ".join(directives)

    def _build_permissions_policy(self) -> str:
        """Build the Permissions Policy header value.

        Returns:
            The Permissions Policy header value.
        """
        directives = []

        for feature, origins in self.permissions_policy.items():
            if origins:
                origins_str = " ".join([f'"{origin}"' for origin in origins])
                directives.append(f"{feature}=({origins_str})")
            else:
                directives.append(f"{feature}=()")

        return ", ".join(directives)


def setup_owasp_middleware(app: FastAPI, **kwargs) -> None:
    """Set up OWASP security middleware for the FastAPI app.

    Args:
        app: The FastAPI application.
        **kwargs: Additional arguments to pass to the middleware.
    """
    # Add TrustedHost middleware
    allowed_hosts = kwargs.get("allowed_hosts", ["localhost", "127.0.0.1"])
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

    # Add CORS middleware
    allowed_origins = kwargs.get("allowed_origins", ["http://localhost:3000"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add OWASP security middleware
    app.add_middleware(OWASPSecurityMiddleware, **kwargs)

    logger.info("OWASP security middleware set up")


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """Middleware for CSRF protection."""

    def __init__(
        self,
        app: FastAPI,
        csrf_cookie_name: str = "csrf_token",
        csrf_header_name: str = "X-CSRF-Token",
        safe_methods: List[str] = ["GET", "HEAD", "OPTIONS"],
        exempt_paths: List[str] = []
    ):
        """Initialize the CSRF protection middleware.

        Args:
            app: The FastAPI application.
            csrf_cookie_name: The name of the CSRF cookie.
            csrf_header_name: The name of the CSRF header.
            safe_methods: HTTP methods that don't require CSRF protection.
            exempt_paths: Paths that are exempt from CSRF protection.
        """
        super().__init__(app)
        self.csrf_cookie_name = csrf_cookie_name
        self.csrf_header_name = csrf_header_name
        self.safe_methods = [method.upper() for method in safe_methods]
        self.exempt_paths = exempt_paths

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and apply CSRF protection.

        Args:
            request: The request to process.
            call_next: The next middleware to call.

        Returns:
            The response from the next middleware.
        """
        # Skip CSRF check for safe methods and exempt paths
        if request.method in self.safe_methods or any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)

        # Get CSRF token from cookie and header
        csrf_cookie = request.cookies.get(self.csrf_cookie_name)
        csrf_header = request.headers.get(self.csrf_header_name)

        # Verify CSRF token
        if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
            logger.warning(f"CSRF token mismatch: cookie={csrf_cookie}, header={csrf_header}")
            return Response(
                content={"error": "CSRF token missing or invalid"},
                status_code=403,
                media_type="application/json"
            )

        return await call_next(request)
