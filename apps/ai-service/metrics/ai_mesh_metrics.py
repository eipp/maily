"""
Prometheus Metrics for AI Mesh Network

This module defines metrics for monitoring the AI Mesh Network performance,
usage, and health using Prometheus.
"""

import time
import logging
import asyncio
from prometheus_client import Counter, Histogram, Gauge, Info
from typing import Dict, Any, Optional, List

logger = logging.getLogger("ai_service.metrics.ai_mesh_metrics")

# Initialize Prometheus metrics
# Task and memory metrics
TASK_COUNTER = Counter(
    "ai_mesh_tasks_total",
    "Total number of tasks processed by AI Mesh Network",
    ["network_id", "status"]
)

TASK_PROCESSING_TIME = Histogram(
    "ai_mesh_task_processing_seconds",
    "Time taken to process tasks",
    ["network_id", "task_type"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0)
)

TASK_QUEUE_SIZE = Gauge(
    "ai_mesh_task_queue_size",
    "Current size of the task queue",
    ["network_id"]
)

MEMORY_ITEMS = Gauge(
    "ai_mesh_memory_items",
    "Number of memory items in the network",
    ["network_id", "memory_type"]
)

MEMORY_RETRIEVAL_TIME = Histogram(
    "ai_mesh_memory_retrieval_seconds",
    "Time taken to retrieve memories",
    ["network_id", "query_type"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

# Agent metrics
AGENT_TASK_COUNTER = Counter(
    "ai_mesh_agent_tasks_total",
    "Total number of tasks processed by each agent type",
    ["network_id", "agent_type", "status"]
)

AGENT_PROCESSING_TIME = Histogram(
    "ai_mesh_agent_processing_seconds",
    "Time taken by agents to process tasks",
    ["network_id", "agent_type"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)
)

AGENT_CONFIDENCE = Gauge(
    "ai_mesh_agent_confidence",
    "Confidence scores of agent responses",
    ["network_id", "agent_type"]
)

# Model usage metrics
MODEL_USAGE_COUNTER = Counter(
    "ai_mesh_model_usage_total",
    "Total number of model API calls",
    ["model", "provider"]
)

MODEL_TOKEN_COUNTER = Counter(
    "ai_mesh_model_tokens_total",
    "Total number of tokens used",
    ["model", "provider", "token_type"]
)

MODEL_COST_COUNTER = Counter(
    "ai_mesh_model_cost_total",
    "Estimated cost of model API usage in USD",
    ["model", "provider"]
)

MODEL_ERROR_COUNTER = Counter(
    "ai_mesh_model_errors_total",
    "Number of model API errors",
    ["model", "provider", "error_type"]
)

# Network info
NETWORK_INFO = Info(
    "ai_mesh_network_info",
    "Information about AI Mesh Networks"
)

# WebSocket connection metrics
WEBSOCKET_CONNECTIONS = Gauge(
    "ai_mesh_websocket_connections",
    "Number of active WebSocket connections",
    ["network_id"]
)

WEBSOCKET_MESSAGES = Counter(
    "ai_mesh_websocket_messages_total",
    "Total number of WebSocket messages",
    ["network_id", "direction", "message_type"]
)

# Embedding metrics
EMBEDDING_REQUESTS = Counter(
    "ai_mesh_embedding_requests_total",
    "Total number of embedding generation requests",
    ["model"]
)

EMBEDDING_PROCESSING_TIME = Histogram(
    "ai_mesh_embedding_processing_seconds",
    "Time taken to generate embeddings",
    ["model"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

VECTOR_SEARCH_TIME = Histogram(
    "ai_mesh_vector_search_seconds",
    "Time taken for vector similarity search",
    ["network_id"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

# Functions to record metrics

def record_task_start(network_id: str, task_id: str, task_type: str = "general"):
    """Record metrics for task start"""
    TASK_COUNTER.labels(network_id=network_id, status="started").inc()
    # Adjust gauge
    TASK_QUEUE_SIZE.labels(network_id=network_id).inc()

def record_task_completion(
    network_id: str,
    task_id: str,
    processing_time: float,
    task_type: str = "general",
    status: str = "completed"
):
    """Record metrics for task completion"""
    TASK_COUNTER.labels(network_id=network_id, status=status).inc()
    TASK_PROCESSING_TIME.labels(network_id=network_id, task_type=task_type).observe(processing_time)
    # Adjust gauge
    TASK_QUEUE_SIZE.labels(network_id=network_id).dec()

def record_agent_task(
    network_id: str,
    agent_type: str,
    processing_time: float,
    confidence: float,
    status: str = "completed"
):
    """Record metrics for agent task processing"""
    AGENT_TASK_COUNTER.labels(network_id=network_id, agent_type=agent_type, status=status).inc()
    AGENT_PROCESSING_TIME.labels(network_id=network_id, agent_type=agent_type).observe(processing_time)
    AGENT_CONFIDENCE.labels(network_id=network_id, agent_type=agent_type).set(confidence)

def record_model_usage(
    model: str,
    provider: str,
    prompt_tokens: int,
    completion_tokens: int,
    cost: float = 0.0
):
    """Record metrics for model API usage"""
    MODEL_USAGE_COUNTER.labels(model=model, provider=provider).inc()
    MODEL_TOKEN_COUNTER.labels(model=model, provider=provider, token_type="prompt").inc(prompt_tokens)
    MODEL_TOKEN_COUNTER.labels(model=model, provider=provider, token_type="completion").inc(completion_tokens)
    MODEL_COST_COUNTER.labels(model=model, provider=provider).inc(cost)

def record_model_error(model: str, provider: str, error_type: str):
    """Record metrics for model API errors"""
    MODEL_ERROR_COUNTER.labels(model=model, provider=provider, error_type=error_type).inc()

def update_memory_metrics(network_id: str, memory_counts: Dict[str, int]):
    """Update metrics for memory items"""
    for memory_type, count in memory_counts.items():
        MEMORY_ITEMS.labels(network_id=network_id, memory_type=memory_type).set(count)

def record_memory_retrieval(network_id: str, query_type: str, retrieval_time: float):
    """Record metrics for memory retrieval"""
    MEMORY_RETRIEVAL_TIME.labels(network_id=network_id, query_type=query_type).observe(retrieval_time)

def record_websocket_connection(network_id: str, is_connect: bool = True):
    """Record metrics for WebSocket connections"""
    if is_connect:
        WEBSOCKET_CONNECTIONS.labels(network_id=network_id).inc()
    else:
        WEBSOCKET_CONNECTIONS.labels(network_id=network_id).dec()

def record_websocket_message(network_id: str, direction: str, message_type: str):
    """Record metrics for WebSocket messages"""
    WEBSOCKET_MESSAGES.labels(
        network_id=network_id, 
        direction=direction, 
        message_type=message_type
    ).inc()

def record_embedding_metrics(model: str, processing_time: float):
    """Record metrics for embedding generation"""
    EMBEDDING_REQUESTS.labels(model=model).inc()
    EMBEDDING_PROCESSING_TIME.labels(model=model).observe(processing_time)

def record_vector_search(network_id: str, search_time: float):
    """Record metrics for vector similarity search"""
    VECTOR_SEARCH_TIME.labels(network_id=network_id).observe(search_time)

def update_network_info(networks: List[Dict[str, Any]]):
    """Update network information metrics"""
    network_info = {}
    
    for network in networks:
        network_id = network.get("id", "unknown")
        network_info[f"network_{network_id}_name"] = network.get("name", "")
        network_info[f"network_{network_id}_agent_count"] = str(len(network.get("agents", [])))
        network_info[f"network_{network_id}_task_count"] = str(len(network.get("tasks", [])))
        network_info[f"network_{network_id}_memory_count"] = str(len(network.get("memories", [])))
        network_info[f"network_{network_id}_status"] = network.get("status", "unknown")
    
    NETWORK_INFO.info(network_info)

# Decorators for timing functions
def timing_decorator(metric):
    """Decorator to time function execution and record to a Prometheus metric"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                execution_time = time.time() - start_time
                # Extract labels from first argument if it's a self instance
                try:
                    labels = {}
                    if len(args) > 0 and hasattr(args[0], 'network_id'):
                        labels['network_id'] = args[0].network_id
                    
                    # Record metric with appropriate labels
                    metric.labels(**labels).observe(execution_time)
                except Exception as e:
                    logger.error(f"Error recording timing metric: {e}")
        
        # For non-async functions
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time = time.time() - start_time
                try:
                    # Extract labels from first argument if it's a self instance
                    labels = {}
                    if len(args) > 0 and hasattr(args[0], 'network_id'):
                        labels['network_id'] = args[0].network_id
                    
                    # Record metric with appropriate labels
                    metric.labels(**labels).observe(execution_time)
                except Exception as e:
                    logger.error(f"Error recording timing metric: {e}")
        
        # Return appropriate wrapper based on whether the function is async
        if asyncio.iscoroutinefunction(func):
            return wrapper
        else:
            return sync_wrapper
    
    return decorator