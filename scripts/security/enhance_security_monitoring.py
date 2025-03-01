#!/usr/bin/env python3
"""
Enhance Security Monitoring Script

This script implements security monitoring enhancements for the Maily platform.
It focuses on improving security event detection, alerting, and response capabilities
by integrating with monitoring tools and implementing additional security checks.

Usage:
    python enhance_security_monitoring.py [--dry-run] [--verbose]

Options:
    --dry-run   Show changes without applying them
    --verbose   Show detailed information during execution
"""

import os
import re
import sys
import argparse
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("security-monitoring")

# Paths to security monitoring-related files
SECURITY_FILES = {
    "prometheus_config": "infrastructure/kubernetes/monitoring/prometheus-operator.yaml",
    "alertmanager_config": "infrastructure/kubernetes/monitoring/alertmanager-config.yaml",
    "security_monitoring": "infrastructure/kubernetes/security/security-monitoring-deployment.yaml",
    "security_scanning": "infrastructure/kubernetes/security/security-scanning-configmap.yaml",
    "falco_rules": "infrastructure/kubernetes/security/falco-rules.yaml",
    "grafana_dashboards": "infrastructure/kubernetes/monitoring/grafana-dashboards.yaml",
    "api_middleware": "apps/api/middleware/security.py",
    "web_middleware": "apps/web/middleware.ts",
}

# Prometheus alert rules for security monitoring
PROMETHEUS_SECURITY_ALERTS = """
groups:
- name: security-alerts
  rules:
  - alert: HighRateOf4xxResponses
    expr: sum(rate(http_requests_total{status=~"4.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05
    for: 5m
    labels:
      severity: warning
      category: security
    annotations:
      summary: "High rate of 4xx responses"
      description: "More than 5% of requests are resulting in 4xx responses over the last 5 minutes"

  - alert: HighRateOf5xxResponses
    expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.01
    for: 5m
    labels:
      severity: critical
      category: security
    annotations:
      summary: "High rate of 5xx responses"
      description: "More than 1% of requests are resulting in 5xx responses over the last 5 minutes"

  - alert: UnusualNumberOfRequests
    expr: sum(rate(http_requests_total[5m])) > (sum(rate(http_requests_total[1h] offset 1d)) * 2) and sum(rate(http_requests_total[5m])) > 10
    for: 15m
    labels:
      severity: warning
      category: security
    annotations:
      summary: "Unusual number of HTTP requests"
      description: "Number of HTTP requests is more than twice the normal rate"

  - alert: BruteForceLoginAttempts
    expr: sum(rate(auth_login_failed_total[5m])) > 10
    for: 5m
    labels:
      severity: critical
      category: security
    annotations:
      summary: "Possible brute force login attempts"
      description: "High rate of failed login attempts detected"

  - alert: UnauthorizedAccessAttempts
    expr: sum(rate(auth_unauthorized_access_total[5m])) > 5
    for: 5m
    labels:
      severity: critical
      category: security
    annotations:
      summary: "Unauthorized access attempts"
      description: "High rate of unauthorized access attempts detected"

  - alert: APIKeyMisuse
    expr: sum(rate(auth_api_key_misuse_total[5m])) > 0
    for: 5m
    labels:
      severity: critical
      category: security
    annotations:
      summary: "API key misuse detected"
      description: "Possible API key misuse or theft detected"

  - alert: WAFBlockedRequests
    expr: sum(rate(waf_blocked_requests_total[5m])) > 10
    for: 5m
    labels:
      severity: warning
      category: security
    annotations:
      summary: "High rate of WAF blocked requests"
      description: "Web Application Firewall is blocking a high number of requests"

  - alert: SuspiciousIPActivity
    expr: sum by (client_ip) (rate(http_requests_total{status=~"4.."}[5m])) > 20
    for: 5m
    labels:
      severity: warning
      category: security
    annotations:
      summary: "Suspicious IP activity"
      description: "IP {{ $labels.client_ip }} is generating a high number of 4xx errors"

  - alert: AnomalousJWTValidationFailure
    expr: sum(rate(auth_jwt_validation_failed_total[5m])) > 5
    for: 5m
    labels:
      severity: critical
      category: security
    annotations:
      summary: "Anomalous JWT validation failures"
      description: "High rate of JWT validation failures detected"

  - alert: DataExfiltrationAttempt
    expr: sum(rate(http_response_size_bytes_sum[5m])) / sum(rate(http_response_size_bytes_count[5m])) > 500000
    for: 5m
    labels:
      severity: critical
      category: security
    annotations:
      summary: "Possible data exfiltration attempt"
      description: "Average response size is unusually large, possible data exfiltration"
"""

