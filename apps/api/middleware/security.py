"""
Consolidated security middleware for the API service.

This module provides comprehensive security protection including:
1. Security headers (HSTS, CSP, etc.)
2. OWASP protections (XSS, CSRF, etc.)
3. WAF capabilities
4. IP-based protection
5. Input validation
"""

import logging
import time
import re
import ipaddress
import json
from typing import List, Dict, Any, Optional, Callable, Union, Set
from urllib.parse import urlparse

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.datastructures import MutableHeaders

logger = logging.getLogger(__name__)

# Security configuration
DEFAULT_ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
DEFAULT_ALLOWED_ORIGINS = ["http://localhost:3000"]

# Attack patterns for basic WAF functionality
SQL_INJECTION_PATTERNS = [
    r"(\b(union|select|insert|update|delete|drop|alter)\b.*\b(from|into|table|database|varchar|where|values)\b)",
    r"(--\s*$)",
    r"(;\s*$)",
    r"(/\*.*\*/)",
]

XSS_PATTERNS = [
    r"(<script.*>.*</script>)",
    r"(javascript:.*\(.*\))",
    r"(on(load|error|click|mouseover|focus|blur)=)",
    r"(alert\s*\(.*\))",
]

PATH_TRAVERSAL_PATTERNS = [
    r"(\.\./|\.\./\.\.)",
    r"(/etc/passwd)",
    r"(/etc/shadow)",
    r"(c:/windows/win.ini)",
]

# Common attack user agents
SUSPICIOUS_USER_AGENTS = [
    "nmap", "sqlmap", "nikto", "burpsuite", "metasploit", "masscan", "dirsearch", "gobuster",
]

# Admin routes that need IP restrictions
ADMIN_ROUTES = [
    "/admin", "/api/v1/admin", "/api/admin", "/management", "/internal"
]

