#!/usr/bin/env python3
"""
Stress Testing Script for Maily API

This script is designed to test the Maily platform under extreme conditions,
pushing the system to its limits to identify breaking points, bottlenecks,
and performance degradation patterns. Unlike the load test which simulates
realistic user behavior, this stress test deliberately creates worst-case
scenarios and edge cases.

Features:
- Extreme concurrency testing
- Resource exhaustion simulation
- Spike testing with sudden traffic surges
- Long-running connection tests
- Large payload testing
- Error injection and recovery testing
- Database connection saturation
- Cache invalidation stress testing
- Rate limiting verification

Usage:
    # Run basic stress test
    python stress_test.py

    # Run specific stress test type
    python stress_test.py --test-type=spike

    # Run with specific intensity level (1-10)
    python stress_test.py --intensity=8

    # Target specific component
    python stress_test.py --component=database
"""

import os
import sys
import time
import json
import random
import logging
import argparse
import threading
import multiprocessing
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

import requests
import psutil
import numpy as np
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("stress_test.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("maily_stress_tester")

# Stress test configuration
DEFAULT_HOST = "http://localhost:5000"
DEFAULT_INTENSITY = 5  # Scale 1-10
DEFAULT_DURATION = 300  # seconds
DEFAULT_TEST_TYPE = "all"  # all, concurrency, spike, payload, etc.
DEFAULT_COMPONENT = "all"  # all, api, database, cache, etc.
DEFAULT_THREADS = multiprocessing.cpu_count() * 2
DEFAULT_PROCESSES = multiprocessing.cpu_count()

# Test data
LARGE_PAYLOADS = {
    "small": "".join(["x" for _ in range(10 * 1024)]),  # 10KB
    "medium": "".join(["x" for _ in range(100 * 1024)]),  # 100KB
    "large": "".join(["x" for _ in range(1024 * 1024)]),  # 1MB
    "xlarge": "".join(["x" for _ in range(10 * 1024 * 1024)])  # 10MB
}

# Generate a large number of test users
TEST_USERS = [
    {
        "email": f"stress_test_{i}@example.com",
        "password": f"StressTest{i}!",
        "name": f"Stress Test User {i}",
        "company": "Stress Test Inc."
    } for i in range(1, 1001)
]

# Generate large campaign data
LARGE_CAMPAIGN = {
    "name": "Stress Test Campaign",
    "subject": "Stress Test Subject Line",
    "from_name": "Stress Tester",
    "from_email": "stress@justmaily.com",
    "content": {
        "type": "html",
        "value": "<h1>Stress Test Email</h1>" + "<p>This is a stress test paragraph.</p>" * 1000
    },
    "settings": {
        "track_opens": True,
        "track_clicks": True,
        "custom_tracking": {
            "utm_source": "stress_test",
            "utm_medium": "email",
            "utm_campaign": "stress_test_campaign"
        },
        "advanced": {
            "throttling": {
                "enabled": False,
                "rate": 0
            },
            "scheduling": {
                "timezone": "UTC",
                "optimal_time": False
            }
        }
    },
    "recipients": {
        "segment_id": None,
        "list_ids": [],
        "filter": {
            "conditions": [
                {"field": "email", "operator": "contains", "value": "@example.com"}
            ] * 20,
            "operator": "AND"
        }
    },
    "metadata": {
        "stress_test": True,
        "test_id": "stress-test-1",
        "tags": ["stress", "test", "performance"] + [f"tag_{i}" for i in range(100)]
    }
}

# Test metrics
class StressTestMetrics:
    """Class to track and report stress test metrics"""

    def __init__(self):
        self.start_time = time.time()
        self.end_time = None
        self.requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times = []
        self.errors = {}
        self.status_codes = {}
        self.cpu_usage = []
        self.memory_usage = []
        self.thread_count = []
        self.connection_count = []
        self.lock = threading.Lock()

    def record_request(self, success: bool, response_time: float, status_code: int, error: Optional[str] = None):
        """Record metrics for a single request"""
        with self.lock:
            self.requests += 1
            if success:
                self.successful_requests += 1
            else:
                self.failed_requests += 1

            self.response_times.append(response_time)

            if status_code not in self.status_codes:
                self.status_codes[status_code] = 0
            self.status_codes[status_code] += 1

            if error:
                if error not in self.errors:
                    self.errors[error] = 0
                self.errors[error] += 1

    def record_system_metrics(self):
        """Record system metrics"""
        self.cpu_usage.append(psutil.cpu_percent(interval=0.1))
        self.memory_usage.append(psutil.virtual_memory().percent)
        self.thread_count.append(threading.active_count())

        # Count network connections to the target
        connections = 0
        for conn in psutil.net_connections():
            if conn.status == 'ESTABLISHED' and DEFAULT_HOST.split(':')[1].strip('/') in str(conn.raddr):
                connections += 1
        self.connection_count.append(connections)

    def finalize(self):
        """Finalize metrics collection"""
        self.end_time = time.time()

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics"""
        if not self.end_time:
            self.finalize()

        duration = self.end_time - self.start_time

        # Calculate response time percentiles
        if self.response_times:
            response_times = np.array(self.response_times)
            percentiles = {
                "min": float(np.min(response_times)),
                "max": float(np.max(response_times)),
                "mean": float(np.mean(response_times)),
                "median": float(np.median(response_times)),
                "p90": float(np.percentile(response_times, 90)),
                "p95": float(np.percentile(response_times, 95)),
                "p99": float(np.percentile(response_times, 99))
            }
        else:
            percentiles = {
                "min": 0, "max": 0, "mean": 0, "median": 0,
                "p90": 0, "p95": 0, "p99": 0
            }

        # Calculate system metrics
        if self.cpu_usage:
            cpu_stats = {
                "min": min(self.cpu_usage),
                "max": max(self.cpu_usage),
                "avg": sum(self.cpu_usage) / len(self.cpu_usage)
            }
        else:
            cpu_stats = {"min": 0, "max": 0, "avg": 0}

        if self.memory_usage:
            memory_stats = {
                "min": min(self.memory_usage),
                "max": max(self.memory_usage),
                "avg": sum(self.memory_usage) / len(self.memory_usage)
            }
        else:
            memory_stats = {"min": 0, "max": 0, "avg": 0}

        # Calculate requests per second
        rps = self.requests / duration if duration > 0 else 0

        return {
            "duration": duration,
            "total_requests": self.requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": (self.successful_requests / self.requests * 100) if self.requests > 0 else 0,
            "requests_per_second": rps,
            "response_times": percentiles,
            "status_codes": self.status_codes,
            "errors": self.errors,
            "system": {
                "cpu": cpu_stats,
                "memory": memory_stats,
                "max_threads": max(self.thread_count) if self.thread_count else 0,
                "max_connections": max(self.connection_count) if self.connection_count else 0
            }
        }

    def print_report(self):
        """Print stress test report to console"""
        summary = self.get_summary()

        print("\n" + "=" * 50)
        print("MAILY STRESS TEST REPORT")
        print("=" * 50)

        print(f"\nTest Duration: {summary['duration']:.2f} seconds")
        print(f"Total Requests: {summary['total_requests']}")
        print(f"Successful Requests: {summary['successful_requests']}")
        print(f"Failed Requests: {summary['failed_requests']}")
        print(f"Success Rate: {summary['success_rate']:.2f}%")
        print(f"Requests Per Second: {summary['requests_per_second']:.2f}")

        print("\nResponse Times (seconds):")
        print(f"  Min: {summary['response_times']['min']:.4f}")
        print(f"  Max: {summary['response_times']['max']:.4f}")
        print(f"  Mean: {summary['response_times']['mean']:.4f}")
        print(f"  Median: {summary['response_times']['median']:.4f}")
        print(f"  90th Percentile: {summary['response_times']['p90']:.4f}")
        print(f"  95th Percentile: {summary['response_times']['p95']:.4f}")
        print(f"  99th Percentile: {summary['response_times']['p99']:.4f}")

        print("\nStatus Code Distribution:")
        for code, count in summary['status_codes'].items():
            print(f"  {code}: {count} ({count/summary['total_requests']*100:.2f}%)")

        if summary['errors']:
            print("\nTop Errors:")
            sorted_errors = sorted(summary['errors'].items(), key=lambda x: x[1], reverse=True)
            for error, count in sorted_errors[:5]:
                print(f"  {error}: {count}")

        print("\nSystem Metrics:")
        print(f"  CPU Usage: {summary['system']['cpu']['avg']:.2f}% (Max: {summary['system']['cpu']['max']:.2f}%)")
        print(f"  Memory Usage: {summary['system']['memory']['avg']:.2f}% (Max: {summary['system']['memory']['max']:.2f}%)")
        print(f"  Max Threads: {summary['system']['max_threads']}")
        print(f"  Max Connections: {summary['system']['max_connections']}")

        print("\nConclusion:")
        if summary['success_rate'] > 99:
            print("  The system handled the stress test exceptionally well.")
        elif summary['success_rate'] > 95:
            print("  The system handled the stress test well with minor issues.")
        elif summary['success_rate'] > 90:
            print("  The system showed moderate stress under load.")
        elif summary['success_rate'] > 80:
            print("  The system showed significant stress under load.")
        else:
            print("  The system failed to handle the stress test adequately.")

        print("=" * 50)

    def save_report(self, filename: str = None):
        """Save stress test report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stress_test_report_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(self.get_summary(), f, indent=2)

        logger.info(f"Stress test report saved to {filename}")
        return filename


# Global metrics instance
metrics = StressTestMetrics()


def authenticate(session: requests.Session, host: str) -> Tuple[bool, Optional[str]]:
    """Authenticate and get access token"""
    user = random.choice(TEST_USERS)

    try:
        # Try to login
        response = session.post(
            f"{host}/api/auth/login",
            json={
                "email": user["email"],
                "password": user["password"]
            },
            timeout=10
        )

        if response.status_code == 200:
            token = response.json().get("access_token")
            if token:
                session.headers.update({"Authorization": f"Bearer {token}"})
                return True, None

        # If login fails, try to register
        response = session.post(
            f"{host}/api/auth/register",
            json=user,
            timeout=10
        )

        if response.status_code == 201:
            token = response.json().get("access_token")
            if token:
                session.headers.update({"Authorization": f"Bearer {token}"})
                return True, None

        return False, f"Authentication failed: {response.status_code}"

    except Exception as e:
        return False, f"Authentication error: {str(e)}"


# Stress test implementations
def run_request(session: requests.Session, method: str, url: str, data: Dict = None,
                expected_status: List[int] = None) -> Tuple[bool, float, int, Optional[str]]:
    """Run a single request and record metrics"""
    if expected_status is None:
        expected_status = [200, 201, 202, 204]

    start_time = time.time()
    error = None
    status_code = 0

    try:
        if method.upper() == "GET":
            response = session.get(url, timeout=30)
        elif method.upper() == "POST":
            response = session.post(url, json=data, timeout=30)
        elif method.upper() == "PUT":
            response = session.put(url, json=data, timeout=30)
        elif method.upper() == "DELETE":
            response = session.delete(url, timeout=30)
        else:
            return False, 0, 0, f"Unsupported method: {method}"

        status_code = response.status_code
        success = status_code in expected_status

        if not success:
            try:
                error_data = response.json()
                error = f"API Error: {error_data.get('message', 'Unknown error')}"
            except:
                error = f"API Error: Status {status_code}"

        return success, time.time() - start_time, status_code, error

    except requests.exceptions.Timeout:
        return False, time.time() - start_time, 408, "Request timeout"
    except requests.exceptions.ConnectionError:
        return False, time.time() - start_time, 503, "Connection error"
    except Exception as e:
        return False, time.time() - start_time, 500, str(e)


def concurrent_stress_test(host: str, intensity: int, duration: int):
    """
    Run concurrent stress test with many simultaneous connections

    Args:
        host: Target host URL
        intensity: Intensity level (1-10)
        duration: Test duration in seconds
    """
    logger.info(f"Starting concurrent stress test (intensity: {intensity}, duration: {duration}s)")

    # Calculate concurrency based on intensity
    concurrency = intensity * 50  # 50-500 concurrent requests

    # Endpoints to test
    endpoints = [
        ("GET", f"{host}/api/dashboard"),
        ("GET", f"{host}/api/campaigns"),
        ("GET", f"{host}/api/templates"),
        ("GET", f"{host}/api/analytics/summary"),
        ("POST", f"{host}/api/campaigns", LARGE_CAMPAIGN)
    ]

    # Create session pool
    session_pool = []
    for _ in range(min(concurrency, 100)):  # Max 100 sessions
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        success, error = authenticate(session, host)
        if success:
            session_pool.append(session)

    if not session_pool:
        logger.error("Failed to create any authenticated sessions")
        return

    logger.info(f"Created {len(session_pool)} authenticated sessions")

    # Start metrics collection thread
    stop_metrics = threading.Event()

    def collect_metrics():
        while not stop_metrics.is_set():
            metrics.record_system_metrics()
            time.sleep(1)

    metrics_thread = threading.Thread(target=collect_metrics)
    metrics_thread.daemon = True
    metrics_thread.start()

    # Run stress test
    start_time = time.time()
    end_time = start_time + duration

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []

        while time.time() < end_time:
            # Submit new tasks up to concurrency limit
            while len(futures) < concurrency and time.time() < end_time:
                # Select random endpoint
                method, url, *data_args = random.choice(endpoints)
                data = data_args[0] if data_args else None

                # Select random session
                session = random.choice(session_pool)

                # Submit task
                future = executor.submit(run_request, session, method, url, data)
                futures.append(future)

            # Process completed futures
            done, futures = concurrent.futures.wait(
                futures,
                timeout=0.1,
                return_when=concurrent.futures.FIRST_COMPLETED
            )

            for future in done:
                success, response_time, status_code, error = future.result()
                metrics.record_request(success, response_time, status_code, error)

    # Stop metrics collection
    stop_metrics.set()
    metrics_thread.join()

    logger.info("Concurrent stress test completed")


def spike_stress_test(host: str, intensity: int, duration: int):
    """
    Run spike stress test with sudden traffic surges

    Args:
        host: Target host URL
        intensity: Intensity level (1-10)
        duration: Test duration in seconds
    """
    logger.info(f"Starting spike stress test (intensity: {intensity}, duration: {duration}s)")

    # Calculate base and spike concurrency based on intensity
    base_concurrency = 10
    spike_concurrency = intensity * 100  # 100-1000 concurrent requests during spike

    # Endpoints to test
    endpoints = [
        ("GET", f"{host}/api/dashboard"),
        ("GET", f"{host}/api/campaigns"),
        ("GET", f"{host}/api/templates"),
        ("GET", f"{host}/api/analytics/summary"),
        ("POST", f"{host}/api/campaigns", LARGE_CAMPAIGN)
    ]

    # Create session pool
    session_pool = []
    for _ in range(min(spike_concurrency, 200)):  # Max 200 sessions
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        success, error = authenticate(session, host)
        if success:
            session_pool.append(session)

    if not session_pool:
        logger.error("Failed to create any authenticated sessions")
        return

    logger.info(f"Created {len(session_pool)} authenticated sessions")

    # Start metrics collection thread
    stop_metrics = threading.Event()

    def collect_metrics():
        while not stop_metrics.is_set():
            metrics.record_system_metrics()
            time.sleep(1)

    metrics_thread = threading.Thread(target=collect_metrics)
    metrics_thread.daemon = True
    metrics_thread.start()

    # Run stress test with spikes
    start_time = time.time()
    end_time = start_time + duration

    # Calculate spike parameters
    num_spikes = max(1, duration // 60)  # At least one spike, or one per minute
    spike_duration = 10  # seconds

    spike_times = []
    for i in range(num_spikes):
        # Distribute spikes evenly, but not at the very beginning or end
        spike_start = start_time + (duration / (num_spikes + 1)) * (i + 1)
        spike_times.append((spike_start, spike_start + spike_duration))

    logger.info(f"Planned {num_spikes} traffic spikes during the test")

    with ThreadPoolExecutor(max_workers=spike_concurrency) as executor:
        futures = []

        while time.time() < end_time:
            current_time = time.time()

            # Check if we're in a spike period
            in_spike = any(start <= current_time <= end for start, end in spike_times)
            current_concurrency = spike_concurrency if in_spike else base_concurrency

            if in_spike and len(futures) < base_concurrency:
                logger.info(f"Traffic spike started at {datetime.now().strftime('%H:%M:%S')}")

            # Submit new tasks up to concurrency limit
            while len(futures) < current_concurrency and time.time() < end_time:
                # Select random endpoint
                method, url, *data_args = random.choice(endpoints)
                data = data_args[0] if data_args else None

                # Select random session
                session = random.choice(session_pool)

                # Submit task
                future = executor.submit(run_request, session, method, url, data)
                futures.append(future)

            # Process completed futures
            done, futures = concurrent.futures.wait(
                futures,
                timeout=0.1,
                return_when=concurrent.futures.FIRST_COMPLETED
            )

            for future in done:
                success, response_time, status_code, error = future.result()
                metrics.record_request(success, response_time, status_code, error)

    # Stop metrics collection
    stop_metrics.set()
    metrics_thread.join()

    logger.info("Spike stress test completed")


def payload_stress_test(host: str, intensity: int, duration: int):
    """
    Run payload stress test with large request/response payloads

    Args:
        host: Target host URL
        intensity: Intensity level (1-10)
        duration: Test duration in seconds
    """
    logger.info(f"Starting payload stress test (intensity: {intensity}, duration: {duration}s)")

    # Calculate concurrency based on intensity
    concurrency = max(5, intensity * 10)  # 10-100 concurrent requests

    # Create large campaign with size based on intensity
    campaign_size_multiplier = intensity * 10
    large_campaign = LARGE_CAMPAIGN.copy()
    large_campaign["content"]["value"] = "<h1>Stress Test Email</h1>" + "<p>This is a stress test paragraph.</p>" * (1000 * campaign_size_multiplier)

    # Add large metadata based on intensity
    large_campaign["metadata"]["large_data"] = {}
    for i in range(intensity * 100):
        large_campaign["metadata"]["large_data"][f"field_{i}"] = f"value_{i}" * 10

    # Create session pool
    session_pool = []
    for _ in range(min(concurrency, 20)):  # Max 20 sessions for large payloads
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        success, error = authenticate(session, host)
        if success:
            session_pool.append(session)

    if not session_pool:
        logger.error("Failed to create any authenticated sessions")
        return

    logger.info(f"Created {len(session_pool)} authenticated sessions")

    # Start metrics collection thread
    stop_metrics = threading.Event()

    def collect_metrics():
        while not stop_metrics.is_set():
            metrics.record_system_metrics()
            time.sleep(1)

    metrics_thread = threading.Thread(target=collect_metrics)
    metrics_thread.daemon = True
    metrics_thread.start()

    # Run stress test
    start_time = time.time()
    end_time = start_time + duration

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []

        while time.time() < end_time:
            # Submit new tasks up to concurrency limit
            while len(futures) < concurrency and time.time() < end_time:
                # Select random session
                session = random.choice(session_pool)

                # Submit task to create campaign with large payload
                future = executor.submit(
                    run_request,
                    session,
                    "POST",
                    f"{host}/api/campaigns",
                    large_campaign
                )
                futures.append(future)

            # Process completed futures
            done, futures = concurrent.futures.wait(
                futures,
                timeout=0.1,
                return_when=concurrent.futures.FIRST_COMPLETED
            )

            for future in done:
                success, response_time, status_code, error = future.result()
                metrics.record_request(success, response_time, status_code, error)

    # Stop metrics collection
    stop_metrics.set()
    metrics_thread.join()

    logger.info("Payload stress test completed")


def database_stress_test(host: str, intensity: int, duration: int):
    """
    Run database stress test focusing on database operations

    Args:
        host: Target host URL
        intensity: Intensity level (1-10)
        duration: Test duration in seconds
    """
    logger.info(f"Starting database stress test (intensity: {intensity}, duration: {duration}s)")

    # Calculate concurrency based on intensity
    concurrency = intensity * 20  # 20-200 concurrent requests

    # Endpoints that are database-intensive
    endpoints = [
        # Complex queries
        ("GET", f"{host}/api/campaigns?page=1&per_page=50&sort=created_at&order=desc"),
        ("GET", f"{host}/api/analytics/campaigns?start_date={datetime.now() - timedelta(days=30)}&end_date={datetime.now()}"),
        ("GET", f"{host}/api/contacts?page=1&per_page=100&sort=email&order=asc"),

        # Write operations
        ("POST", f"{host}/api/campaigns", LARGE_CAMPAIGN),
        ("POST", f"{host}/api/templates", {
            "name": f"Stress Test Template {random.randint(1000, 9999)}",
            "content": "<h1>Stress Test Template</h1>" + "<p>This is a stress test paragraph.</p>" * 100
        }),

        # Complex filtering
        ("GET", f"{host}/api/contacts?filter=" + json.dumps({
            "conditions": [
                {"field": "email", "operator": "contains", "value": "@example.com"},
                {"field": "created_at", "operator": "gt", "value": (datetime.now() - timedelta(days=30)).isoformat()}
            ],
            "operator": "AND"
        }))
    ]

    # Create session pool
    session_pool = []
    for _ in range(min(concurrency, 50)):  # Max 50 sessions
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        success, error = authenticate(session, host)
        if success:
            session_pool.append(session)

    if not session_pool:
        logger.error("Failed to create any authenticated sessions")
        return

    logger.info(f"Created {len(session_pool)} authenticated sessions")

    # Start metrics collection thread
    stop_metrics = threading.Event()

    def collect_metrics():
        while not stop_metrics.is_set():
            metrics.record_system_metrics()
            time.sleep(1)

    metrics_thread = threading.Thread(target=collect_metrics)
    metrics_thread.daemon = True
    metrics_thread.start()

    # Run stress test
    start_time = time.time()
    end_time = start_time + duration

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []

        while time.time() < end_time:
            # Submit new tasks up to concurrency limit
            while len(futures) < concurrency and time.time() < end_time:
                # Select random endpoint
                method, url, *data_args = random.choice(endpoints)
                data = data_args[0] if data_args else None

                # Select random session
                session = random.choice(session_pool)

                # Submit task
                future = executor.submit(run_request, session, method, url, data)
                futures.append(future)

            # Process completed futures
            done, futures = concurrent.futures.wait(
                futures,
                timeout=0.1,
                return_when=concurrent.futures.FIRST_COMPLETED
            )

            for future in done:
                success, response_time, status_code, error = future.result()
                metrics.record_request(success, response_time, status_code, error)

    # Stop metrics collection
    stop_metrics.set()
    metrics_thread.join()

    logger.info("Database stress test completed")


def cache_stress_test(host: str, intensity: int, duration: int):
    """
    Run cache stress test focusing on cache invalidation

    Args:
        host: Target host URL
        intensity: Intensity level (1-10)
        duration: Test duration in seconds
    """
    logger.info(f"Starting cache stress test (intensity: {intensity}, duration: {duration}s)")

    # Calculate concurrency based on intensity
    concurrency = intensity * 30  # 30-300 concurrent requests

    # Create session pool
    session_pool = []
    for _ in range(min(concurrency, 50)):  # Max 50 sessions
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        success, error = authenticate(session, host)
        if success:
            session_pool.append(session)

    if not session_pool:
        logger.error("Failed to create any authenticated sessions")
        return

    logger.info(f"Created {len(session_pool)} authenticated sessions")

    # Start metrics collection thread
    stop_metrics = threading.Event()

    def collect_metrics():
        while not stop_metrics.is_set():
            metrics.record_system_metrics()
            time.sleep(1)

    metrics_thread = threading.Thread(target=collect_metrics)
    metrics_thread.daemon = True
    metrics_thread.start()

    # Create a campaign to use for testing
    campaign_id = None
    for session in session_pool:
        success, response_time, status_code, error = run_request(
            session, "POST", f"{host}/api/campaigns", LARGE_CAMPAIGN
        )
        if success:
            try:
                response = session.get(f"{host}/api/campaigns")
                campaigns = response.json()
                if campaigns and len(campaigns) > 0:
                    campaign_id = campaigns[0].get("id")
                    break
            except:
                pass

    if not campaign_id:
        logger.warning("Could not create or find a campaign for cache testing")
    else:
        logger.info(f"Using campaign ID {campaign_id} for cache testing")

    # Endpoints that are cache-intensive
    endpoints = [
        # Cacheable endpoints
        ("GET", f"{host}/api/dashboard"),
        ("GET", f"{host}/api/analytics/summary"),
    ]

    if campaign_id:
        endpoints.extend([
            ("GET", f"{host}/api/campaigns/{campaign_id}"),
            ("GET", f"{host}/api/analytics/campaigns/{campaign_id}")
        ])

    # Cache invalidation endpoints
    invalidation_endpoints = [
        ("POST", f"{host}/api/campaigns", LARGE_CAMPAIGN),
        ("POST", f"{host}/api/templates", {
            "name": f"Cache Test Template {random.randint(1000, 9999)}",
            "content": "<h1>Cache Test Template</h1><p>This is a test.</p>"
        })
    ]

    if campaign_id:
        invalidation_endpoints.append((
            "PUT",
            f"{host}/api/campaigns/{campaign_id}",
            {"name": f"Updated Campaign {random.randint(1000, 9999)}"}
        ))

    # Run stress test
    start_time = time.time()
    end_time = start_time + duration

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []

        while time.time() < end_time:
            current_time = time.time()

            # Every 5 seconds, trigger cache invalidation
            should_invalidate = int(current_time - start_time) % 5 == 0

            # Submit new tasks up to concurrency limit
            while len(futures) < concurrency and time.time() < end_time:
                # Select random session
                session = random.choice(session_pool)

                # Select endpoint based on whether we should invalidate cache
                if should_invalidate and random.random() < 0.2:  # 20% chance during invalidation periods
                    method, url, *data_args = random.choice(invalidation_endpoints)
                else:
                    method, url, *data_args = random.choice(endpoints)

                data = data_args[0] if data_args else None

                # Submit task
                future = executor.submit(run_request, session, method, url, data)
                futures.append(future)

            # Process completed futures
            done, futures = concurrent.futures.wait(
                futures,
                timeout=0.1,
                return_when=concurrent.futures.FIRST_COMPLETED
            )

            for future in done:
                success, response_time, status_code, error = future.result()
                metrics.record_request(success, response_time, status_code, error)

    # Stop metrics collection
    stop_metrics.set()
    metrics_thread.join()

    logger.info("Cache stress test completed")


def run_stress_test(host: str, test_type: str, intensity: int, duration: int, component: str):
    """
    Run stress test with specified parameters

    Args:
        host: Target host URL
        test_type: Type of stress test to run
        intensity: Intensity level (1-10)
        duration: Test duration in seconds
        component: Component to target
    """
    # Validate intensity
    if intensity < 1 or intensity > 10:
        logger.warning(f"Invalid intensity level: {intensity}. Using default: {DEFAULT_INTENSITY}")
        intensity = DEFAULT_INTENSITY

    # Log test parameters
    logger.info(f"Starting stress test with parameters:")
    logger.info(f"  Host: {host}")
    logger.info(f"  Test Type: {test_type}")
    logger.info(f"  Intensity: {intensity}")
    logger.info(f"  Duration: {duration} seconds")
    logger.info(f"  Component: {component}")

    # Run appropriate test based on type and component
    if test_type == "all" or test_type == "concurrency":
        concurrent_stress_test(host, intensity, duration)

    if test_type == "all" or test_type == "spike":
        spike_stress_test(host, intensity, duration)

    if test_type == "all" or test_type == "payload":
        payload_stress_test(host, intensity, duration)

    if (test_type == "all" or test_type == "component") and (component == "all" or component == "database"):
        database_stress_test(host, intensity, duration)

    if (test_type == "all" or test_type == "component") and (component == "all" or component == "cache"):
        cache_stress_test(host, intensity, duration)

    # Generate and print report
    metrics.print_report()
    report_file = metrics.save_report()

    logger.info(f"Stress test completed. Report saved to {report_file}")
    return report_file


def main():
    """Main entry point for stress testing script"""
    parser = argparse.ArgumentParser(description="Maily API Stress Testing Tool")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Target host URL (default: {DEFAULT_HOST})")
    parser.add_argument("--intensity", type=int, default=DEFAULT_INTENSITY, help=f"Intensity level 1-10 (default: {DEFAULT_INTENSITY})")
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION, help=f"Test duration in seconds (default: {DEFAULT_DURATION})")
    parser.add_argument("--test-type", default=DEFAULT_TEST_TYPE, choices=["all", "concurrency", "spike", "payload", "component"], help=f"Type of stress test to run (default: {DEFAULT_TEST_TYPE})")
    parser.add_argument("--component", default=DEFAULT_COMPONENT, choices=["all", "api", "database", "cache"], help=f"Component to target (default: {DEFAULT_COMPONENT})")
    parser.add_argument("--threads", type=int, default=DEFAULT_THREADS, help=f"Number of threads to use (default: {DEFAULT_THREADS})")
    parser.add_argument("--processes", type=int, default=DEFAULT_PROCESSES, help=f"Number of processes to use (default: {DEFAULT_PROCESSES})")
    parser.add_argument("--report-file", help="Custom filename for the report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Set thread and process count
    ThreadPoolExecutor._max_workers = args.threads
    ProcessPoolExecutor._max_workers = args.processes

    try:
        # Run stress test
        report_file = run_stress_test(
            host=args.host,
            test_type=args.test_type,
            intensity=args.intensity,
            duration=args.duration,
            component=args.component
        )

        # Save report with custom filename if provided
        if args.report_file and report_file:
            import shutil
            shutil.copy(report_file, args.report_file)
            logger.info(f"Report also saved to {args.report_file}")

        print(f"\nStress test completed successfully. See {report_file} for detailed results.")

    except KeyboardInterrupt:
        print("\nStress test interrupted by user.")
        # Still generate report for partial test
        metrics.print_report()
        report_file = metrics.save_report()
        print(f"Partial results saved to {report_file}")

    except Exception as e:
        logger.error(f"Stress test failed: {str(e)}", exc_info=True)
        print(f"\nStress test failed: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