# Falco rules for runtime security monitoring
FALCO_SECURITY_RULES = """
- rule: Unauthorized Process Access
  desc: Detect unauthorized process access to sensitive files
  condition: >
    open_read and
    (
      fd.name startswith "/etc/shadow" or
      fd.name startswith "/etc/passwd" or
      fd.name startswith "/etc/kubernetes/pki" or
      fd.name startswith "/var/run/secrets"
    ) and not proc.name in (authorized_processes)
  output: >
    Unauthorized process accessing sensitive file (user=%user.name process=%proc.name
    command=%proc.cmdline file=%fd.name parent=%proc.pname container_id=%container.id)
  priority: CRITICAL
  tags: [process, mitre_credential_access]

- rule: Suspicious Outbound Connection
  desc: Detect suspicious outbound connections to potentially malicious domains
  condition: >
    outbound and
    not fd.sip in (allowed_outbound_ips) and
    not fd.domain in (allowed_outbound_domains)
  output: >
    Suspicious outbound connection detected (user=%user.name process=%proc.name
    command=%proc.cmdline connection=%fd.name container_id=%container.id)
  priority: WARNING
  tags: [network, mitre_command_and_control]

- rule: Container Escape Attempt
  desc: Detect potential container escape attempts
  condition: >
    spawned_process and
    container and
    (
      proc.name = "mount" or
      proc.name = "nsenter" or
      proc.name = "unshare" or
      proc.cmdline contains "capability" or
      proc.cmdline contains "privileged"
    )
  output: >
    Container escape attempt detected (user=%user.name process=%proc.name
    command=%proc.cmdline container_id=%container.id)
  priority: CRITICAL
  tags: [process, container, mitre_privilege_escalation]

- rule: Suspicious File Modification
  desc: Detect modifications to critical system files
  condition: >
    open_write and
    (
      fd.name startswith "/etc/kubernetes" or
      fd.name startswith "/var/lib/kubelet" or
      fd.name startswith "/etc/systemd" or
      fd.name startswith "/etc/ssl/certs" or
      fd.name startswith "/usr/bin" or
      fd.name startswith "/usr/sbin"
    ) and not proc.name in (authorized_processes)
  output: >
    Critical system file modification detected (user=%user.name process=%proc.name
    command=%proc.cmdline file=%fd.name container_id=%container.id)
  priority: CRITICAL
  tags: [file, mitre_persistence]

- rule: Suspicious Process Execution
  desc: Detect execution of suspicious processes
  condition: >
    spawned_process and
    (
      proc.name in (suspicious_processes) or
      proc.cmdline contains "nc -l" or
      proc.cmdline contains "netcat -l" or
      proc.cmdline contains "ncat -l" or
      proc.cmdline contains "curl -o" or
      proc.cmdline contains "wget -O"
    )
  output: >
    Suspicious process execution detected (user=%user.name process=%proc.name
    command=%proc.cmdline container_id=%container.id)
  priority: WARNING
  tags: [process, mitre_execution]

- rule: Unauthorized API Server Access
  desc: Detect unauthorized access to the Kubernetes API server
  condition: >
    outbound and fd.sport=443 and fd.sip="kubernetes_api_server_ip" and
    not proc.name in (authorized_k8s_processes)
  output: >
    Unauthorized access to Kubernetes API server detected (user=%user.name
    process=%proc.name command=%proc.cmdline container_id=%container.id)
  priority: CRITICAL
  tags: [network, k8s, mitre_discovery]

- rule: Sensitive Data Access
  desc: Detect access to sensitive data
  condition: >
    open_read and
    (
      fd.name contains "credentials" or
      fd.name contains "password" or
      fd.name contains "secret" or
      fd.name contains "token" or
      fd.name contains "apikey"
    ) and not proc.name in (authorized_processes)
  output: >
    Sensitive data access detected (user=%user.name process=%proc.name
    command=%proc.cmdline file=%fd.name container_id=%container.id)
  priority: WARNING
  tags: [file, mitre_credential_access]

- list: authorized_processes
  items: [
    "sshd",
    "sudo",
    "su",
    "kubectl",
    "kubelet",
    "kube-apiserver",
    "kube-controller-manager",
    "kube-scheduler",
    "etcd",
    "falco",
    "systemd",
    "systemd-journald"
  ]

- list: authorized_k8s_processes
  items: [
    "kubectl",
    "kubelet",
    "kube-proxy",
    "kube-apiserver",
    "kube-controller-manager",
    "kube-scheduler",
    "helm"
  ]

- list: suspicious_processes
  items: [
    "nc",
    "ncat",
    "netcat",
    "nmap",
    "tcpdump",
    "wireshark",
    "tshark",
    "socat",
    "mitmproxy",
    "proxychains"
  ]

- list: allowed_outbound_domains
  items: [
    "kubernetes.default.svc",
    "kube-dns.kube-system.svc",
    "registry.k8s.io",
    "docker.io",
    "gcr.io",
    "ghcr.io",
    "quay.io",
    "amazonaws.com",
    "cloudflare.com",
    "github.com",
    "npmjs.org",
    "pypi.org"
  ]

- list: allowed_outbound_ips
  items: []  # To be populated with trusted IPs
"""

