#!/usr/bin/env python3
"""
Load Testing Script for Maily API

This script provides a comprehensive load testing framework for benchmarking
the Maily platform performance under various load conditions. It simulates
realistic user behavior patterns, allowing for accurate performance testing.

Features:
- Configurable user scenarios (campaigns, emails, analytics)
- Realistic user behavior simulation
- Distributed load testing capability
- Performance metrics collection and reporting
- Dynamic runtime configuration

Usage:
    # Run with default settings
    python load_test.py

    # Run with specific host
    python load_test.py --host=https://api.maily.app

    # Run distributed test
    python load_test.py --master --host=https://api.maily.app
    python load_test.py --worker --master-host=192.168.1.100

    # Run with specific scenario
    python load_test.py --scenarios=campaign_creation,email_sending

    # Run with specific user count and rate
    python load_test.py --users=1000 --spawn-rate=50
"""

import os
import time
import json
import random
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

import gevent
from locust import HttpUser, task, between, tag, events
from locust.env import Environment
from locust.stats import stats_printer, stats_history
from locust.runners import MasterRunner, WorkerRunner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("maily_load_tester")

# Load test configuration
DEFAULT_HOST = "http://localhost:5000"
DEFAULT_USERS = 100
DEFAULT_SPAWN_RATE = 10
DEFAULT_RUN_TIME = 300  # seconds
DEFAULT_SCENARIOS = ["dashboard", "campaign_creation", "email_sending", "analytics"]
DEFAULT_WAIT_TIME_MIN = 1  # seconds
DEFAULT_WAIT_TIME_MAX = 5  # seconds

# Test data
SAMPLE_TEMPLATES = [
    {"name": "Welcome Email", "subject": "Welcome to our service!"},
    {"name": "Newsletter", "subject": "This week's updates"},
    {"name": "Promotion", "subject": "Special offer just for you!"},
    {"name": "Confirmation", "subject": "Your order is confirmed"},
    {"name": "Reminder", "subject": "Don't forget your appointment"},
]

SAMPLE_SEGMENTS = [
    {"name": "New Users", "filter": {"joined_days": {"lt": 30}}},
    {"name": "Active Users", "filter": {"activity": {"gt": 5}}},
    {"name": "Premium Users", "filter": {"subscription": "premium"}},
    {"name": "Inactive Users", "filter": {"last_active_days": {"gt": 90}}},
]

# Test metrics
successful_requests = 0
failed_requests = 0
request_latencies = {}


