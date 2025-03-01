"""
Tests for the Enhanced Security Headers Middleware.

These tests verify the security headers are correctly applied, rate limiting works,
IP allowlisting functions correctly, and request size validation is enforced.
"""

import pytest
import time
import ipaddress
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from apps.api.middleware.security_headers import (
    EnhancedSecurityHeadersMiddleware,
    SecurityConfig
)


# Helper functions
def create_test_app(config=None, exclude_paths=None):
    """Create a test FastAPI app with the security middleware."""
    app = FastAPI()
    app.add_middleware(
        EnhancedSecurityHeadersMiddleware,
        config=config,
        exclude_paths=exclude_paths
    )

    @app.get("/")
    async def root():
        return {"message": "Hello World"}

    @app.get("/admin")
    async def admin():
        return {"message": "Admin Area"}

    @app.get("/docs")
    async def docs():
        return {"message": "API Docs"}

    @app.post("/upload")
    async def upload(request: Request):
        return {"message": "Upload received"}

    return app


# Fixtures
@pytest.fixture
def default_app():
    """Create a test app with default settings."""
    return create_test_app()


@pytest.fixture
def custom_app():
    """Create a test app with custom settings."""
    config = SecurityConfig(
        csp_enabled=True,
        csp_report_only=False,
        rate_limiting_enabled=True,
        rate_limit_requests=3,  # Low limit for testing
        rate_limit_window=10,
        max_content_length=1024,  # 1KB for testing
        admin_ip_allowlist=["127.0.0.1", "192.168.1.0/24"],
        log_security_events=True
    )
    return create_test_app(config=config)


@pytest.fixture
def excluded_paths_app():
    """Create a test app with excluded paths."""
    return create_test_app(exclude_paths=["/excluded"])


# Tests
class TestSecurityHeaders:
    """Tests for security headers functionality."""

    def test_default_security_headers(self, default_app):
        """Test that default security headers are applied."""
        client = TestClient(default_app)
        response = client.get("/")

        # Verify status code
        assert response.status_code == 200

        # Verify security headers
        headers = response.headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"
        assert headers["X-XSS-Protection"] == "1; mode=block"
        assert "max-age=31536000" in headers["Strict-Transport-Security"]
        assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "Permissions-Policy" in headers

        # CSP should be enabled by default
        assert "Content-Security-Policy" in headers
        assert "default-src 'self'" in headers["Content-Security-Policy"]

        # Cross-Origin policies should be set
        assert headers["Cross-Origin-Opener-Policy"] == "same-origin"
        assert headers["Cross-Origin-Embedder-Policy"] == "require-corp"
        assert headers["Cross-Origin-Resource-Policy"] == "same-origin"

    def test_custom_security_headers(self, custom_app):
        """Test that custom security headers are applied."""
        client = TestClient(custom_app)
        response = client.get("/")

        # Verify custom headers are present
        headers = response.headers
        assert "Content-Security-Policy" in headers
        assert "default-src 'self'" in headers["Content-Security-Policy"]

    def test_csp_report_only(self):
        """Test that CSP report-only mode works."""
        config = SecurityConfig(
            csp_enabled=True,
            csp_report_only=True,
            csp_report_uri="/csp-report"
        )
        app = create_test_app(config=config)
        client = TestClient(app)
        response = client.get("/")

        # Verify CSP is in report-only mode
        headers = response.headers
        assert "Content-Security-Policy-Report-Only" in headers
        assert "Content-Security-Policy" not in headers
        assert "report-uri /csp-report" in headers["Content-Security-Policy-Report-Only"]

    def test_excluded_paths(self, excluded_paths_app):
        """Test that excluded paths don't get security headers."""
        client = TestClient(excluded_paths_app)

        # Regular path should have security headers
        regular_response = client.get("/")
        assert "X-Content-Type-Options" in regular_response.headers

        # Add route to excluded path
        @excluded_paths_app.get("/excluded")
        async def excluded():
            return {"message": "Excluded Path"}

        # Excluded path should not have security headers
        excluded_response = client.get("/excluded")
        assert excluded_response.status_code == 200
        assert "X-Content-Type-Options" not in excluded_response.headers


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    def test_rate_limiting(self):
        """Test that rate limiting works correctly."""
        config = SecurityConfig(
            rate_limiting_enabled=True,
            rate_limit_requests=3,  # Allow only 3 requests
            rate_limit_window=60
        )
        app = create_test_app(config=config)
        client = TestClient(app)

        # Make requests up to the limit
        for _ in range(3):
            response = client.get("/")
            assert response.status_code == 200

        # The next request should be rate limited
        response = client.get("/")
        assert response.status_code == 429
        assert "Too Many Requests" in response.text
        assert "Retry-After" in response.headers

    def test_rate_limiting_disabled(self):
        """Test that when rate limiting is disabled, no limit is applied."""
        config = SecurityConfig(
            rate_limiting_enabled=False
        )
        app = create_test_app(config=config)
        client = TestClient(app)

        # Make many requests, should all succeed
        for _ in range(10):
            response = client.get("/")
            assert response.status_code == 200