# Enhanced security headers for API
API_SECURITY_HEADERS = '''
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
import re
import time
from typing import List, Dict, Optional, Set, Tuple

logger = logging.getLogger(__name__)

class EnhancedSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to responses."""

    def __init__(
        self,
        app: ASGIApp,
        csp_directives: Optional[Dict[str, str]] = None,
        allowed_admin_ips: Optional[List[str]] = None,
        max_request_size: int = 10 * 1024 * 1024,  # 10MB
        enable_rate_limiting: bool = True,
        rate_limit_requests: int = 100,
        rate_limit_window: int = 60,  # 1 minute
    ):
        """Initialize the middleware.

        Args:
            app: The ASGI application
            csp_directives: Content Security Policy directives
            allowed_admin_ips: List of IPs allowed to access admin endpoints
            max_request_size: Maximum allowed request size in bytes
            enable_rate_limiting: Whether to enable rate limiting
            rate_limit_requests: Maximum number of requests allowed in the window
            rate_limit_window: Time window for rate limiting in seconds
        """
        super().__init__(app)
        self.csp_directives = csp_directives or {
            "default-src": "'self'",
            "script-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            "style-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            "img-src": "'self' data: https://cdn.jsdelivr.net",
            "font-src": "'self' https://cdn.jsdelivr.net",
            "connect-src": "'self'",
            "frame-src": "'none'",
            "object-src": "'none'",
            "base-uri": "'self'",
            "form-action": "'self'",
            "frame-ancestors": "'none'",
            "upgrade-insecure-requests": "",
        }
        self.allowed_admin_ips = set(allowed_admin_ips or [])
        self.max_request_size = max_request_size
        self.enable_rate_limiting = enable_rate_limiting
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_window = rate_limit_window
        self.rate_limit_store = {}  # IP -> [(timestamp, count)]

    async def dispatch(self, request: Request, call_next):
        """Process the request and add security headers to the response."""
        # Check request size
        if "content-length" in request.headers:
            content_length = int(request.headers["content-length"])
            if content_length > self.max_request_size:
                logger.warning(
                    f"Request size exceeds maximum allowed size",
                    extra={
                        "client_ip": self._get_client_ip(request),
                        "path": request.url.path,
                        "content_length": content_length,
                        "max_size": self.max_request_size,
                    }
                )
                return Response(
                    content="Request entity too large",
                    status_code=413,
                )

        # Check rate limiting
        if self.enable_rate_limiting:
            client_ip = self._get_client_ip(request)
            if self._is_rate_limited(client_ip):
                logger.warning(
                    f"Rate limit exceeded for client",
                    extra={
                        "client_ip": client_ip,
                        "path": request.url.path,
                    }
                )
                return Response(
                    content="Too many requests",
                    status_code=429,
                    headers={"Retry-After": str(self.rate_limit_window)},
                )

        # Check admin endpoint access
        if self._is_admin_endpoint(request.url.path):
            client_ip = self._get_client_ip(request)
            if client_ip not in self.allowed_admin_ips:
                logger.warning(
                    f"Unauthorized access attempt to admin endpoint",
                    extra={
                        "client_ip": client_ip,
                        "path": request.url.path,
                    }
                )
                return Response(
                    content="Forbidden",
                    status_code=403,
                )

        # Process the request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()"
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        # Add Content-Security-Policy header
        csp_value = "; ".join([
            f"{key} {value}" for key, value in self.csp_directives.items()
        ])
        response.headers["Content-Security-Policy"] = csp_value

        # Add server timing header for performance monitoring
        response.headers["Server-Timing"] = f"total;dur={process_time * 1000}"

        # Log request details for security monitoring
        logger.info(
            f"Request processed",
            extra={
                "client_ip": self._get_client_ip(request),
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": process_time,
                "user_agent": request.headers.get("user-agent", ""),
                "referer": request.headers.get("referer", ""),
            }
        )

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get the client IP address from the request."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_admin_endpoint(self, path: str) -> bool:
        """Check if the path is an admin endpoint."""
        return path.startswith("/admin") or path.startswith("/api/admin")

    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if the client IP is rate limited."""
        if not self.enable_rate_limiting:
            return False

        current_time = time.time()

        # Clean up old entries
        if client_ip in self.rate_limit_store:
            self.rate_limit_store[client_ip] = [
                (ts, count) for ts, count in self.rate_limit_store[client_ip]
                if current_time - ts < self.rate_limit_window
            ]

        # Initialize if not exists
        if client_ip not in self.rate_limit_store:
            self.rate_limit_store[client_ip] = []

        # Count requests in the current window
        total_requests = sum(count for _, count in self.rate_limit_store[client_ip])

        # Add current request
        if not self.rate_limit_store[client_ip]:
            self.rate_limit_store[client_ip].append((current_time, 1))
        else:
            last_ts, count = self.rate_limit_store[client_ip][-1]
            if current_time - last_ts < 1:  # Group requests within 1 second
                self.rate_limit_store[client_ip][-1] = (last_ts, count + 1)
            else:
                self.rate_limit_store[client_ip].append((current_time, 1))

        # Check if rate limit is exceeded
        return total_requests >= self.rate_limit_requests
'''

