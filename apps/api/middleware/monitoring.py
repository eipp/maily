import time
from typing import Callable

from fastapi import Request

from ..monitoring.metrics import REQUEST_COUNT, REQUEST_LATENCY


async def monitor_requests(request: Request, call_next: Callable):
    """Middleware for monitoring request metrics."""
    start_time = time.time()

    try:
        response = await call_next(request)
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
        ).inc()
    except Exception as e:
        REQUEST_COUNT.labels(
            method=request.method, endpoint=request.url.path, status=500
        ).inc()
        raise e
    finally:
        REQUEST_LATENCY.labels(
            method=request.method, endpoint=request.url.path
        ).observe(time.time() - start_time)

    return response
