"""
AI Performance Benchmark API

This module provides API endpoints for running and managing AI performance benchmarks.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field

from ..monitoring.ai_metrics_service import AIMetricsService, ai_metrics_service
from ..monitoring.ai_performance_benchmark import AIPerformanceBenchmark
from ..dependencies import get_model_service

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/ai/benchmark",
    tags=["ai-benchmark"],
    responses={404: {"description": "Not found"}},
)

# Get consolidated service instance
consolidated_ai_service = get_model_service()

# Create benchmark service
benchmark_service = AIPerformanceBenchmark(consolidated_ai_service, ai_metrics_service)

# Models
class BenchmarkRequest(BaseModel):
    """Request model for running a benchmark."""
    model_name: str = Field(..., description="The name of the model to benchmark")
    prompts: List[str] = Field(..., description="List of prompts to use for benchmarking")
    iterations: int = Field(3, description="Number of iterations per prompt")
    concurrent_requests: int = Field(1, description="Number of concurrent requests")
    temperature: float = Field(0.0, description="Temperature setting for generation")
    max_tokens: int = Field(100, description="Maximum tokens to generate")
    tag: Optional[str] = Field(None, description="Optional tag for the benchmark run")

class BenchmarkSummary(BaseModel):
    """Summary model for benchmark results."""
    id: str
    model: str
    timestamp: str
    tag: Optional[str] = None
    mean_latency: float
    throughput: float
    success_rate: float

class BenchmarkResponse(BaseModel):
    """Response model for benchmark results."""
    id: str
    model: str
    timestamp: str
    config: Dict[str, Any]
    stats: Dict[str, Any]
    baseline_comparison: Optional[Dict[str, Any]] = None

# Background task for running benchmarks
async def run_benchmark_task(
    request: BenchmarkRequest,
    benchmark_id: str
) -> None:
    """
    Background task for running benchmarks.

    Args:
        request: The benchmark request
        benchmark_id: The ID of the benchmark run
    """
    try:
        await benchmark_service.run_benchmark(
            model_name=request.model_name,
            prompt_templates=request.prompts,
            iterations=request.iterations,
            concurrent_requests=request.concurrent_requests,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            tag=request.tag
        )
        logger.info(f"Benchmark {benchmark_id} completed successfully")
    except Exception as e:
        logger.error(f"Error running benchmark {benchmark_id}: {e}")

# Endpoints
@router.post("/run", response_model=Dict[str, str])
async def start_benchmark(
    request: BenchmarkRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, str]:
    """
    Start a benchmark run in the background.

    Args:
        request: The benchmark request
        background_tasks: FastAPI background tasks

    Returns:
        Dictionary with benchmark ID
    """
    # Generate benchmark ID
    import time
    benchmark_id = f"{request.model_name}_{int(time.time())}"

    # Start benchmark in background
    background_tasks.add_task(run_benchmark_task, request, benchmark_id)

    return {"benchmark_id": benchmark_id, "status": "started"}

@router.get("/list", response_model=List[BenchmarkSummary])
async def list_benchmarks(
    model: Optional[str] = Query(None, description="Filter by model name"),
    limit: int = Query(10, description="Maximum number of results to return")
) -> List[BenchmarkSummary]:
    """
    List recent benchmark runs.

    Args:
        model: Optional filter by model name
        limit: Maximum number of results to return

    Returns:
        List of benchmark summaries
    """
    benchmarks = benchmark_service.list_benchmarks(model_name=model, limit=limit)
    return benchmarks

@router.get("/{benchmark_id}", response_model=BenchmarkResponse)
async def get_benchmark(
    benchmark_id: str
) -> BenchmarkResponse:
    """
    Get results for a specific benchmark run.

    Args:
        benchmark_id: ID of the benchmark run

    Returns:
        Benchmark results
    """
    benchmark = benchmark_service.get_benchmark_results(benchmark_id)
    if not benchmark:
        raise HTTPException(status_code=404, detail=f"Benchmark {benchmark_id} not found")

    return benchmark

@router.post("/{benchmark_id}/baseline", response_model=Dict[str, str])
async def set_baseline(
    benchmark_id: str
) -> Dict[str, str]:
    """
    Set a benchmark run as the baseline for future comparisons.

    Args:
        benchmark_id: ID of the benchmark run to use as baseline

    Returns:
        Status message
    """
    success = benchmark_service.set_baseline(benchmark_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Benchmark {benchmark_id} not found")

    return {"status": "success", "message": f"Benchmark {benchmark_id} set as baseline"}

@router.get("/{benchmark_id}/report", response_model=Dict[str, Any])
async def get_report(
    benchmark_id: str
) -> Dict[str, Any]:
    """
    Generate a detailed report for a benchmark run.

    Args:
        benchmark_id: ID of the benchmark run

    Returns:
        Benchmark report
    """
    report = benchmark_service.generate_report(benchmark_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Benchmark {benchmark_id} not found")

    return report