# Enhanced security headers for Web
WEB_SECURITY_HEADERS = '''
import { NextRequest, NextResponse } from 'next/server';

/**
 * Middleware to add security headers to responses
 */
export function middleware(request: NextRequest) {
  // Get the response
  const response = NextResponse.next();

  // Add security headers
  const headers = response.headers;

  // Basic security headers
  headers.set('X-Content-Type-Options', 'nosniff');
  headers.set('X-Frame-Options', 'DENY');
  headers.set('X-XSS-Protection', '1; mode=block');
  headers.set('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload');
  headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  headers.set('Permissions-Policy', 'accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()');
  headers.set('Cache-Control', 'no-store, max-age=0');
  headers.set('X-Permitted-Cross-Domain-Policies', 'none');
  headers.set('Cross-Origin-Embedder-Policy', 'require-corp');
  headers.set('Cross-Origin-Opener-Policy', 'same-origin');
  headers.set('Cross-Origin-Resource-Policy', 'same-origin');

  // Content Security Policy
  headers.set(
    'Content-Security-Policy',
    `default-src 'self';
     script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;
     style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;
     img-src 'self' data: https://cdn.jsdelivr.net;
     font-src 'self' https://cdn.jsdelivr.net;
     connect-src 'self';
     frame-src 'none';
     object-src 'none';
     base-uri 'self';
     form-action 'self';
     frame-ancestors 'none';
     upgrade-insecure-requests;`
  );

  // Log security-relevant information
  console.log(`Security headers added for ${request.url}`);

  return response;
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|public/).*)',
  ],
};
'''