class TestIPAllowlisting:
    """Tests for IP allowlisting functionality."""

    def test_admin_ip_allowlist(self):
        """Test that admin IP allowlisting works correctly."""
        config = SecurityConfig(
            admin_ip_allowlist=["192.168.1.1"]  # Only allow this IP
        )
        app = create_test_app(config=config)
        client = TestClient(app)

        # Patch the _get_client_ip method to return a non-allowed IP
        with patch.object(
            EnhancedSecurityHeadersMiddleware,
            '_get_client_ip',
            return_value="192.168.1.2"
        ):
            # Admin path should be blocked
            response = client.get("/admin")
            assert response.status_code == 403
            assert "Unauthorized" in response.text

            # Regular path should still work
            response = client.get("/")
            assert response.status_code == 200

        # Patch to return an allowed IP
        with patch.object(
            EnhancedSecurityHeadersMiddleware,
            '_get_client_ip',
            return_value="192.168.1.1"
        ):
            # Admin path should now work
            response = client.get("/admin")
            assert response.status_code == 200

    def test_ip_cidr_allowlisting(self):
        """Test that CIDR notation works for IP allowlisting."""
        config = SecurityConfig(
            admin_ip_allowlist=["10.0.0.0/24"]  # Allow 10.0.0.* IPs
        )
        app = create_test_app(config=config)
        client = TestClient(app)

        # Test IPs in the allowed range
        for ip in ["10.0.0.1", "10.0.0.100", "10.0.0.254"]:
            with patch.object(
                EnhancedSecurityHeadersMiddleware,
                '_get_client_ip',
                return_value=ip
            ):
                response = client.get("/admin")
                assert response.status_code == 200, f"IP {ip} should be allowed"

        # Test IPs outside the allowed range
        for ip in ["10.0.1.1", "192.168.1.1", "8.8.8.8"]:
            with patch.object(
                EnhancedSecurityHeadersMiddleware,
                '_get_client_ip',
                return_value=ip
            ):
                response = client.get("/admin")
                assert response.status_code == 403, f"IP {ip} should be blocked"


class TestRequestSizeValidation:
    """Tests for request size validation functionality."""

    def test_max_content_length(self):
        """Test that requests exceeding max_content_length are rejected."""
        config = SecurityConfig(
            max_content_length=100  # 100 bytes
        )
        app = create_test_app(config=config)
        client = TestClient(app)

        # Small request should be accepted
        small_data = "a" * 50
        headers = {"Content-Length": str(len(small_data))}
        response = client.post("/upload", data=small_data, headers=headers)
        assert response.status_code == 200

        # Large request should be rejected
        large_data = "a" * 200
        headers = {"Content-Length": str(len(large_data))}
        response = client.post("/upload", data=large_data, headers=headers)
        assert response.status_code == 413
        assert "Request Entity Too Large" in response.text


class TestSecurityUtils:
    """Tests for security utility functions."""

    def test_get_client_ip(self):
        """Test that client IP is correctly extracted."""
        middleware = EnhancedSecurityHeadersMiddleware(app=FastAPI())

        # Test with X-Forwarded-For header
        mock_request = MagicMock()
        mock_request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
        assert middleware._get_client_ip(mock_request) == "192.168.1.1"

        # Test with client.host
        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.client.host = "192.168.1.2"
        assert middleware._get_client_ip(mock_request) == "192.168.1.2"

        # Test with no client information
        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.client = None
        assert middleware._get_client_ip(mock_request) == "0.0.0.0"

    def test_is_ip_allowed(self):
        """Test that IP allowlist checking works correctly."""
        config = SecurityConfig(
            admin_ip_allowlist=["192.168.1.1", "10.0.0.0/24"]
        )
        middleware = EnhancedSecurityHeadersMiddleware(app=FastAPI(), config=config)

        # Test allowed exact IP
        assert middleware._is_ip_allowed("192.168.1.1") is True

        # Test allowed CIDR range
        assert middleware._is_ip_allowed("10.0.0.1") is True
        assert middleware._is_ip_allowed("10.0.0.254") is True

        # Test disallowed IPs
        assert middleware._is_ip_allowed("192.168.1.2") is False
        assert middleware._is_ip_allowed("10.0.1.1") is False

        # Test invalid IP format
        assert middleware._is_ip_allowed("invalid-ip") is False

        # Test empty allowlist (should allow all)
        middleware.config.admin_ip_allowlist = []
        assert middleware._is_ip_allowed("192.168.1.1") is True

    def test_check_rate_limit(self):
        """Test that rate limit checking works correctly."""
        config = SecurityConfig(
            rate_limiting_enabled=True,
            rate_limit_requests=3,
            rate_limit_window=10
        )
        middleware = EnhancedSecurityHeadersMiddleware(app=FastAPI(), config=config)

        # Clear rate limit store
        middleware.rate_limit_store = {}

        # Test requests under the limit
        assert middleware._check_rate_limit("192.168.1.1") is True
        assert middleware._check_rate_limit("192.168.1.1") is True
        assert middleware._check_rate_limit("192.168.1.1") is True

        # Test exceeding the limit
        assert middleware._check_rate_limit("192.168.1.1") is False

        # Test different IP (should have its own limit)
        assert middleware._check_rate_limit("192.168.1.2") is True

        # Test cleanup (expired entries should be removed)
        old_time = time.time() - 20  # 20 seconds ago (beyond the window)
        middleware.rate_limit_store["192.168.1.3"] = [old_time, old_time]
        middleware._cleanup_rate_limit_store(time.time() - 10)
        assert "192.168.1.3" not in middleware.rate_limit_store