class MailyUser(HttpUser):
    """Base user class for Maily API load testing"""

    # Wait time between tasks
    wait_time = between(DEFAULT_WAIT_TIME_MIN, DEFAULT_WAIT_TIME_MAX)

    # User authentication token
    token = None
    user_id = None

    def on_start(self):
        """Execute when user starts"""
        self.login()

    def login(self):
        """Authenticate user"""
        credentials = {
            "email": f"loadtest_{random.randint(1, 10000)}@example.com",
            "password": "LoadTest123!"
        }

        with self.client.post("/api/auth/login", json=credentials, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user_id")
                self.client.headers = {
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                }
                response.success()
                logger.debug(f"User login successful: {self.user_id}")
            else:
                # If login fails, try to register
                response.failure(f"Login failed: {response.status_code}")
                self.register()

    def register(self):
        """Register a new user"""
        user_num = random.randint(1, 100000)
        user_data = {
            "email": f"loadtest_{user_num}@example.com",
            "password": "LoadTest123!",
            "name": f"Load Test User {user_num}",
            "company": "LoadTest Inc."
        }

        with self.client.post("/api/auth/register", json=user_data, catch_response=True) as response:
            if response.status_code == 201:
                data = response.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user_id")
                self.client.headers = {
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                }
                response.success()
                logger.debug(f"User registration successful: {self.user_id}")
            else:
                response.failure(f"Registration failed: {response.status_code}")
                # Use default test user if all else fails
                self.use_default_test_user()

    def use_default_test_user(self):
        """Use default test user when login/register fails"""
        # This uses a preconfigured test account - replace with your test account
        default_token = os.environ.get("LOAD_TEST_TOKEN", "test_token")
        self.token = default_token
        self.user_id = os.environ.get("LOAD_TEST_USER_ID", "test_user_id")
        self.client.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        logger.warning(f"Using default test user: {self.user_id}")

    # Dashboard tasks
    @tag("dashboard")
    @task(10)
    def view_dashboard(self):
        """Simulate viewing the dashboard"""
        with self.client.get("/api/dashboard", name="Dashboard - View", catch_response=True) as response:
            handle_response(response)

    @tag("dashboard")
    @task(5)
    def get_recent_campaigns(self):
        """Simulate fetching recent campaigns"""
        with self.client.get("/api/campaigns/recent?limit=5", name="Dashboard - Recent Campaigns", catch_response=True) as response:
            handle_response(response)

    @tag("dashboard")
    @task(5)
    def get_performance_metrics(self):
        """Simulate fetching performance metrics"""
        with self.client.get("/api/analytics/summary", name="Dashboard - Performance Metrics", catch_response=True) as response:
            handle_response(response)

    # Campaign tasks
    @tag("campaign_creation")
    @task(3)
    def create_campaign(self):
        """Simulate creating a new campaign"""
        template_idx = random.randint(0, len(SAMPLE_TEMPLATES) - 1)
        segment_idx = random.randint(0, len(SAMPLE_SEGMENTS) - 1)

        campaign_data = {
            "name": f"Load Test Campaign {random.randint(1000, 9999)}",
            "template_id": random.randint(1, 10),
            "segment_id": random.randint(1, 5),
            "schedule_time": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "subject": SAMPLE_TEMPLATES[template_idx]["subject"],
            "from_name": "Load Tester",
            "from_email": "loadtest@maily.app",
            "content": {
                "type": "html",
                "value": "<h1>Load Test Email</h1><p>This is a test email generated during load testing.</p>"
            },
            "settings": {
                "track_opens": True,
                "track_clicks": True
            }
        }

        with self.client.post("/api/campaigns", json=campaign_data, name="Campaign - Create", catch_response=True) as response:
            if response.status_code == 201:
                campaign_id = response.json().get("id")
                # Store for future use
                self.campaign_id = campaign_id
                response.success()
            else:
                handle_response(response)

    @tag("campaign_creation")
    @task(5)
    def list_campaigns(self):
        """Simulate listing campaigns"""
        with self.client.get("/api/campaigns?page=1&per_page=10", name="Campaign - List", catch_response=True) as response:
            handle_response(response)

    @tag("campaign_creation")
    @task(2)
    def get_campaign_details(self):
        """Simulate getting campaign details"""
        campaign_id = getattr(self, "campaign_id", random.randint(1, 100))
        with self.client.get(f"/api/campaigns/{campaign_id}", name="Campaign - Details", catch_response=True) as response:
            handle_response(response)

    # Email tasks
    @tag("email_sending")
    @task(2)
    def send_test_email(self):
        """Simulate sending a test email"""
        campaign_id = getattr(self, "campaign_id", random.randint(1, 100))
        test_data = {
            "email": f"test-recipient-{random.randint(1, 1000)}@example.com",
            "campaign_id": campaign_id
        }

        with self.client.post("/api/emails/test", json=test_data, name="Email - Send Test", catch_response=True) as response:
            handle_response(response)

    @tag("email_sending")
    @task(1)
    def schedule_campaign(self):
        """Simulate scheduling a campaign for sending"""
        campaign_id = getattr(self, "campaign_id", random.randint(1, 100))
        schedule_data = {
            "send_time": (datetime.utcnow() + timedelta(hours=2)).isoformat()
        }

        with self.client.post(f"/api/campaigns/{campaign_id}/schedule", json=schedule_data, name="Campaign - Schedule", catch_response=True) as response:
            handle_response(response)

    # Analytics tasks
    @tag("analytics")
    @task(4)
    def view_campaign_analytics(self):
        """Simulate viewing campaign analytics"""
        campaign_id = getattr(self, "campaign_id", random.randint(1, 100))
        with self.client.get(f"/api/analytics/campaigns/{campaign_id}", name="Analytics - Campaign", catch_response=True) as response:
            handle_response(response)

    @tag("analytics")
    @task(3)
    def get_open_rates(self):
        """Simulate getting email open rates"""
        with self.client.get("/api/analytics/open-rates?period=30d", name="Analytics - Open Rates", catch_response=True) as response:
            handle_response(response)

    @tag("analytics")
    @task(3)
    def get_click_rates(self):
        """Simulate getting email click rates"""
        with self.client.get("/api/analytics/click-rates?period=30d", name="Analytics - Click Rates", catch_response=True) as response:
            handle_response(response)

    @tag("analytics")
    @task(2)
    def export_analytics_data(self):
        """Simulate exporting analytics data"""
        export_data = {
            "start_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
            "end_date": datetime.utcnow().isoformat(),
            "format": "csv"
        }

        with self.client.post("/api/analytics/export", json=export_data, name="Analytics - Export", catch_response=True) as response:
            handle_response(response)


class ApiPerformanceUser(HttpUser):
    """User class for API performance testing"""

    wait_time = between(0.1, 1)

    def on_start(self):
        """Execute when user starts"""
        self.login()

    def login(self):
        """Authenticate user"""
        credentials = {
            "email": f"apitest_{random.randint(1, 10000)}@example.com",
            "password": "ApiTest123!"
        }

        with self.client.post("/api/auth/login", json=credentials, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.client.headers = {
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                }
            else:
                # Use default test user
                self.use_default_test_user()

    def use_default_test_user(self):
        """Use default test user"""
        default_token = os.environ.get("LOAD_TEST_TOKEN", "test_token")
        self.token = default_token
        self.client.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    @task
    def benchmark_api_endpoints(self):
        """Benchmark various API endpoints"""
        # This is a rapid fire test of multiple endpoints
        endpoints = [
            ("/api/dashboard", "GET", None),
            ("/api/campaigns?page=1&per_page=10", "GET", None),
            ("/api/analytics/summary", "GET", None),
            ("/api/templates", "GET", None),
            ("/api/contacts?page=1&per_page=20", "GET", None),
        ]

        for endpoint, method, data in endpoints:
            if method == "GET":
                with self.client.get(endpoint, name=f"Benchmark - {endpoint}", catch_response=True) as response:
                    handle_response(response)
            elif method == "POST" and data:
                with self.client.post(endpoint, json=data, name=f"Benchmark - {endpoint}", catch_response=True) as response:
                    handle_response(response)


def handle_response(response):
    """Handle and log API response"""
    global successful_requests, failed_requests

    if response.status_code < 400:
        successful_requests += 1
        response.success()
    else:
        failed_requests += 1
        error_msg = f"Request failed: {response.status_code}"
        try:
            error_data = response.json()
            error_msg += f" - {error_data.get('message', '')}"
        except:
            pass
        response.failure(error_msg)

    # Track latency by endpoint
    endpoint = response.request.url.split('?')[0].split('/api/')[-1]
    if endpoint not in request_latencies:
        request_latencies[endpoint] = []
    request_latencies[endpoint].append(response.elapsed.total_seconds())


def run_load_test(host=DEFAULT_HOST,
                 num_users=DEFAULT_USERS,
                 spawn_rate=DEFAULT_SPAWN_RATE,
                 run_time=DEFAULT_RUN_TIME,
                 scenarios=DEFAULT_SCENARIOS):
    """
    Run load test with specified parameters

    Args:
        host: Target host URL
        num_users: Number of users to simulate
        spawn_rate: User spawn rate (users per second)
        run_time: Test duration in seconds
        scenarios: List of scenarios to run
    """
    # Configure environment
    env = Environment(user_classes=[MailyUser, ApiPerformanceUser])
    env.create_local_runner()

    # Configure user weighting
    if "dashboard" in scenarios:
        env.weighted_users = {MailyUser: 100}
    if "api_performance" in scenarios:
        if len(scenarios) == 1:
            env.weighted_users = {ApiPerformanceUser: 100}
        else:
            env.weighted_users = {MailyUser: 70, ApiPerformanceUser: 30}

    # Configure host
    env.host = host

    # Configure available tags
    available_tags = []
    for scenario in scenarios:
        if scenario in DEFAULT_SCENARIOS:
            available_tags.append(scenario)

    if available_tags:
        env.runner.tag_list = available_tags

    # Start runner
    env.runner.start(num_users, spawn_rate=spawn_rate)

    # Start stats printer and history
    gevent.spawn(stats_printer(env.stats))
    gevent.spawn(stats_history, env.runner)

    # Run for specified time
    gevent.spawn_later(run_time, lambda: env.runner.quit())

    # Wait for completion
    env.runner.greenlet.join()

    # Generate report
    generate_report(env.stats)


def generate_report(stats):
    """Generate and print load test report"""
    print("\n=== Load Test Report ===\n")

    # Summary statistics
    print(f"Total Requests: {successful_requests + failed_requests}")
    print(f"Successful Requests: {successful_requests}")
    print(f"Failed Requests: {failed_requests}")
    success_rate = (successful_requests / (successful_requests + failed_requests)) * 100 if (successful_requests + failed_requests) > 0 else 0
    print(f"Success Rate: {success_rate:.2f}%")

    # Endpoint performance
    print("\nEndpoint Performance:")
    for endpoint, latencies in request_latencies.items():
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) >= 20 else max_latency
            print(f"  {endpoint}:")
            print(f"    Requests: {len(latencies)}")
            print(f"    Avg Latency: {avg_latency*1000:.2f}ms")
            print(f"    Min Latency: {min_latency*1000:.2f}ms")
            print(f"    Max Latency: {max_latency*1000:.2f}ms")
            print(f"    P95 Latency: {p95_latency*1000:.2f}ms")

    # Write to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"load_test_report_{timestamp}.json"

    report_data = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_requests": successful_requests + failed_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": success_rate
        },
        "endpoints": {}
    }

    for endpoint, latencies in request_latencies.items():
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) >= 20 else max_latency

            report_data["endpoints"][endpoint] = {
                "requests": len(latencies),
                "avg_latency_ms": avg_latency * 1000,
                "min_latency_ms": min_latency * 1000,
                "max_latency_ms": max_latency * 1000,
                "p95_latency_ms": p95_latency * 1000
            }

    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)

    print(f"\nDetailed report saved to {report_file}")