class SecurityMonitoringEnhancer:
    """Class to enhance security monitoring in the codebase."""

    def __init__(self, dry_run: bool = False, verbose: bool = False):
        """Initialize the enhancer.

        Args:
            dry_run: If True, show changes without applying them
            verbose: If True, show detailed information during execution
        """
        self.dry_run = dry_run
        self.verbose = verbose
        self.root_dir = self._find_root_dir()
        self.files_updated = 0

    def _find_root_dir(self) -> Path:
        """Find the root directory of the project."""
        current_dir = Path.cwd()
        while current_dir != current_dir.parent:
            if (current_dir / "README.md").exists() and (current_dir / "apps").exists():
                return current_dir
            current_dir = current_dir.parent

        # If we can't find the root directory, use the current directory
        return Path.cwd()

    def _log(self, message: str):
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            logger.info(message)

    def enhance_security_monitoring(self):
        """Enhance security monitoring across the codebase."""
        logger.info("Enhancing security monitoring...")

        # Add Prometheus security alerts
        self._add_prometheus_alerts()

        # Add Falco security rules
        self._add_falco_rules()

        # Enhance API security headers
        self._enhance_api_security_headers()

        # Enhance Web security headers
        self._enhance_web_security_headers()

        # Create security dashboard
        self._create_security_dashboard()

        logger.info(f"Security monitoring enhancement complete. {self.files_updated} files updated.")

    def _add_prometheus_alerts(self):
        """Add Prometheus security alerts."""
        prometheus_alerts_path = self.root_dir / "infrastructure/prometheus/security-alerts.yml"

        # Create directory if it doesn't exist
        prometheus_alerts_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Adding Prometheus security alerts at {prometheus_alerts_path}")

        if not self.dry_run:
            prometheus_alerts_path.write_text(PROMETHEUS_SECURITY_ALERTS)
            self.files_updated += 1
        else:
            self._log(f"Would add Prometheus security alerts at {prometheus_alerts_path} (dry run)")

    def _add_falco_rules(self):
        """Add Falco security rules."""
        falco_rules_path = self.root_dir / "infrastructure/kubernetes/security/falco-rules.yaml"

        # Create directory if it doesn't exist
        falco_rules_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Adding Falco security rules at {falco_rules_path}")

        if not self.dry_run:
            falco_rules_path.write_text(FALCO_SECURITY_RULES)
            self.files_updated += 1
        else:
            self._log(f"Would add Falco security rules at {falco_rules_path} (dry run)")

    def _enhance_api_security_headers(self):
        """Enhance API security headers."""
        api_security_path = self.root_dir / SECURITY_FILES["api_middleware"]

        if api_security_path.exists():
            logger.info(f"Enhancing API security headers at {api_security_path}")

            # Read existing file to check if it already has the enhanced headers
            existing_code = api_security_path.read_text()

            if "EnhancedSecurityHeadersMiddleware" in existing_code:
                logger.info("Enhanced security headers already exist in API middleware")
                return

            if not self.dry_run:
                api_security_path.write_text(API_SECURITY_HEADERS)
                self.files_updated += 1
            else:
                self._log(f"Would enhance API security headers at {api_security_path} (dry run)")
        else:
            logger.info(f"Creating API security headers at {api_security_path}")

            # Create directory if it doesn't exist
            api_security_path.parent.mkdir(parents=True, exist_ok=True)

            if not self.dry_run:
                api_security_path.write_text(API_SECURITY_HEADERS)
                self.files_updated += 1
            else:
                self._log(f"Would create API security headers at {api_security_path} (dry run)")

    def _enhance_web_security_headers(self):
        """Enhance Web security headers."""
        web_security_path = self.root_dir / SECURITY_FILES["web_middleware"]

        if web_security_path.exists():
            logger.info(f"Enhancing Web security headers at {web_security_path}")

            # Read existing file to check if it already has the enhanced headers
            existing_code = web_security_path.read_text()

            if "Content-Security-Policy" in existing_code:
                logger.info("Enhanced security headers already exist in Web middleware")
                return

            if not self.dry_run:
                web_security_path.write_text(WEB_SECURITY_HEADERS)
                self.files_updated += 1
            else:
                self._log(f"Would enhance Web security headers at {web_security_path} (dry run)")
        else:
            logger.info(f"Creating Web security headers at {web_security_path}")

            # Create directory if it doesn't exist
            web_security_path.parent.mkdir(parents=True, exist_ok=True)

            if not self.dry_run:
                web_security_path.write_text(WEB_SECURITY_HEADERS)
                self.files_updated += 1
            else:
                self._log(f"Would create Web security headers at {web_security_path} (dry run)")

    def _create_security_dashboard(self):
        """Create security monitoring dashboard."""
        # This would typically involve creating a Grafana dashboard JSON
        # For now, we'll just log that this would be done
        logger.info("Creating security monitoring dashboard")

        if not self.dry_run:
            # In a real implementation, this would create a dashboard JSON file
            self._log("Would create security dashboard (not implemented in this version)")
        else:
            self._log("Would create security dashboard (dry run)")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Enhance security monitoring in the Maily platform.")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without applying them")
    parser.add_argument("--verbose", action="store_true", help="Show detailed information during execution")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    enhancer = SecurityMonitoringEnhancer(dry_run=args.dry_run, verbose=args.verbose)

    if args.dry_run:
        logger.info("Dry run mode. No changes will be applied.")

    enhancer.enhance_security_monitoring()


if __name__ == "__main__":
    main()
