"""
AI Performance Benchmarking Module

This module provides tools for benchmarking AI service performance,
tracking response times, and generating performance reports.
"""

import time
import asyncio
import logging
import statistics
import json
import os
from typing import Dict, List, Optional, Any, Tuple, Callable, Awaitable, Union
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import base64

# Local imports
from ..monitoring.ai_metrics_service import AIMetricsService
from ..adapters.base import ModelRequest, ModelResponse
from .. import AIService

# Configure logging
logger = logging.getLogger(__name__)

class AIPerformanceBenchmark:
    """
    Benchmark service for AI model performance.

    This class provides methods for benchmarking AI model performance,
    including latency, throughput, and quality metrics.
    """

    def __init__(self, ai_service: AIService, metrics_service: Optional[AIMetricsService] = None):
        """
        Initialize the benchmark service.

        Args:
            ai_service: The AI service to benchmark
            metrics_service: Optional metrics service for recording results
        """
        self.ai_service = ai_service
        self.metrics_service = metrics_service

        # Benchmark results storage
        self.benchmark_results = {}
        self.baseline_results = {}

        # Load baseline results if available
        self._load_baseline_results()

    async def run_benchmark(
        self,
        model_name: str,
        prompt_templates: List[str],
        iterations: int = 5,
        concurrent_requests: int = 1,
        temperature: float = 0.0,
        max_tokens: int = 100,
        tag: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run a performance benchmark for a specific model.

        Args:
            model_name: The name of the model to benchmark
            prompt_templates: List of prompt templates to use
            iterations: Number of iterations per prompt
            concurrent_requests: Number of concurrent requests
            temperature: Temperature setting for generation
            max_tokens: Maximum tokens to generate
            tag: Optional tag for the benchmark run

        Returns:
            Dictionary with benchmark results
        """
        logger.info(f"Starting benchmark for {model_name} with {len(prompt_templates)} prompts, "
                   f"{iterations} iterations, {concurrent_requests} concurrent requests")

        start_time = time.time()
        benchmark_id = f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Prepare tasks
        all_tasks = []
        for prompt_template in prompt_templates:
            for i in range(iterations):
                all_tasks.append(self._benchmark_single_request(
                    model_name=model_name,
                    prompt=prompt_template,
                    temperature=temperature,
                    max_tokens=max_tokens
                ))

        # Run tasks with concurrency control
        results = []
        for i in range(0, len(all_tasks), concurrent_requests):
            batch = all_tasks[i:i+concurrent_requests]
            batch_results = await asyncio.gather(*batch)
            results.extend(batch_results)

            # Small delay between batches to avoid rate limiting
            if i + concurrent_requests < len(all_tasks):
                await asyncio.sleep(0.5)

        # Calculate statistics
        latencies = [r["latency"] for r in results]
        token_rates = [r["tokens_per_second"] for r in results]

        stats = {
            "latency": {
                "min": min(latencies),
                "max": max(latencies),
                "mean": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "p90": np.percentile(latencies, 90),
                "p95": np.percentile(latencies, 95),
                "p99": np.percentile(latencies, 99),
                "std_dev": statistics.stdev(latencies) if len(latencies) > 1 else 0
            },
            "tokens_per_second": {
                "min": min(token_rates),
                "max": max(token_rates),
                "mean": statistics.mean(token_rates),
                "median": statistics.median(token_rates)
            },
            "total_tokens": sum(r["output_tokens"] for r in results),
            "success_rate": sum(1 for r in results if r["success"]) / len(results) * 100,
            "total_time": time.time() - start_time,
            "throughput": len(results) / (time.time() - start_time)
        }

        # Store benchmark results
        benchmark_result = {
            "id": benchmark_id,
            "model": model_name,
            "timestamp": datetime.now().isoformat(),
            "config": {
                "prompt_count": len(prompt_templates),
                "iterations": iterations,
                "concurrent_requests": concurrent_requests,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "tag": tag
            },
            "stats": stats,
            "raw_results": results
        }

        self.benchmark_results[benchmark_id] = benchmark_result

        # Save results to file
        self._save_benchmark_results(benchmark_id, benchmark_result)

        # Compare with baseline if available
        comparison = self._compare_with_baseline(model_name, stats)
        if comparison:
            benchmark_result["baseline_comparison"] = comparison

        # Record metrics if metrics service is available
        if self.metrics_service:
            self.metrics_service.record_metric(
                "benchmark_latency_mean",
                stats["latency"]["mean"],
                {"model": model_name, "tag": tag or "default"}
            )
            self.metrics_service.record_metric(
                "benchmark_throughput",
                stats["throughput"],
                {"model": model_name, "tag": tag or "default"}
            )
            self.metrics_service.record_metric(
                "benchmark_success_rate",
                stats["success_rate"],
                {"model": model_name, "tag": tag or "default"}
            )

        logger.info(f"Benchmark completed for {model_name}. "
                   f"Mean latency: {stats['latency']['mean']:.2f}s, "
                   f"Throughput: {stats['throughput']:.2f} req/s, "
                   f"Success rate: {stats['success_rate']:.2f}%")

        return benchmark_result

    async def _benchmark_single_request(
        self,
        model_name: str,
        prompt: str,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """
        Benchmark a single request to the model.

        Args:
            model_name: The name of the model
            prompt: The prompt to send
            temperature: Temperature setting
            max_tokens: Maximum tokens to generate

        Returns:
            Dictionary with request results
        """
        start_time = time.time()
        success = True
        error = None
        response = None

        try:
            response = await self.ai_service.generate_text(
                prompt=prompt,
                model_name=model_name,
                temperature=temperature,
                max_tokens=max_tokens
            )

            end_time = time.time()
            latency = end_time - start_time

            # Calculate tokens per second
            input_tokens = response.get("usage", {}).get("prompt_tokens", len(prompt) // 4)
            output_tokens = response.get("usage", {}).get("completion_tokens", len(response.get("text", "")) // 4)

            tokens_per_second = output_tokens / latency if latency > 0 else 0

            return {
                "success": True,
                "latency": latency,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "tokens_per_second": tokens_per_second,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            end_time = time.time()
            latency = end_time - start_time
            success = False
            error = str(e)

            return {
                "success": False,
                "latency": latency,
                "error": error,
                "input_tokens": len(prompt) // 4,
                "output_tokens": 0,
                "tokens_per_second": 0,
                "timestamp": datetime.now().isoformat()
            }

    def set_baseline(self, benchmark_id: str) -> bool:
        """
        Set a benchmark run as the baseline for future comparisons.

        Args:
            benchmark_id: ID of the benchmark run to use as baseline

        Returns:
            True if successful, False otherwise
        """
        if benchmark_id not in self.benchmark_results:
            logger.error(f"Benchmark ID {benchmark_id} not found")
            return False

        benchmark = self.benchmark_results[benchmark_id]
        model_name = benchmark["model"]

        self.baseline_results[model_name] = {
            "id": benchmark_id,
            "timestamp": datetime.now().isoformat(),
            "stats": benchmark["stats"]
        }

        # Save baseline to file
        self._save_baseline_results()

        logger.info(f"Set benchmark {benchmark_id} as baseline for model {model_name}")
        return True

    def _compare_with_baseline(self, model_name: str, stats: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Compare benchmark results with baseline.

        Args:
            model_name: The name of the model
            stats: Statistics from the benchmark run

        Returns:
            Dictionary with comparison results or None if no baseline
        """
        if model_name not in self.baseline_results:
            return None

        baseline = self.baseline_results[model_name]["stats"]

        # Calculate percentage changes
        latency_change = ((stats["latency"]["mean"] - baseline["latency"]["mean"]) /
                          baseline["latency"]["mean"]) * 100

        throughput_change = ((stats["throughput"] - baseline["throughput"]) /
                            baseline["throughput"]) * 100

        success_rate_change = stats["success_rate"] - baseline["success_rate"]

        return {
            "baseline_id": self.baseline_results[model_name]["id"],
            "baseline_timestamp": self.baseline_results[model_name]["timestamp"],
            "latency_change_pct": latency_change,
            "throughput_change_pct": throughput_change,
            "success_rate_change_pct": success_rate_change,
            "improved": latency_change < 0 and throughput_change > 0
        }

    def _save_benchmark_results(self, benchmark_id: str, results: Dict[str, Any]) -> None:
        """
        Save benchmark results to file.

        Args:
            benchmark_id: ID of the benchmark run
            results: Benchmark results to save
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs("benchmark_results", exist_ok=True)

            # Save to file
            file_path = f"benchmark_results/{benchmark_id}.json"
            with open(file_path, "w") as f:
                json.dump(results, f, indent=2)

            logger.info(f"Saved benchmark results to {file_path}")
        except Exception as e:
            logger.error(f"Error saving benchmark results: {e}")

    def _save_baseline_results(self) -> None:
        """Save baseline results to file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs("benchmark_results", exist_ok=True)

            # Save to file
            file_path = "benchmark_results/baselines.json"
            with open(file_path, "w") as f:
                json.dump(self.baseline_results, f, indent=2)

            logger.info(f"Saved baseline results to {file_path}")
        except Exception as e:
            logger.error(f"Error saving baseline results: {e}")

    def _load_baseline_results(self) -> None:
        """Load baseline results from file."""
        try:
            file_path = "benchmark_results/baselines.json"
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    self.baseline_results = json.load(f)

                logger.info(f"Loaded baseline results for {len(self.baseline_results)} models")
        except Exception as e:
            logger.error(f"Error loading baseline results: {e}")

    def get_benchmark_results(self, benchmark_id: str) -> Optional[Dict[str, Any]]:
        """
        Get results for a specific benchmark run.

        Args:
            benchmark_id: ID of the benchmark run

        Returns:
            Dictionary with benchmark results or None if not found
        """
        if benchmark_id in self.benchmark_results:
            return self.benchmark_results[benchmark_id]

        # Try to load from file
        try:
            file_path = f"benchmark_results/{benchmark_id}.json"
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    results = json.load(f)
                    self.benchmark_results[benchmark_id] = results
                    return results
        except Exception as e:
            logger.error(f"Error loading benchmark results: {e}")

        return None

    def list_benchmarks(self, model_name: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List recent benchmark runs.

        Args:
            model_name: Optional filter by model name
            limit: Maximum number of results to return

        Returns:
            List of benchmark summary dictionaries
        """
        # List benchmark files
        try:
            benchmarks = []

            if os.path.exists("benchmark_results"):
                files = [f for f in os.listdir("benchmark_results") if f.endswith(".json") and f != "baselines.json"]

                for file in sorted(files, reverse=True)[:limit * 2]:  # Get more than needed for filtering
                    try:
                        with open(f"benchmark_results/{file}", "r") as f:
                            data = json.load(f)

                            # Filter by model name if specified
                            if model_name and data.get("model") != model_name:
                                continue

                            # Add summary to list
                            benchmarks.append({
                                "id": data.get("id"),
                                "model": data.get("model"),
                                "timestamp": data.get("timestamp"),
                                "tag": data.get("config", {}).get("tag"),
                                "mean_latency": data.get("stats", {}).get("latency", {}).get("mean"),
                                "throughput": data.get("stats", {}).get("throughput"),
                                "success_rate": data.get("stats", {}).get("success_rate")
                            })

                            if len(benchmarks) >= limit:
                                break
                    except Exception as e:
                        logger.error(f"Error reading benchmark file {file}: {e}")

            return benchmarks
        except Exception as e:
            logger.error(f"Error listing benchmarks: {e}")
            return []

    def generate_report(self, benchmark_id: str) -> Optional[Dict[str, Any]]:
        """
        Generate a detailed report for a benchmark run.

        Args:
            benchmark_id: ID of the benchmark run

        Returns:
            Dictionary with report data or None if benchmark not found
        """
        benchmark = self.get_benchmark_results(benchmark_id)
        if not benchmark:
            return None

        # Generate visualizations
        latency_distribution = self._generate_latency_distribution(benchmark)

        # Create report
        report = {
            "benchmark_id": benchmark_id,
            "model": benchmark.get("model"),
            "timestamp": benchmark.get("timestamp"),
            "summary": {
                "mean_latency": benchmark.get("stats", {}).get("latency", {}).get("mean"),
                "p95_latency": benchmark.get("stats", {}).get("latency", {}).get("p95"),
                "throughput": benchmark.get("stats", {}).get("throughput"),
                "success_rate": benchmark.get("stats", {}).get("success_rate"),
                "total_tokens": benchmark.get("stats", {}).get("total_tokens"),
                "total_time": benchmark.get("stats", {}).get("total_time")
            },
            "config": benchmark.get("config", {}),
            "visualizations": {
                "latency_distribution": latency_distribution
            },
            "baseline_comparison": benchmark.get("baseline_comparison")
        }

        return report

    def _generate_latency_distribution(self, benchmark: Dict[str, Any]) -> Optional[str]:
        """
        Generate a latency distribution visualization.

        Args:
            benchmark: Benchmark data

        Returns:
            Base64-encoded PNG image or None if generation fails
        """
        try:
            # Extract latencies
            latencies = [r.get("latency", 0) for r in benchmark.get("raw_results", [])]

            # Create figure
            plt.figure(figsize=(10, 6))
            plt.hist(latencies, bins=20, alpha=0.7, color='blue')
            plt.axvline(statistics.mean(latencies), color='red', linestyle='dashed', linewidth=1, label=f'Mean: {statistics.mean(latencies):.2f}s')
            plt.axvline(statistics.median(latencies), color='green', linestyle='dashed', linewidth=1, label=f'Median: {statistics.median(latencies):.2f}s')
            plt.axvline(np.percentile(latencies, 95), color='orange', linestyle='dashed', linewidth=1, label=f'P95: {np.percentile(latencies, 95):.2f}s')

            plt.title(f'Latency Distribution for {benchmark.get("model")}')
            plt.xlabel('Latency (seconds)')
            plt.ylabel('Frequency')
            plt.legend()
            plt.grid(True, alpha=0.3)

            # Save to BytesIO
            buf = BytesIO()
            plt.savefig(buf, format='png')
            plt.close()

            # Convert to base64
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')

            return img_base64
        except Exception as e:
            logger.error(f"Error generating latency distribution: {e}")
            return None

# Create singleton instances if needed
if __name__ == "__main__":
    from ..dependencies import get_model_service
    from .ai_metrics_service import AIMetricsService

    # Get services
    consolidated_ai_service = get_model_service()
    metrics_service = AIMetricsService()

    # Create benchmark service
    benchmark_service = AIPerformanceBenchmark(consolidated_ai_service, metrics_service)

# Example usage:
"""
# Initialize the benchmark service
model_service = ModelService()
metrics_service = AIMetricsService()
benchmark_service = AIPerformanceBenchmark(model_service, metrics_service)

# Define benchmark prompts
prompts = [
    "Explain the concept of machine learning in simple terms.",
    "Write a short poem about artificial intelligence.",
    "Summarize the key points of the last G20 summit.",
    "Provide three tips for improving productivity.",
    "Explain the difference between supervised and unsupervised learning."
]

# Run benchmark
async def run_benchmark_example():
    results = await benchmark_service.run_benchmark(
        model_name="gpt-3.5-turbo",
        prompt_templates=prompts,
        iterations=3,
        concurrent_requests=2,
        tag="baseline"
    )

    # Set as baseline
    benchmark_service.set_baseline(results["id"])

    # Generate report
    report = benchmark_service.generate_report(results["id"])

    # List recent benchmarks
    benchmarks = benchmark_service.list_benchmarks(model_name="gpt-3.5-turbo")

# Run the example
# asyncio.run(run_benchmark_example())
"""
