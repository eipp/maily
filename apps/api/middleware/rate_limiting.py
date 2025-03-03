"""
Advanced rate limiting middleware with adaptive quotas, client fingerprinting, and burst detection.

This module provides sophisticated rate limiting capabilities:
1. Token bucket algorithm for rate limiting
2. Tiered rate limits based on API key authentication
3. Path-based rate limiting for specific high-load endpoints
4. Daily quota tracking with automatic reset
5. Client fingerprinting to prevent circumvention
6. Adaptive rate limiting based on server load
7. IP reputation tracking to penalize bad actors
"""

import time
import logging
import hashlib
import uuid
import re
import math
import json
import asyncio
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple, Any, Callable, Union

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Configure logging
logger = logging.getLogger(__name__)

# Rate limit tiers (requests per second, daily quota, burst limit)
RATE_LIMIT_TIERS = {
    # Key: (rps, daily_quota, burst_allowed, burst_rate)
    "unauthenticated": (5, 1000, False, 0),
    "free": (10, 5000, True, 20),
    "basic": (30, 50000, True, 60),
    "premium": (100, 250000, True, 200),
    "enterprise": (300, 1000000, True, 600),
}

# Default tier for unauthenticated requests
DEFAULT_TIER = "unauthenticated"

# Special endpoint rate limits - override the tier settings
ENDPOINT_RATE_LIMITS = {
    # High resource endpoints get stricter limits
    "/api/v1/ai/generate": {
        "unauthenticated": (2, 100, False, 0),
        "free": (3, 500, False, 0),
        "basic": (10, 5000, True, 20),
        "premium": (30, 25000, True, 60),
        "enterprise": (100, 100000, True, 200),
    },
    "/api/v1/campaigns/bulk": {
        "unauthenticated": (1, 50, False, 0),
        "free": (2, 200, False, 0),
        "basic": (5, 2000, True, 10),
        "premium": (20, 10000, True, 40),
        "enterprise": (50, 50000, True, 100),
    }
}

# Exempt paths that don't count towards rate limits
EXEMPT_PATHS = ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]

# Define a grace factor for high load situations
LOAD_ADAPTIVE_FACTOR = 0.5  # Reduce rate limits by 50% under high load

# IP Reputation penalty duration
REPUTATION_PENALTY_DURATION = 24 * 60 * 60  # 24 hours in seconds
MAX_VIOLATIONS_BEFORE_PENALTY = 5
VIOLATION_RESET_PERIOD = 60 * 60  # 1 hour in seconds


class QuotaTracker:
    """Tracks daily API usage quotas for users."""
    
    def __init__(self):
        """Initialize the quota tracker."""
        self.daily_quotas = defaultdict(int)  # {user_key: usage_count}
        self.last_reset = datetime.now(timezone.utc).date()
    
    def increment(self, key: str, amount: int = 1) -> Tuple[int, int]:
        """
        Increment the usage count for a key and return current usage and quota.
        
        Args:
            key: The user identifier
            amount: The amount to increment by
            
        Returns:
            Tuple of (current_usage, daily_quota)
        """
        # Reset quotas if it's a new day
        self._check_reset()
        
        # Get the tier for this key
        tier = get_user_tier(key)
        _, daily_quota, _, _ = RATE_LIMIT_TIERS.get(tier, RATE_LIMIT_TIERS[DEFAULT_TIER])
        
        # Increment the usage
        self.daily_quotas[key] += amount
        
        return self.daily_quotas[key], daily_quota
    
    def get_usage(self, key: str) -> Tuple[int, int]:
        """
        Get the current usage and quota for a key.
        
        Args:
            key: The user identifier
            
        Returns:
            Tuple of (current_usage, daily_quota)
        """
        # Reset quotas if it's a new day
        self._check_reset()
        
        # Get the tier for this key
        tier = get_user_tier(key)
        _, daily_quota, _, _ = RATE_LIMIT_TIERS.get(tier, RATE_LIMIT_TIERS[DEFAULT_TIER])
        
        return self.daily_quotas.get(key, 0), daily_quota
    
    def _check_reset(self):
        """Reset all quotas if it's a new day (UTC)."""
        today = datetime.now(timezone.utc).date()
        if today > self.last_reset:
            logger.info(f"Resetting daily quotas at {today}")
            self.daily_quotas.clear()
            self.last_reset = today