def main():
    """Main entry point for load testing script"""
    parser = argparse.ArgumentParser(description="Maily API Load Testing Tool")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Target host URL (default: {DEFAULT_HOST})")
    parser.add_argument("--users", type=int, default=DEFAULT_USERS, help=f"Number of users to simulate (default: {DEFAULT_USERS})")
    parser.add_argument("--spawn-rate", type=int, default=DEFAULT_SPAWN_RATE, help=f"User spawn rate per second (default: {DEFAULT_SPAWN_RATE})")
    parser.add_argument("--run-time", type=int, default=DEFAULT_RUN_TIME, help=f"Test duration in seconds (default: {DEFAULT_RUN_TIME})")
    parser.add_argument("--scenarios", default=",".join(DEFAULT_SCENARIOS), help=f"Comma-separated list of scenarios to run (default: {','.join(DEFAULT_SCENARIOS)})")
    parser.add_argument("--master", action="store_true", help="Run as master in distributed mode")
    parser.add_argument("--worker", action="store_true", help="Run as worker in distributed mode")
    parser.add_argument("--master-host", default="127.0.0.1", help="Master host in distributed mode")
    parser.add_argument("--master-port", type=int, default=5557, help="Master port in distributed mode")

    args = parser.parse_args()

    # Parse scenarios
    scenarios = args.scenarios.split(",")

    # Run in standalone mode
    if not args.master and not args.worker:
        print(f"Starting load test with {args.users} users at {args.host}")
        print(f"Scenarios: {', '.join(scenarios)}")
        run_load_test(
            host=args.host,
            num_users=args.users,
            spawn_rate=args.spawn_rate,
            run_time=args.run_time,
            scenarios=scenarios
        )
    # Run in distributed mode
    else:
        from locust.main import main as locust_main

        locust_args = [
            "--host", args.host,
            "--users", str(args.users),
            "--spawn-rate", str(args.spawn_rate),
            "--run-time", f"{args.run_time}s",
            "--headless"
        ]

        if args.master:
            locust_args.extend(["--master"])
            print(f"Starting master node at {args.host}")

        if args.worker:
            locust_args.extend(["--worker", "--master-host", args.master_host, "--master-port", str(args.master_port)])
            print(f"Starting worker node connecting to {args.master_host}:{args.master_port}")

        # Add tag filtering based on scenarios
        if scenarios and scenarios != DEFAULT_SCENARIOS:
            scenario_tags = ",".join(scenarios)
            locust_args.extend(["--tags", scenario_tags])

        # Hand over to Locust's main function
        import sys
        sys.argv = ["locust", "-f", __file__] + locust_args
        locust_main()


if __name__ == "__main__":
    main()