class SecurityConfig:
    """Configuration for comprehensive security middleware."""

    def __init__(
        self,
        # General settings
        environment: str = "development",
        debug: bool = False,
        
        # Security header settings
        content_security_policy: Dict[str, List[str]] = None,
        csp_report_only: bool = False,
        csp_report_uri: Optional[str] = None,
        strict_transport_security_max_age: int = 31536000,  # 1 year
        x_frame_options: str = "DENY",
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: Dict[str, List[str]] = None,
        
        # CORS settings
        allowed_origins: List[str] = None,
        allowed_hosts: List[str] = None,
        
        # WAF settings
        block_suspicious_requests: bool = True,
        block_suspicious_user_agents: bool = True,
        
        # Admin protection
        admin_ip_allowlist: List[str] = None,
        
        # Rate limiting settings
        admin_rate_limit_requests: int = 100,
        admin_rate_limit_window: int = 60,  # seconds
        
        # Request size validation
        max_content_length: int = 10 * 1024 * 1024,  # 10 MB
        
        # Security event logging
        log_security_events: bool = True,
        
        # Custom settings
        custom_headers: Dict[str, str] = None,
        
        # CSRF protection
        csrf_protection_enabled: bool = True,
        csrf_cookie_name: str = "csrf_token",
        csrf_header_name: str = "X-CSRF-Token",
        csrf_safe_methods: List[str] = None,
        
        # Bot protection
        bot_protection_enabled: bool = True,
        
        # Path exclusions
        exclude_paths: List[str] = None,
    ):
        """Initialize security configuration with comprehensive settings."""
        # General settings
        self.environment = environment
        self.debug = debug
        
        # Security header settings
        self.content_security_policy = content_security_policy or {
            "default-src": ["'self'"],
            "script-src": ["'self'", "'unsafe-inline'"],
            "style-src": ["'self'", "'unsafe-inline'"],
            "img-src": ["'self'", "data:", "https://cdn.maily.com"],
            "connect-src": ["'self'", "https://*.maily.com"],
            "font-src": ["'self'", "data:"],
            "object-src": ["'none'"],
            "base-uri": ["'self'"],
            "form-action": ["'self'"]
        }
        self.csp_report_only = csp_report_only
        self.csp_report_uri = csp_report_uri
        self.strict_transport_security_max_age = strict_transport_security_max_age
        self.x_frame_options = x_frame_options
        self.referrer_policy = referrer_policy
        
        # Permissions policy (formerly Feature-Policy)
        self.permissions_policy = permissions_policy or {
            "camera": [],
            "microphone": [],
            "geolocation": [],
            "payment": []
        }
        
        # CORS settings
        self.allowed_origins = allowed_origins or DEFAULT_ALLOWED_ORIGINS
        self.allowed_hosts = allowed_hosts or DEFAULT_ALLOWED_HOSTS
        
        # WAF settings
        self.block_suspicious_requests = block_suspicious_requests
        self.block_suspicious_user_agents = block_suspicious_user_agents
        
        # Admin protection
        self.admin_ip_allowlist = admin_ip_allowlist or []
        
        # Rate limiting settings (used only for admin endpoints in this middleware)
        self.admin_rate_limit_requests = admin_rate_limit_requests
        self.admin_rate_limit_window = admin_rate_limit_window
        self.admin_rate_limit_store = {}  # {ip: [(timestamp, count)]}
        
        # Request size validation
        self.max_content_length = max_content_length
        
        # Security event logging
        self.log_security_events = log_security_events
        
        # Custom headers
        self.custom_headers = custom_headers or {}
        
        # CSRF protection
        self.csrf_protection_enabled = csrf_protection_enabled
        self.csrf_cookie_name = csrf_cookie_name
        self.csrf_header_name = csrf_header_name
        self.csrf_safe_methods = csrf_safe_methods or ["GET", "HEAD", "OPTIONS"]
        
        # Bot protection
        self.bot_protection_enabled = bot_protection_enabled
        
        # Compile regex patterns
        self._compile_patterns()
        
        # Path exclusions (for documentation, health checks, etc.)
        self.exclude_paths = exclude_paths or ["/docs", "/redoc", "/openapi.json", "/health", "/metrics"]
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        self.sql_injection_regex = [re.compile(pattern, re.IGNORECASE) for pattern in SQL_INJECTION_PATTERNS]
        self.xss_regex = [re.compile(pattern, re.IGNORECASE) for pattern in XSS_PATTERNS]
        self.path_traversal_regex = [re.compile(pattern, re.IGNORECASE) for pattern in PATH_TRAVERSAL_PATTERNS]
        self.admin_routes_regex = [re.compile(f"^{pattern}.*") for pattern in ADMIN_ROUTES]


class ConsolidatedSecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware that combines multiple security functions.
    
    Features:
    - Security headers (CSP, HSTS, etc.)
    - OWASP Top 10 mitigations
    - Web Application Firewall (WAF) capabilities
    - IP-based protection
    - Request validation
    - CSRF protection
    - Bot detection
    """
    
    def __init__(
        self,
        app: ASGIApp,
        config: SecurityConfig = None,
    ):
        """
        Initialize the security middleware.
        
        Args:
            app: The ASGI application
            config: Security configuration (optional)
        """
        super().__init__(app)
        self.config = config or SecurityConfig()
        
        # Initialize rate limiting data
        self.last_cleanup = time.time()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request with security checks.
        
        Args:
            request: The request to process
            call_next: The next middleware to call
            
        Returns:
            The response from the next middleware
        """
        start_time = time.time()
        
        # Skip security checks for excluded paths
        if any(request.url.path.startswith(path) for path in self.config.exclude_paths):
            return await call_next(request)
        
        try:
            # 1. Check host header
            if not self._is_valid_host(request):
                if self.config.log_security_events:
                    logger.warning(f"Invalid host header: {request.headers.get('host')}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid host header"}
                )
            
            # 2. Check content length if applicable
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.config.max_content_length:
                if self.config.log_security_events:
                    logger.warning(f"Request too large: {content_length} bytes")
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": "Request entity too large"}
                )
            
            # 3. Check for WAF triggers
            waf_block, waf_reason = await self._check_waf_rules(request)
            if waf_block:
                if self.config.log_security_events:
                    logger.warning(f"WAF blocked request: {waf_reason} - {request.client.host} - {request.url.path}")
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Request blocked by security controls"}
                )
            
            # 4. Admin route protection
            if self._is_admin_route(request.url.path):
                # Check if IP is allowed for admin routes
                client_ip = self._get_client_ip(request)
                if not self._is_ip_allowed_for_admin(client_ip):
                    if self.config.log_security_events:
                        logger.warning(f"Unauthorized admin access attempt from IP: {client_ip}")
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"detail": "Access denied"}
                    )
                
                # Check admin rate limit
                if not self._check_admin_rate_limit(client_ip):
                    if self.config.log_security_events:
                        logger.warning(f"Admin rate limit exceeded for IP: {client_ip}")
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={"detail": "Rate limit exceeded for administrative endpoint"}
                    )
            
            # 5. CSRF protection
            if (self.config.csrf_protection_enabled and 
                request.method not in self.config.csrf_safe_methods):
                csrf_valid = await self._validate_csrf_token(request)
                if not csrf_valid:
                    if self.config.log_security_events:
                        logger.warning(f"CSRF validation failed: {request.client.host} - {request.url.path}")
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN, 
                        content={"detail": "CSRF token validation failed"}
                    )
            
            # Process the request
            response = await call_next(request)
            
            # Add security headers
            response = self._add_security_headers(response)
            
            # Add CSRF token to response if needed
            if self.config.csrf_protection_enabled:
                response = self._add_csrf_token(request, response)
            
            # Log security event if enabled
            if self.config.log_security_events:
                duration = time.time() - start_time
                logger.debug(f"Request processed with security checks in {duration:.3f}s: {request.method} {request.url.path}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in security middleware: {str(e)}")
            
            # Return generic error in production, more details in development
            if self.config.environment == "production":
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"detail": "Internal server error"}
                )
            else:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"detail": f"Security middleware error: {str(e)}"}
                )

    def _is_valid_host(self, request: Request) -> bool:
        """
        Check if the Host header is valid.
        
        Args:
            request: The incoming request
            
        Returns:
            True if the host is valid, False otherwise
        """
        host = request.headers.get("host", "").split(":")[0]
        return host in self.config.allowed_hosts or "*" in self.config.allowed_hosts
    
    async def _check_waf_rules(self, request: Request) -> tuple[bool, str]:
        """
        Check request against WAF rules.
        
        Args:
            request: The incoming request
            
        Returns:
            Tuple of (should_block, reason)
        """
        if not self.config.block_suspicious_requests:
            return False, ""
        
        # Check user agent
        user_agent = request.headers.get("user-agent", "").lower()
        if (self.config.block_suspicious_user_agents and 
            any(agent in user_agent for agent in SUSPICIOUS_USER_AGENTS)):
            return True, "suspicious_user_agent"
        
        # Check query parameters
        query_string = str(request.query_params)
        if self._contains_attack_patterns(query_string):
            return True, "suspicious_query"
        
        # Check path for traversal attempts
        if self._contains_path_traversal(request.url.path):
            return True, "path_traversal"
        
        # Check request body for POST, PUT, PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
                if body_bytes:
                    body_text = body_bytes.decode("utf-8", errors="ignore").lower()
                    if self._contains_attack_patterns(body_text):
                        return True, "suspicious_body"
            except Exception as e:
                logger.warning(f"Failed to read request body: {str(e)}")
        
        # Check headers for injection attempts
        headers_str = json.dumps(dict(request.headers))
        if self._contains_attack_patterns(headers_str):
            return True, "suspicious_headers"
        
        return False, ""
    
    def _contains_attack_patterns(self, content: str) -> bool:
        """
        Check if content contains attack patterns.
        
        Args:
            content: The content to check
            
        Returns:
            True if attack patterns are found, False otherwise
        """
        # Skip check for empty content
        if not content:
            return False
        
        # Check for SQL injection patterns
        for pattern in self.config.sql_injection_regex:
            if pattern.search(content):
                return True
        
        # Check for XSS patterns
        for pattern in self.config.xss_regex:
            if pattern.search(content):
                return True
        
        return False
    
    def _contains_path_traversal(self, path: str) -> bool:
        """
        Check if path contains traversal attempts.
        
        Args:
            path: The path to check
            
        Returns:
            True if path traversal is detected, False otherwise
        """
        for pattern in self.config.path_traversal_regex:
            if pattern.search(path):
                return True
        return False
    
    def _is_admin_route(self, path: str) -> bool:
        """
        Check if the path is an admin route.
        
        Args:
            path: The path to check
            
        Returns:
            True if it's an admin route, False otherwise
        """
        return any(pattern.match(path) for pattern in self.config.admin_routes_regex)
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Get the client IP address.
        
        Args:
            request: The incoming request
            
        Returns:
            The client IP address
        """
        # Try to get IP from X-Forwarded-For header
        xff = request.headers.get("x-forwarded-for")
        if xff:
            # Use the first IP in the list
            return xff.split(",")[0].strip()
        
        # Fall back to client.host
        return request.client.host if request.client else "unknown"
    
    def _is_ip_allowed_for_admin(self, ip: str) -> bool:
        """
        Check if IP is allowed for admin routes.
        
        Args:
            ip: The IP address to check
            
        Returns:
            True if IP is allowed, False otherwise
        """
        # If no allowlist is configured, default to deny
        if not self.config.admin_ip_allowlist:
            return False
        
        # Check if IP is in the allowlist
        for allowed_ip in self.config.admin_ip_allowlist:
            # Support for IP ranges with CIDR notation
            if "/" in allowed_ip:
                try:
                    network = ipaddress.ip_network(allowed_ip)
                    client_ip = ipaddress.ip_address(ip)
                    if client_ip in network:
                        return True
                except ValueError:
                    continue
            # Exact IP match
            elif ip == allowed_ip:
                return True
        
        return False

    def _check_admin_rate_limit(self, ip: str) -> bool:
        """
        Check rate limit for admin endpoints.
        
        Args:
            ip: The IP address
            
        Returns:
            True if within rate limit, False otherwise
        """
        now = time.time()
        
        # Clean up rate limit store periodically
        if now - self.last_cleanup > 60:  # Clean up every minute
            self._cleanup_rate_limit_store()
            self.last_cleanup = now
        
        # Get or initialize rate limiting data for this IP
        if ip not in self.config.admin_rate_limit_store:
            self.config.admin_rate_limit_store[ip] = []
        
        # Filter out entries outside the current window
        window_start = now - self.config.admin_rate_limit_window
        self.config.admin_rate_limit_store[ip] = [
            entry for entry in self.config.admin_rate_limit_store[ip] 
            if entry[0] > window_start
        ]
        
        # Count requests in the current window
        request_count = len(self.config.admin_rate_limit_store[ip])
        
        # Check if limit is exceeded
        if request_count >= self.config.admin_rate_limit_requests:
            return False

        # Add current request to the store
        self.config.admin_rate_limit_store[ip].append((now, 1))
        
        return True

    def _cleanup_rate_limit_store(self):
        """Clean up expired entries in the rate limit store."""
        now = time.time()
        window_start = now - self.config.admin_rate_limit_window
        
        for ip in list(self.config.admin_rate_limit_store.keys()):
            self.config.admin_rate_limit_store[ip] = [
                entry for entry in self.config.admin_rate_limit_store[ip] 
                if entry[0] > window_start
            ]
            
            # Remove empty entries
            if not self.config.admin_rate_limit_store[ip]:
                del self.config.admin_rate_limit_store[ip]
    
    async def _validate_csrf_token(self, request: Request) -> bool:
        """
        Validate CSRF token.
        
        Args:
            request: The incoming request
            
        Returns:
            True if CSRF token is valid, False otherwise
        """
        # Get CSRF token from headers
        csrf_token = request.headers.get(self.config.csrf_header_name)
        if not csrf_token:
            return False
        
        # Get CSRF token from cookies
        cookie_token = request.cookies.get(self.config.csrf_cookie_name)
        if not cookie_token:
            return False
        
        # Compare tokens
        return csrf_token == cookie_token
    
    def _add_csrf_token(self, request: Request, response: Response) -> Response:
        """
        Add CSRF token to response if needed.
        
        Args:
            request: The incoming request
            response: The response
            
        Returns:
            The updated response
        """
        # Only set CSRF cookie if it doesn't exist
        if self.config.csrf_cookie_name not in request.cookies:
            # Generate token
            import secrets
            token = secrets.token_hex(16)
            
            # Set cookie
            response.set_cookie(
                key=self.config.csrf_cookie_name,
                value=token,
                httponly=True,
                secure=request.url.scheme == "https",
                samesite="lax"
            )
        
        return response
    
    def _add_security_headers(self, response: Response) -> Response:
        """
        Add security headers to response.
        
        Args:
            response: The response
            
        Returns:
            The response with security headers added
        """
        # Content-Security-Policy
        if self.config.content_security_policy:
            csp_value = self._build_csp_header()
            header_name = "Content-Security-Policy-Report-Only" if self.config.csp_report_only else "Content-Security-Policy"
            response.headers[header_name] = csp_value
        
        # Strict-Transport-Security
        response.headers["Strict-Transport-Security"] = f"max-age={self.config.strict_transport_security_max_age}; includeSubDomains; preload"
        
        # X-Frame-Options
        response.headers["X-Frame-Options"] = self.config.x_frame_options
        
        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy
        response.headers["Referrer-Policy"] = self.config.referrer_policy
        
        # Permissions-Policy
        response.headers["Permissions-Policy"] = self._build_permissions_policy()
        
        # Add custom headers
        for name, value in self.config.custom_headers.items():
            response.headers[name] = value
        
        return response
    
    def _build_csp_header(self) -> str:
        """
        Build Content-Security-Policy header value.
        
        Returns:
            The CSP header value
        """
        csp_parts = []
        
        for directive, sources in self.config.content_security_policy.items():
            csp_parts.append(f"{directive} {' '.join(sources)}")
        
        # Add report URI if configured
        if self.config.csp_report_uri:
            csp_parts.append(f"report-uri {self.config.csp_report_uri}")
        
        return "; ".join(csp_parts)
    
    def _build_permissions_policy(self) -> str:
        """
        Build Permissions-Policy header value.
        
        Returns:
            The Permissions-Policy header value
        """
        policy_parts = []
        
        for feature, origins in self.config.permissions_policy.items():
            if not origins:
                policy_parts.append(f"{feature}=()")
            else:
                origins_str = " ".join(f'"{origin}"' for origin in origins)
                policy_parts.append(f"{feature}=({origins_str})")
        
        return ", ".join(policy_parts)


# This middleware integrates WAF capabilities with broader security controls
async def waf_middleware(request: Request, call_next: Callable) -> Response:
    """
    WAF middleware that inspects requests for malicious content.
    
    This is now integrated into the ConsolidatedSecurityMiddleware, but kept
    as a separate function for backward compatibility.
    
    Args:
        request: The incoming request
        call_next: The next middleware to call
        
    Returns:
        The response from the next middleware
    """
    # Pass through to the next middleware
    return await call_next(request)


# Security middleware integrates various security controls
async def security_middleware(request: Request, call_next: Callable) -> Response:
    """
    Security middleware that adds various security controls.
    
    This is now integrated into the ConsolidatedSecurityMiddleware, but kept
    as a separate function for backward compatibility.
    
    Args:
        request: The incoming request
        call_next: The next middleware to call
        
    Returns:
        The response from the next middleware
    """
    # Pass through to the next middleware
    return await call_next(request)


def add_security_middleware(app, config=None):
    """
    Add security middleware to a FastAPI application.
    
    Args:
        app: The FastAPI application
        config: Optional security configuration
        
    Returns:
        The FastAPI application with security middleware added
    """
    # Create default config if not provided
    if config is None:
        config = SecurityConfig()
    
    # Add the consolidated security middleware
    app.add_middleware(ConsolidatedSecurityMiddleware, config=config)
    
    return app