class IPReputationTracker:
    """Tracks IP reputation and applies penalties for suspicious behavior."""
    
    def __init__(self):
        """Initialize the IP reputation tracker."""
        self.violations = defaultdict(list)  # {ip: [timestamps]}
        self.penalties = {}  # {ip: expiry_timestamp}
        self.last_cleanup = time.time()
    
    def record_violation(self, ip: str) -> bool:
        """
        Record a violation for an IP and determine if a penalty should be applied.
        
        Args:
            ip: The IP address
            
        Returns:
            True if penalty should be applied, False otherwise
        """
        now = time.time()
        
        # Clean up expired data periodically
        if now - self.last_cleanup > 300:  # Every 5 minutes
            self._cleanup()
            self.last_cleanup = now
        
        # Check if IP is already penalized
        if ip in self.penalties and self.penalties[ip] > now:
            return True
        
        # Add current violation
        self.violations[ip].append(now)
        
        # Filter recent violations only
        cutoff = now - VIOLATION_RESET_PERIOD
        self.violations[ip] = [t for t in self.violations[ip] if t > cutoff]
        
        # Check if threshold exceeded
        if len(self.violations[ip]) >= MAX_VIOLATIONS_BEFORE_PENALTY:
            # Apply penalty
            self.penalties[ip] = now + REPUTATION_PENALTY_DURATION
            logger.warning(f"Applied rate limit penalty to IP {ip} for {REPUTATION_PENALTY_DURATION//3600} hours")
            return True
        
        return False
    
    def is_penalized(self, ip: str) -> bool:
        """
        Check if an IP is currently penalized.
        
        Args:
            ip: The IP address
            
        Returns:
            True if penalized, False otherwise
        """
        now = time.time()
        return ip in self.penalties and self.penalties[ip] > now
    
    def get_violation_count(self, ip: str) -> int:
        """
        Get the number of recent violations for an IP.
        
        Args:
            ip: The IP address
            
        Returns:
            The number of recent violations
        """
        now = time.time()
        cutoff = now - VIOLATION_RESET_PERIOD
        return len([t for t in self.violations.get(ip, []) if t > cutoff])
    
    def _cleanup(self):
        """Clean up expired violations and penalties."""
        now = time.time()
        
        # Clean up violations
        cutoff = now - VIOLATION_RESET_PERIOD
        for ip in list(self.violations.keys()):
            self.violations[ip] = [t for t in self.violations[ip] if t > cutoff]
            if not self.violations[ip]:
                del self.violations[ip]
        
        # Clean up penalties
        for ip in list(self.penalties.keys()):
            if self.penalties[ip] <= now:
                del self.penalties[ip]


def get_user_tier(key: str) -> str:
    """
    Determine the rate limit tier based on the API key.
    
    In a production system, this would look up the tier in a database or cache.
    This is a simplified version for demonstration.
    
    Args:
        key: The API key or user identifier
        
    Returns:
        The rate limit tier
    """
    if not key or key == "unauthenticated":
        return "unauthenticated"
    
    # In a real system, this would query a database
    # This is a simplified version for testing purposes
    if key.startswith("test_free_"):
        return "free"
    elif key.startswith("test_basic_"):
        return "basic"
    elif key.startswith("test_premium_"):
        return "premium"
    elif key.startswith("test_enterprise_"):
        return "enterprise"
    
    # Default to free tier for unknown keys
    return "free"


def get_client_fingerprint(request: Request) -> str:
    """
    Generate a client fingerprint from request attributes.
    
    This helps identify clients even if they change IP addresses.
    
    Args:
        request: The request object
        
    Returns:
        A fingerprint string
    """
    # Gather fingerprinting data
    components = []
    
    # User agent is the most stable identifier
    user_agent = request.headers.get("user-agent", "")
    components.append(f"ua:{user_agent}")
    
    # Accept headers can help identify the client
    accept = request.headers.get("accept", "")
    accept_encoding = request.headers.get("accept-encoding", "")
    accept_language = request.headers.get("accept-language", "")
    components.append(f"a:{accept[:50]}")
    components.append(f"ae:{accept_encoding[:20]}")
    components.append(f"al:{accept_language[:20]}")
    
    # IP address (least reliable but still useful)
    ip = _get_client_ip(request)
    components.append(f"ip:{ip}")
    
    # Use a subset of headers to create a reasonably unique fingerprint
    # Create hash of the components
    fingerprint = hashlib.sha256(":".join(components).encode()).hexdigest()
    
    return fingerprint


def _get_client_ip(request: Request) -> str:
    """
    Extract the client IP address from the request.
    
    Args:
        request: The request object
        
    Returns:
        The client IP address
    """
    # Try to get IP from X-Forwarded-For header
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # The client IP is the first address in the list
        return forwarded_for.split(",")[0].strip()
    
    # Fall back to request.client.host
    return request.client.host if request.client else "unknown"


