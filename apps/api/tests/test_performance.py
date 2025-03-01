"""Performance tests for the email generation system."""

import statistics
import time
from typing import Any, Dict, List

import pytest
from locust import HttpUser, between, task

from backend.ai.adapters import ModelFactory
from backend.ai.agents import EmailAgent


class TestPerformance:
    """Performance test suite."""

    @pytest.mark.performance
    def test_response_time(self, mock_env, mock_monitoring):
        """Test response time for email generation."""
        models = ["r1-1776", "gpt-4", "gemini-pro", "claude-3-opus"]
        iterations = 5
        max_response_time = 1.0  # 1 second maximum

        context = {
            "purpose": "Product launch",
            "audience": "Enterprise customers",
            "message": "New AI features",
            "tone": "Professional",
        }

        results = {}
        for model_name in models:
            agent = EmailAgent(model_name=model_name)
            response_times = []

            for _ in range(iterations):
                start_time = time.time()
                subject = agent.generate_subject(context)
                end_time = time.time()

                response_time = end_time - start_time
                response_times.append(response_time)

            results[model_name] = {
                "mean": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "max": max(response_times),
                "min": min(response_times),
            }

            # Assert performance requirements
            assert results[model_name]["mean"] < max_response_time

    @pytest.mark.performance
    def test_concurrent_load(self, mock_env, mock_monitoring):
        """Test system under concurrent load."""
        import concurrent.futures

        num_requests = 100
        max_workers = 10
        timeout = 30  # 30 seconds timeout

        def make_request() -> Dict[str, Any]:
            agent = EmailAgent(model_name="gpt-4")  # Use any model
            context = {
                "purpose": "Product launch",
                "audience": "Enterprise customers",
                "message": "New AI features",
                "tone": "Professional",
            }

            start_time = time.time()
            subject = agent.generate_subject(context)
            end_time = time.time()

            return {
                "success": subject is not None,
                "response_time": end_time - start_time,
            }

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            results = []

            for future in concurrent.futures.as_completed(futures, timeout=timeout):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({"success": False, "error": str(e)})

        # Analyze results
        success_rate = sum(1 for r in results if r["success"]) / len(results)
        response_times = [r["response_time"] for r in results if "response_time" in r]

        assert success_rate >= 0.95  # 95% success rate
        assert statistics.mean(response_times) < 2.0  # Average < 2 seconds


class EmailGenerationUser(HttpUser):
    """Locust user class for load testing."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """Initialize user session."""
        self.context = {
            "purpose": "Product launch",
            "audience": "Enterprise customers",
            "message": "New AI features",
            "tone": "Professional",
        }

    @task(2)
    def generate_subject(self):
        """Generate email subject."""
        response = self.client.post("/api/ai/email/subject", json=self.context)
        assert response.status_code == 200

    @task(1)
    def generate_body(self):
        """Generate email body."""
        self.context["subject"] = "Test Subject"
        self.context["cta"] = "Schedule demo"

        response = self.client.post("/api/ai/email/body", json=self.context)
        assert response.status_code == 200


class TestCache:
    """Cache performance test suite."""

    @pytest.mark.performance
    def test_cache_performance(self, mock_env, mock_monitoring, test_cache):
        """Test cache hit/miss performance."""
        agent = EmailAgent(model_name="gpt-4")
        context = {
            "purpose": "Product launch",
            "audience": "Enterprise customers",
            "message": "New AI features",
            "tone": "Professional",
        }

        # First request (cache miss)
        start_time = time.time()
        subject1 = agent.generate_subject(context)
        cache_miss_time = time.time() - start_time

        # Second request (cache hit)
        start_time = time.time()
        subject2 = agent.generate_subject(context)
        cache_hit_time = time.time() - start_time

        # Cache hit should be significantly faster
        assert cache_hit_time < cache_miss_time * 0.5
        assert subject1 == subject2  # Results should be identical
