#!/usr/bin/env python3
"""
Redis diagnostics tool for Maily Redis infrastructure.
Tests connection to Redis, examines cache usage, and checks Redis memory stats.
"""

import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Add project paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../apps/api')))

try:
    # Import Redis client and settings
    import redis
    from config.settings import get_settings
except ImportError:
    print("Failed to import project modules. Make sure you're running from the project root.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("redis-diagnostics")

# Get settings
settings = get_settings()

class RedisDiagnostics:
    """Diagnostic tool for Redis services."""

    def __init__(self, verbose: bool = False):
        """Initialize the diagnostics tool.

        Args:
            verbose: Whether to enable verbose output
        """
        self.verbose = verbose
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "environment": os.environ.get("ENVIRONMENT", "development"),
            "tests": {},
            "summary": {
                "passed": 0,
                "failed": 0,
                "warnings": 0,
                "skipped": 0
            }
        }

        # Initialize Redis client
        self.redis_url = os.environ.get("REDIS_URL", f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}")
        self.redis_password = os.environ.get("REDIS_PASSWORD", settings.REDIS_PASSWORD)
        self.redis_ssl = os.environ.get("REDIS_SSL", "false").lower() == "true"

        self.results["config"] = {
            "redis_url": self.mask_connection_string(self.redis_url),
            "redis_ssl": self.redis_ssl,
            "host": settings.REDIS_HOST,
            "port": settings.REDIS_PORT,
            "db": settings.REDIS_DB
        }

        try:
            self.redis = redis.from_url(
                self.redis_url,
                password=self.redis_password,
                ssl=self.redis_ssl,
                socket_timeout=5.0,
                socket_connect_timeout=2.0,
                health_check_interval=30,
                decode_responses=True,
            )
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            self.redis = None

    def mask_connection_string(self, url: str) -> str:
        """Mask sensitive information in a connection string.

        Args:
            url: Connection string to mask

        Returns:
            Masked connection string
        """
        if not url:
            return ""

        # Mask password in Redis URL
        if "@" in url:
            proto_auth, host_port = url.split("@", 1)

            if "://" in proto_auth:
                protocol, auth = proto_auth.split("://", 1)

                if ":" in auth:
                    username, _ = auth.split(":", 1)
                    return f"{protocol}://{username}:****@{host_port}"

            return f"{proto_auth.split(':')[0]}:****@{host_port}"

        return url

    async def run_diagnostics(self) -> Dict[str, Any]:
        """Run all diagnostic tests.

        Returns:
            Dictionary of test results
        """
        logger.info("Starting Redis diagnostics")

        # Connection test
        await self.test_redis_connection()

        # Skip remaining tests if connection failed
        if not self.redis:
            logger.warning("Skipping remaining tests as Redis connection failed")
            return self.results

        # Run tests
        await self.test_memory_usage()
        await self.test_key_space()
        await self.test_persistence()
        await self.test_performance()
        await self.test_expiry_policy()
        await self.test_eviction_policy()
        await self.test_cache_hit_rate()

        # Generate summary
        self.summarize_results()

        return self.results

    def record_result(self, test_name: str, status: str, message: str, details: Any = None) -> None:
        """Record a test result.

        Args:
            test_name: Name of the test
            status: "passed", "failed", "warning", or "skipped"
            message: Result message
            details: Additional details (optional)
        """
        self.results["tests"][test_name] = {
            "status": status,
            "message": message,
        }

        if details:
            self.results["tests"][test_name]["details"] = details

        # Update summary counters
        if status == "passed":
            self.results["summary"]["passed"] += 1
        elif status == "failed":
            self.results["summary"]["failed"] += 1
        elif status == "warning":
            self.results["summary"]["warnings"] += 1
        elif status == "skipped":
            self.results["summary"]["skipped"] += 1

        # Log result
        if status == "passed":
            logger.info(f"✅ {test_name}: {message}")
        elif status == "failed":
            logger.error(f"❌ {test_name}: {message}")
        elif status == "warning":
            logger.warning(f"⚠️ {test_name}: {message}")
        else:
            logger.info(f"⏭️ {test_name}: {message}")

    async def test_redis_connection(self) -> None:
        """Test connection to Redis."""
        if not self.redis:
            self.record_result(
                "redis_connection",
                "failed",
                "Failed to initialize Redis client"
            )
            return

        try:
            # Measure connection time
            start_time = time.time()
            pong = self.redis.ping()
            connection_time = time.time() - start_time

            if not pong:
                self.record_result(
                    "redis_connection",
                    "failed",
                    f"Failed to connect to Redis at {self.mask_connection_string(self.redis_url)}"
                )
                return

            # Get Redis info
            info = self.redis.info()

            details = {
                "version": info.get("redis_version"),
                "uptime_days": round(info.get("uptime_in_seconds", 0) / 86400, 1),
                "connection_time_ms": round(connection_time * 1000, 2),
                "mode": info.get("redis_mode", "standalone"),
                "os": info.get("os", "unknown"),
                "connected_clients": info.get("connected_clients"),
                "expired_keys": info.get("expired_keys"),
                "evicted_keys": info.get("evicted_keys")
            }

            self.record_result(
                "redis_connection",
                "passed",
                f"Successfully connected to Redis {info.get('redis_version')} in {round(connection_time * 1000, 2)}ms",
                details
            )

            # Record Redis info for other tests
            self.redis_info = info

        except Exception as e:
            self.record_result(
                "redis_connection",
                "failed",
                f"Error connecting to Redis: {str(e)}"
            )
            self.redis = None

    async def test_memory_usage(self) -> None:
        """Test Redis memory usage."""
        if not self.redis or not hasattr(self, 'redis_info'):
            self.record_result(
                "memory_usage",
                "skipped",
                "Redis connection not available"
            )
            return

        try:
            # Get memory usage from info
            used_memory = self.redis_info.get("used_memory", 0)
            used_memory_human = self.redis_info.get("used_memory_human", "0B")
            used_memory_peak = self.redis_info.get("used_memory_peak", 0)
            used_memory_peak_human = self.redis_info.get("used_memory_peak_human", "0B")
            used_memory_rss = self.redis_info.get("used_memory_rss", 0)
            used_memory_rss_human = self.redis_info.get("used_memory_rss_human", "0B")

            mem_fragmentation_ratio = self.redis_info.get("mem_fragmentation_ratio", 0)
            maxmemory = self.redis_info.get("maxmemory", 0)
            maxmemory_human = self.format_bytes(maxmemory)

            if maxmemory > 0:
                memory_usage_pct = (used_memory / maxmemory) * 100
            else:
                memory_usage_pct = 0

            details = {
                "used_memory": used_memory,
                "used_memory_human": used_memory_human,
                "used_memory_peak": used_memory_peak,
                "used_memory_peak_human": used_memory_peak_human,
                "used_memory_rss": used_memory_rss,
                "used_memory_rss_human": used_memory_rss_human,
                "mem_fragmentation_ratio": mem_fragmentation_ratio,
                "maxmemory": maxmemory,
                "maxmemory_human": maxmemory_human,
                "memory_usage_pct": round(memory_usage_pct, 2)
            }

            # Check memory usage
            if maxmemory > 0 and memory_usage_pct > 90:
                self.record_result(
                    "memory_usage",
                    "warning",
                    f"Redis memory usage is high: {round(memory_usage_pct, 2)}% of {maxmemory_human}",
                    details
                )
                return

            # Check memory fragmentation
            if mem_fragmentation_ratio > 1.5:
                self.record_result(
                    "memory_usage",
                    "warning",
                    f"Redis memory fragmentation ratio is high: {mem_fragmentation_ratio}",
                    details
                )
                return

            # Check if maxmemory is set
            if maxmemory == 0:
                self.record_result(
                    "memory_usage",
                    "warning",
                    "Redis maxmemory is not set. This could lead to unconstrained memory growth.",
                    details
                )
                return

            self.record_result(
                "memory_usage",
                "passed",
                f"Redis memory usage is normal: {round(memory_usage_pct, 2)}% of {maxmemory_human}",
                details
            )

        except Exception as e:
            self.record_result(
                "memory_usage",
                "failed",
                f"Error checking memory usage: {str(e)}"
            )

    def format_bytes(self, size_bytes: int) -> str:
        """Format bytes to human-readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            Human-readable string
        """
        if size_bytes == 0:
            return "0B"

        size_name = ("B", "KB", "MB", "GB", "TB", "PB")
        i = 0
        while size_bytes >= 1024 and i < len(size_name) - 1:
            size_bytes /= 1024
            i += 1

        return f"{round(size_bytes, 2)}{size_name[i]}"

    async def test_key_space(self) -> None:
        """Test Redis key space usage."""
        if not self.redis:
            self.record_result(
                "key_space",
                "skipped",
                "Redis connection not available"
            )
            return

        try:
            # Get key counts
            db_keys = {}
            keyspace = {k: v for k, v in self.redis_info.items() if k.startswith("db")}

            for db, stats in keyspace.items():
                db_keys[db] = stats.get("keys", 0)

            # Get key patterns (sample)
            maily_keys = len(self.redis.keys("maily:*"))
            campaign_keys = len(self.redis.keys("maily:*:campaign:*"))
            analytics_keys = len(self.redis.keys("maily:*:analytics:*"))
            user_keys = len(self.redis.keys("maily:*:user:*"))
            rate_limit_keys = len(self.redis.keys("maily:*:rate_limit:*"))

            total_keys = sum(db_keys.values())

            details = {
                "total_keys": total_keys,
                "db_keys": db_keys,
                "maily_keys": maily_keys,
                "campaign_keys": campaign_keys,
                "analytics_keys": analytics_keys,
                "user_keys": user_keys,
                "rate_limit_keys": rate_limit_keys
            }

            # Check for over-large key space
            if total_keys > 1000000:  # 1M keys
                self.record_result(
                    "key_space",
                    "warning",
                    f"Redis contains a very large number of keys: {total_keys}",
                    details
                )
                return

            self.record_result(
                "key_space",
                "passed",
                f"Redis key space is normal: {total_keys} total keys",
                details
            )

        except Exception as e:
            self.record_result(
                "key_space",
                "failed",
                f"Error checking key space: {str(e)}"
            )

    async def test_persistence(self) -> None:
        """Test Redis persistence configuration."""
        if not self.redis or not hasattr(self, 'redis_info'):
            self.record_result(
                "persistence",
                "skipped",
                "Redis connection not available"
            )
            return

        try:
            # Check RDB and AOF configuration
            rdb_last_save = self.redis_info.get("rdb_last_save_time", 0)
            rdb_changes_since = self.redis_info.get("rdb_changes_since_last_save", 0)
            rdb_last_save_time = datetime.fromtimestamp(rdb_last_save).isoformat() if rdb_last_save else "never"

            aof_enabled = self.redis_info.get("aof_enabled", 0) == 1
            aof_rewrite_in_progress = self.redis_info.get("aof_rewrite_in_progress", 0) == 1
            aof_rewrite_scheduled = self.redis_info.get("aof_rewrite_scheduled", 0) == 1

            details = {
                "rdb_last_save_time": rdb_last_save_time,
                "rdb_changes_since_last_save": rdb_changes_since,
                "aof_enabled": aof_enabled,
                "aof_rewrite_in_progress": aof_rewrite_in_progress,
                "aof_rewrite_scheduled": aof_rewrite_scheduled
            }

            # Check persistence settings
            now = time.time()
            time_since_save = now - rdb_last_save if rdb_last_save else None

            if not aof_enabled and (time_since_save is None or time_since_save > 86400):  # 24 hours
                self.record_result(
                    "persistence",
                    "warning",
                    "Redis has not saved data in over 24 hours, and AOF is disabled",
                    details
                )
                return

            if not aof_enabled and rdb_changes_since > 10000:
                self.record_result(
                    "persistence",
                    "warning",
                    f"Redis has {rdb_changes_since} changes since last save, and AOF is disabled",
                    details
                )
                return

            persistence_type = "AOF enabled" if aof_enabled else "RDB only"
            self.record_result(
                "persistence",
                "passed",
                f"Redis persistence configuration is good: {persistence_type}",
                details
            )

        except Exception as e:
            self.record_result(
                "persistence",
                "failed",
                f"Error checking persistence: {str(e)}"
            )

    async def test_performance(self) -> None:
        """Test Redis performance."""
        if not self.redis:
            self.record_result(
                "performance",
                "skipped",
                "Redis connection not available"
            )
            return

        try:
            # Perform simple benchmarks
            results = {}

            # SET benchmark
            start_time = time.time()
            for i in range(100):
                self.redis.set(f"maily:benchmark:set:{i}", f"value_{i}")
            set_time = time.time() - start_time

            # GET benchmark
            start_time = time.time()
            for i in range(100):
                self.redis.get(f"maily:benchmark:set:{i}")
            get_time = time.time() - start_time

            # Pipeline benchmark
            start_time = time.time()
            pipe = self.redis.pipeline()
            for i in range(100):
                pipe.set(f"maily:benchmark:pipe:{i}", f"value_{i}")
            pipe.execute()
            pipeline_time = time.time() - start_time

            # Clean up
            self.redis.delete(*[f"maily:benchmark:set:{i}" for i in range(100)])
            self.redis.delete(*[f"maily:benchmark:pipe:{i}" for i in range(100)])

            # Commands per second from Redis info
            commands_processed = self.redis_info.get("total_commands_processed", 0)
            uptime = self.redis_info.get("uptime_in_seconds", 1)
            commands_per_second = commands_processed / uptime if uptime > 0 else 0

            # Keyspace hits/misses
            keyspace_hits = self.redis_info.get("keyspace_hits", 0)
            keyspace_misses = self.redis_info.get("keyspace_misses", 0)
            total_keyspace_requests = keyspace_hits + keyspace_misses
            hit_rate = keyspace_hits / total_keyspace_requests if total_keyspace_requests > 0 else 0

            details = {
                "set_ops_per_second": round(100 / set_time if set_time > 0 else 0, 2),
                "get_ops_per_second": round(100 / get_time if get_time > 0 else 0, 2),
                "pipeline_ops_per_second": round(100 / pipeline_time if pipeline_time > 0 else 0, 2),
                "commands_per_second": round(commands_per_second, 2),
                "hit_rate": round(hit_rate * 100, 2),
                "keyspace_hits": keyspace_hits,
                "keyspace_misses": keyspace_misses
            }

            # Check for slow Redis
            if details["set_ops_per_second"] < 1000 or details["get_ops_per_second"] < 1000:
                self.record_result(
                    "performance",
                    "warning",
                    f"Redis performance is slower than expected: {details['set_ops_per_second']} SET/s, {details['get_ops_per_second']} GET/s",
                    details
                )
                return

            self.record_result(
                "performance",
                "passed",
                f"Redis performance is good: {details['set_ops_per_second']} SET/s, {details['get_ops_per_second']} GET/s, {details['hit_rate']}% hit rate",
                details
            )

        except Exception as e:
            self.record_result(
                "performance",
                "failed",
                f"Error testing performance: {str(e)}"
            )

    async def test_eviction_policy(self) -> None:
        """Test Redis eviction policy."""
        if not self.redis or not hasattr(self, 'redis_info'):
            self.record_result(
                "eviction_policy",
                "skipped",
                "Redis connection not available"
            )
            return

        try:
            # Get eviction policy and stats
            maxmemory_policy = self.redis_info.get("maxmemory_policy", "noeviction")
            evicted_keys = self.redis_info.get("evicted_keys", 0)
            expired_keys = self.redis_info.get("expired_keys", 0)

            details = {
                "maxmemory_policy": maxmemory_policy,
                "evicted_keys": evicted_keys,
                "expired_keys": expired_keys
            }

            # Check if policy is appropriate for a cache
            recommended_policies = ["allkeys-lru", "volatile-lru", "allkeys-lfu", "volatile-lfu"]

            if maxmemory_policy not in recommended_policies:
                self.record_result(
                    "eviction_policy",
                    "warning",
                    f"Redis is using '{maxmemory_policy}' eviction policy, which may not be optimal for caching",
                    details
                )
                return

            # Check if there have been a lot of evictions
            uptime = self.redis_info.get("uptime_in_seconds", 0)
            eviction_rate = evicted_keys / uptime if uptime > 0 else 0

            if eviction_rate > 1:  # More than 1 eviction per second
                self.record_result(
                    "eviction_policy",
                    "warning",
                    f"Redis has a high eviction rate: {round(eviction_rate, 2)} keys/second",
                    details
                )
                return

            self.record_result(
                "eviction_policy",
                "passed",
                f"Redis eviction policy is appropriate: {maxmemory_policy}",
                details
            )

        except Exception as e:
            self.record_result(
                "eviction_policy",
                "failed",
                f"Error checking eviction policy: {str(e)}"
            )

    async def test_expiry_policy(self) -> None:
        """Test Redis key expiry."""
        if not self.redis:
            self.record_result(
                "expiry_policy",
                "skipped",
                "Redis connection not available"
            )
            return

        try:
            # Check expiry by sampling some keys
            sample_prefixes = [
                "maily:prod:campaign:",
                "maily:prod:user:",
                "maily:prod:analytics:",
                "maily:prod:rate_limit:"
            ]

            results = {}

            for prefix in sample_prefixes:
                keys = self.redis.keys(f"{prefix}*")[:100]  # Sample up to 100 keys

                if not keys:
                    results[prefix] = {
                        "total": 0,
                        "with_ttl": 0,
                        "ttl_pct": 0,
                        "avg_ttl": 0
                    }
                    continue

                with_ttl = 0
                ttl_sum = 0

                for key in keys:
                    ttl = self.redis.ttl(key)
                    if ttl > 0:
                        with_ttl += 1
                        ttl_sum += ttl

                ttl_pct = (with_ttl / len(keys)) * 100
                avg_ttl = ttl_sum / with_ttl if with_ttl > 0 else 0

                results[prefix] = {
                    "total": len(keys),
                    "with_ttl": with_ttl,
                    "ttl_pct": round(ttl_pct, 2),
                    "avg_ttl": round(avg_ttl, 2)
                }

            details = results

            # Check for keys without TTL
            problem_prefixes = []
            for prefix, stats in results.items():
                if stats["total"] > 0 and stats["ttl_pct"] < 80:
                    problem_prefixes.append(f"{prefix} ({stats['ttl_pct']}%)")

            if problem_prefixes:
                self.record_result(
                    "expiry_policy",
                    "warning",
                    f"Some key prefixes have low TTL coverage: {', '.join(problem_prefixes)}",
                    details
                )
                return

            self.record_result(
                "expiry_policy",
                "passed",
                "Redis keys have appropriate expiry times",
                details
            )

        except Exception as e:
            self.record_result(
                "expiry_policy",
                "failed",
                f"Error checking expiry policy: {str(e)}"
            )

    async def test_cache_hit_rate(self) -> None:
        """Test Redis cache hit rate."""
        if not self.redis or not hasattr(self, 'redis_info'):
            self.record_result(
                "cache_hit_rate",
                "skipped",
                "Redis connection not available"
            )
            return

        try:
            # Get hit/miss stats
            keyspace_hits = self.redis_info.get("keyspace_hits", 0)
            keyspace_misses = self.redis_info.get("keyspace_misses", 0)
            total_requests = keyspace_hits + keyspace_misses

            if total_requests == 0:
                self.record_result(
                    "cache_hit_rate",
                    "skipped",
                    "No cache access data available"
                )
                return

            hit_rate = (keyspace_hits / total_requests) * 100

            details = {
                "keyspace_hits": keyspace_hits,
                "keyspace_misses": keyspace_misses,
                "total_requests": total_requests,
                "hit_rate": round(hit_rate, 2)
            }

            # Check hit rate
            if hit_rate < 50:
                self.record_result(
                    "cache_hit_rate",
                    "warning",
                    f"Redis cache hit rate is low: {round(hit_rate, 2)}%",
                    details
                )
                return

            self.record_result(
                "cache_hit_rate",
                "passed",
                f"Redis cache hit rate is good: {round(hit_rate, 2)}%",
                details
            )

        except Exception as e:
            self.record_result(
                "cache_hit_rate",
                "failed",
                f"Error checking cache hit rate: {str(e)}"
            )

    def summarize_results(self) -> None:
        """Generate a summary of test results."""
        total_tests = sum(self.results["summary"].values())

        if self.results["summary"]["failed"] > 0:
            status = "FAILED"
        elif self.results["summary"]["warnings"] > 0:
            status = "WARNING"
        else:
            status = "PASSED"

        self.results["overall_status"] = status

        failed_tests = [
            name for name, result in self.results["tests"].items()
            if result["status"] == "failed"
        ]

        warning_tests = [
            name for name, result in self.results["tests"].items()
            if result["status"] == "warning"
        ]

        self.results["summary"]["total"] = total_tests
        self.results["summary"]["failed_tests"] = failed_tests
        self.results["summary"]["warning_tests"] = warning_tests

        logger.info(f"Redis diagnostics completed: {status}")
        logger.info(f"Total tests: {total_tests}")
        logger.info(f"Passed: {self.results['summary']['passed']}")
        logger.info(f"Failed: {self.results['summary']['failed']}")
        logger.info(f"Warnings: {self.results['summary']['warnings']}")
        logger.info(f"Skipped: {self.results['summary']['skipped']}")

        if failed_tests:
            logger.error(f"Failed tests: {', '.join(failed_tests)}")

        if warning_tests:
            logger.warning(f"Tests with warnings: {', '.join(warning_tests)}")

async def main() -> None:
    """Run Redis diagnostics."""
    parser = argparse.ArgumentParser(description="Redis diagnostics tool")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--output", "-o", help="Output file for results")
    parser.add_argument("--format", "-f", choices=["json", "text"], default="text", help="Output format")
    args = parser.parse_args()

    diagnostics = RedisDiagnostics(verbose=args.verbose)
    results = await diagnostics.run_diagnostics()

    # Print results
    if args.format == "json":
        print(json.dumps(results, indent=2))

    # Save results if output file specified
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
            logger.info(f"Results saved to {args.output}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