def is_exempt_path(path: str) -> bool:
    """
    Check if a path is exempt from rate limiting.
    
    Args:
        path: The request path
        
    Returns:
        True if exempt, False otherwise
    """
    return any(path.startswith(exempt) for exempt in EXEMPT_PATHS)


def get_endpoint_limits(path: str, tier: str) -> Tuple[float, int, bool, float]:
    """
    Get rate limits for a specific endpoint and tier.
    
    Args:
        path: The request path
        tier: The user tier
        
    Returns:
        Tuple of (requests_per_second, daily_quota, burst_allowed, burst_rate)
    """
    # Check for endpoint-specific limits
    for endpoint, limits in ENDPOINT_RATE_LIMITS.items():
        if path.startswith(endpoint):
            return limits.get(tier, limits.get(DEFAULT_TIER, RATE_LIMIT_TIERS[DEFAULT_TIER]))
    
    # Use default tier limits
    return RATE_LIMIT_TIERS.get(tier, RATE_LIMIT_TIERS[DEFAULT_TIER])


class TokenBucket:
    """Token bucket algorithm for rate limiting with burst support."""
    
    def __init__(self, rate: float, capacity: float):
        """
        Initialize a token bucket.
        
        Args:
            rate: Token refill rate per second
            capacity: Maximum bucket size
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.time()
    
    def consume(self, tokens: float = 1.0) -> bool:
        """
        Consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False if not enough tokens
        """
        # Refill the bucket based on elapsed time
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now
        
        # Check if we have enough tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Advanced rate limiting middleware with tiered limits and quotas."""
    
    def __init__(
        self,
        app: ASGIApp,
        api_key_header: str = "X-API-Key",
        default_rps: float = 5.0,
        default_quota: int = 1000,
        enable_client_fingerprinting: bool = True,
        enable_adaptive_limits: bool = True,
        enable_reputation_tracking: bool = True,
    ):
        """
        Initialize the rate limit middleware.
        
        Args:
            app: The ASGI application
            api_key_header: The header name for API keys
            default_rps: Default requests per second for unauthenticated users
            default_quota: Default daily quota for unauthenticated users
            enable_client_fingerprinting: Whether to use client fingerprinting
            enable_adaptive_limits: Whether to adjust limits based on server load
            enable_reputation_tracking: Whether to track and penalize suspicious IPs
        """
        super().__init__(app)
        self.api_key_header = api_key_header
        self.default_rps = default_rps
        self.default_quota = default_quota
        self.enable_client_fingerprinting = enable_client_fingerprinting
        self.enable_adaptive_limits = enable_adaptive_limits
        self.enable_reputation_tracking = enable_reputation_tracking
        
        # Initialize rate limiters
        self.buckets = {}  # {key: TokenBucket}
        
        # Initialize quota tracker
        self.quota_tracker = QuotaTracker()
        
        # Initialize IP reputation tracker
        self.reputation_tracker = IPReputationTracker()
        
        # For tracking system load
        self.current_load_factor = 1.0
        self.request_times = []
        self.last_load_check = time.time()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process a request with rate limiting.
        
        Args:
            request: The request to process
            call_next: The next middleware to call
            
        Returns:
            The response
        """
        # Skip rate limiting for exempt paths
        if is_exempt_path(request.url.path):
            return await call_next(request)
        
        # Get client identifiers
        client_ip = _get_client_ip(request)
        api_key = request.headers.get(self.api_key_header, "")
        
        # Use client fingerprint if enabled
        if self.enable_client_fingerprinting:
            client_id = get_client_fingerprint(request)
        else:
            client_id = api_key if api_key else client_ip
        
        # Check IP reputation if enabled
        if self.enable_reputation_tracking and self.reputation_tracker.is_penalized(client_ip):
            logger.warning(f"Request denied due to IP reputation penalty: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded due to previous violations",
                    "retry_after": int(time.time() - self.reputation_tracker.penalties[client_ip]),
                }
            )
        
        # Get user tier based on API key
        tier = get_user_tier(api_key)
        
        # Get appropriate limits for this endpoint and tier
        rps, daily_quota, burst_allowed, burst_rate = get_endpoint_limits(request.url.path, tier)
        
        # Apply adaptive limits if enabled
        if self.enable_adaptive_limits:
            self._update_load_factor()
            adjusted_rps = rps * self.current_load_factor
            if adjusted_rps < rps:
                logger.debug(f"Adjusting rate limit due to load: {rps} -> {adjusted_rps:.2f}")
                rps = adjusted_rps
        
        # Check daily quota
        current_usage, quota_limit = self.quota_tracker.get_usage(client_id)
        if current_usage >= quota_limit:
            # Record violation for IP reputation
            if self.enable_reputation_tracking:
                self.reputation_tracker.record_violation(client_ip)
            
            # Return quota exceeded response
            retry_after = self._get_seconds_until_midnight()
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Daily API quota exceeded",
                    "limit": quota_limit,
                    "current": current_usage,
                    "retry_after": retry_after,
                }
            )
        
        # Get or create token bucket
        if client_id not in self.buckets:
            capacity = burst_rate if burst_allowed else rps
            self.buckets[client_id] = TokenBucket(rps, capacity)
        
        # Try to consume a token
        if not self.buckets[client_id].consume():
            # Record violation for IP reputation
            if self.enable_reputation_tracking:
                self.reputation_tracker.record_violation(client_ip)
            
            # Return rate limit exceeded response
            retry_after = int(1.0 / rps)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "limit": rps,
                    "retry_after": retry_after,
                }
            )
        
        # Process the request and track timing
        start_time = time.time()
        response = await call_next(request)
        request_time = time.time() - start_time
        
        # Update quota usage
        self.quota_tracker.increment(client_id)
        
        # Add rate limit headers to response
        tier_rps, tier_quota, _, _ = RATE_LIMIT_TIERS.get(tier, RATE_LIMIT_TIERS[DEFAULT_TIER])
        current_usage, _ = self.quota_tracker.get_usage(client_id)
        
        response.headers["X-RateLimit-Limit"] = str(tier_rps)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.buckets[client_id].tokens))
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + (1.0 / tier_rps)))
        response.headers["X-Daily-Quota-Limit"] = str(tier_quota)
        response.headers["X-Daily-Quota-Remaining"] = str(max(0, tier_quota - current_usage))
        response.headers["X-Daily-Quota-Reset"] = str(self._get_seconds_until_midnight())
        
        # Store request timing for load calculation
        if self.enable_adaptive_limits:
            self._add_request_time(request_time)
        
        return response
    
    def _get_seconds_until_midnight(self) -> int:
        """
        Calculate seconds until midnight UTC.
        
        Returns:
            Seconds until midnight
        """
        now = datetime.now(timezone.utc)
        midnight = datetime(
            now.year, now.month, now.day, tzinfo=timezone.utc
        ) + timedelta(days=1)
        return int((midnight - now).total_seconds())
    
    def _add_request_time(self, request_time: float):
        """
        Add a request time to the history for load calculation.
        
        Args:
            request_time: The request processing time in seconds
        """
        now = time.time()
        cutoff = now - 60  # Keep the last minute of data
        
        # Add new timing data
        self.request_times.append((now, request_time))
        
        # Remove old data
        self.request_times = [(t, rt) for t, rt in self.request_times if t > cutoff]
    
    def _update_load_factor(self):
        """Update the load factor based on recent request times."""
        now = time.time()
        
        # Only update every 5 seconds
        if now - self.last_load_check < 5:
            return
        
        self.last_load_check = now
        
        # Skip if not enough data
        if len(self.request_times) < 10:
            self.current_load_factor = 1.0
            return
        
        # Calculate the 90th percentile request time
        request_times = [rt for _, rt in self.request_times]
        request_times.sort()
        p90_index = int(len(request_times) * 0.9)
        p90_time = request_times[p90_index]
        
        # Calculate load factor (higher times = lower factor)
        # A reasonable threshold might be 500ms
        # If p90 is > 500ms, we start reducing the factor
        if p90_time > 0.5:  # 500ms
            # Logarithmic reduction to avoid sudden changes
            self.current_load_factor = max(LOAD_ADAPTIVE_FACTOR, 1.0 / (1.0 + math.log(p90_time * 2)))
        else:
            # Gradually return to normal
            self.current_load_factor = min(1.0, self.current_load_factor + 0.05)
        
        logger.debug(f"Current load factor: {self.current_load_factor:.2f} (p90 time: {p90_time*1000:.1f}ms)")


def add_rate_limiting_middleware(app, **kwargs):
    """
    Add rate limiting middleware to an application.
    
    Args:
        app: The FastAPI application
        **kwargs: Additional keyword arguments for RateLimitMiddleware
        
    Returns:
        The application with rate limiting middleware
    """
    app.add_middleware(RateLimitMiddleware, **kwargs)
    return app
