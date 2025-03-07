#!/usr/bin/env python3
"""
AI Mesh Network Load Test

This script conducts load and performance testing for the AI Mesh Network,
focusing on:
1. Network creation and task submission
2. Memory operations (write/read/search)
3. Concurrent task processing
4. Rate limiting behavior

Usage:
    python ai_mesh_load_test.py --concurrent=10 --duration=300 --intensity=medium
"""

import argparse
import asyncio
import json
import logging
import random
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import statistics
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import httpx
from packages.error_handling.python.http_client import HttpClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ai_mesh_load_test.log')
    ]
)
logger = logging.getLogger("ai_mesh_load_test")

# ANSI Colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

# Test configuration
DEFAULT_CONCURRENT_USERS = 5
DEFAULT_TEST_DURATION = 60  # seconds
DEFAULT_INTENSITY = "medium"  # low, medium, high
DEFAULT_API_URL = "http://localhost:8000"  # Can be overridden with --api-url
DEFAULT_API_KEY = ""  # Can be overridden with --api-key

# Test data metrics
network_ids = []
latencies = {
    "create_network": [],
    "submit_task": [],
    "process_task": [],
    "add_memory": [],
    "get_memory": [],
    "search_memory": []
}
error_counts = {
    "create_network": 0,
    "submit_task": 0,
    "process_task": 0,
    "add_memory": 0,
    "get_memory": 0,
    "search_memory": 0,
    "rate_limited": 0
}
successful_operations = {
    "create_network": 0,
    "submit_task": 0,
    "process_task": 0,
    "add_memory": 0,
    "get_memory": 0,
    "search_memory": 0
}

# Semaphore to limit concurrent API calls
api_semaphore = None

class IntensitySettings:
    """Settings for different test intensity levels"""
    LOW = {
        'task_complexity': (50, 150),  # token range
        'memory_size': (50, 200),      # character range
        'network_count': 2,
        'tasks_per_network': 5,
        'memories_per_network': 10,
        'think_time': (1, 3),          # seconds between operations
    }
    MEDIUM = {
        'task_complexity': (150, 500),
        'memory_size': (200, 800),
        'network_count': 5,
        'tasks_per_network': 10,
        'memories_per_network': 20,
        'think_time': (0.5, 2),
    }
    HIGH = {
        'task_complexity': (500, 1500),
        'memory_size': (800, 2000),
        'network_count': 10,
        'tasks_per_network': 20,
        'memories_per_network': 50,
        'think_time': (0.1, 1),
    }

async def make_api_request(
    client: HttpClient,
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
    operation_name: str = "unknown"
) -> Tuple[bool, Dict[str, Any], float]:
    """
    Make an API request to the AI Mesh Network using standardized HTTP client
    
    Args:
        client: Standardized HTTP client
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint
        data: Request data
        api_key: API key for authentication
        operation_name: Name of operation for metrics
        
    Returns:
        Tuple (success, response_data, latency_ms)
    """
    headers = {
        "Content-Type": "application/json",
    }
    
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    start_time = time.time()
    success = False
    response_data = {}
    
    # Use semaphore to limit concurrent requests
    async with api_semaphore:
        try:
            # Make request using the appropriate method based on the HTTP verb
            if method.upper() == "GET":
                response = await client.async_get(endpoint, headers=headers, timeout=30.0)
            elif method.upper() == "POST":
                response = await client.async_post(endpoint, json=data, headers=headers, timeout=30.0)
            elif method.upper() == "PUT":
                response = await client.async_put(endpoint, json=data, headers=headers, timeout=30.0)
            elif method.upper() == "DELETE":
                response = await client.async_delete(endpoint, headers=headers, timeout=30.0)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
            
            # Check for success
            if 200 <= response.status_code < 300:
                success = True
                latencies[operation_name].append(latency_ms)
                successful_operations[operation_name] += 1
            else:
                # Check if it's a rate limit error
                if response.status_code == 429 or "rate limit" in str(response_data).lower():
                    error_counts["rate_limited"] += 1
                else:
                    error_counts[operation_name] += 1
                
                logger.warning(
                    f"{operation_name} failed: {response.status_code} - {json.dumps(response_data)[:100]}..."
                )
            
            return success, response_data, latency_ms
            
        except httpx.TimeoutException:
            latency_ms = (time.time() - start_time) * 1000
            error_counts[operation_name] += 1
            logger.warning(f"{operation_name} timed out after {latency_ms:.2f}ms")
            return False, {"error": "Request timed out"}, latency_ms
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            error_counts[operation_name] += 1
            logger.error(f"{operation_name} error: {str(e)}")
            return False, {"error": str(e)}, latency_ms

async def create_network(client: HttpClient, base_url: str, api_key: str, user_id: str) -> Tuple[bool, str]:
    """Create an AI Mesh Network"""
    network_name = f"Test Network {user_id[:8]} {uuid.uuid4().hex[:6]}"
    
    agents = [
        {
            "name": "Test Coordinator",
            "type": "coordinator",
            "model": "claude-3-7-sonnet"
        },
        {
            "name": "Test Content Agent",
            "type": "content",
            "model": "claude-3-7-sonnet"
        }
    ]
    
    data = {
        "name": network_name,
        "description": "Network created for load testing",
        "agents": agents
    }
    
    success, response, _ = await make_api_request(
        client, 
        "POST", 
        f"{base_url}/api/mesh/networks",
        data=data,
        api_key=api_key,
        operation_name="create_network"
    )
    
    network_id = response.get("network_id", "")
    if success and network_id:
        network_ids.append(network_id)
        return True, network_id
    
    return False, ""

async def submit_task(
    client: HttpClient, 
    base_url: str, 
    api_key: str, 
    network_id: str,
    complexity: Tuple[int, int]
) -> Tuple[bool, str]:
    """Submit a task to an AI Mesh Network"""
    # Generate task with specified complexity
    token_count = random.randint(*complexity)
    words = []
    for _ in range(token_count // 2):  # Approximate 2 tokens per word
        word_length = random.randint(3, 10)
        words.append(''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(word_length)))
    
    task_description = f"Process the following text and generate insights: {' '.join(words)}"
    
    data = {
        "task": task_description,
        "context": {
            "complexity": token_count,
            "test_id": str(uuid.uuid4())
        },
        "priority": random.randint(1, 10)
    }
    
    success, response, _ = await make_api_request(
        client, 
        "POST", 
        f"{base_url}/api/mesh/networks/{network_id}/tasks",
        data=data,
        api_key=api_key,
        operation_name="submit_task"
    )
    
    task_id = response.get("task_id", "")
    return success, task_id

async def process_task(
    client: HttpClient, 
    base_url: str, 
    api_key: str, 
    network_id: str,
    task_id: str
) -> bool:
    """Process a task in an AI Mesh Network"""
    success, _, _ = await make_api_request(
        client, 
        "POST", 
        f"{base_url}/api/mesh/networks/{network_id}/tasks/{task_id}/process",
        api_key=api_key,
        operation_name="process_task"
    )
    
    return success

async def add_memory(
    client: HttpClient, 
    base_url: str, 
    api_key: str, 
    network_id: str,
    memory_size: Tuple[int, int]
) -> Tuple[bool, str]:
    """Add a memory item to an AI Mesh Network"""
    # Generate memory content with specified size
    content_length = random.randint(*memory_size)
    words = []
    while sum(len(w) for w in words) + len(words) < content_length:
        word_length = random.randint(3, 12)
        words.append(''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(word_length)))
    
    memory_content = ' '.join(words)
    
    memory_types = ["fact", "context", "decision", "feedback"]
    memory_type = random.choice(memory_types)
    
    data = {
        "content": memory_content,
        "type": memory_type,
        "confidence": random.uniform(0.5, 1.0)
    }
    
    success, response, _ = await make_api_request(
        client, 
        "POST", 
        f"{base_url}/api/mesh/networks/{network_id}/memories",
        data=data,
        api_key=api_key,
        operation_name="add_memory"
    )
    
    memory_id = response.get("memory_id", "")
    return success, memory_id

async def get_memories(
    client: HttpClient, 
    base_url: str, 
    api_key: str, 
    network_id: str
) -> bool:
    """Get memories from an AI Mesh Network"""
    success, _, _ = await make_api_request(
        client, 
        "GET", 
        f"{base_url}/api/mesh/networks/{network_id}/memories",
        api_key=api_key,
        operation_name="get_memory"
    )
    
    return success

async def search_memories(
    client: HttpClient, 
    base_url: str, 
    api_key: str, 
    network_id: str,
    query: str
) -> bool:
    """Search memories in an AI Mesh Network"""
    success, _, _ = await make_api_request(
        client, 
        "GET", 
        f"{base_url}/api/mesh/networks/{network_id}/memories/search?query={query}",
        api_key=api_key,
        operation_name="search_memory"
    )
    
    return success

async def user_workflow(
    user_id: str,
    base_url: str,
    api_key: str,
    intensity: str,
    test_duration: int
):
    """Simulate a single user's workflow"""
    # Get settings based on intensity
    if intensity == "low":
        settings = IntensitySettings.LOW
    elif intensity == "high":
        settings = IntensitySettings.HIGH
    else:  # medium is default
        settings = IntensitySettings.MEDIUM
    
    # Set end time for this user's test
    end_time = time.time() + test_duration
    
    # Create HTTP client for this user
    client = HttpClient(base_url=base_url)
    
    try:
        # Create networks for this user
        user_networks = []
        for _ in range(settings['network_count']):
            success, network_id = await create_network(client, base_url, api_key, user_id)
            if success:
                user_networks.append(network_id)
            
            # Random think time between operations
            await asyncio.sleep(random.uniform(*settings['think_time']))
            
            # Check if test time is up
            if time.time() >= end_time:
                break
        
        # For each network, create tasks and memories
        for network_id in user_networks:
            # Add memories to the network
            for _ in range(settings['memories_per_network']):
                if time.time() >= end_time:
                    break
                    
                # Add memory
                success, _ = await add_memory(
                    client, base_url, api_key, network_id, 
                    settings['memory_size']
                )
                
                # Random think time
                await asyncio.sleep(random.uniform(*settings['think_time']))
            
            # Get network memories
            if time.time() < end_time:
                await get_memories(client, base_url, api_key, network_id)
                await asyncio.sleep(random.uniform(*settings['think_time']))
            
            # Search memories with random words
            if time.time() < end_time:
                search_terms = ["test", "important", "decision", "result", "analysis"]
                await search_memories(
                    client, base_url, api_key, network_id, 
                    random.choice(search_terms)
                )
                await asyncio.sleep(random.uniform(*settings['think_time']))
            
            # Submit and process tasks
            task_ids = []
            for _ in range(settings['tasks_per_network']):
                if time.time() >= end_time:
                    break
                    
                # Submit task
                success, task_id = await submit_task(
                    client, base_url, api_key, network_id,
                    settings['task_complexity']
                )
                
                if success and task_id:
                    task_ids.append(task_id)
                
                # Random think time
                await asyncio.sleep(random.uniform(*settings['think_time']))
                
                # Process some tasks (50% chance)
                if task_ids and random.random() < 0.5 and time.time() < end_time:
                    task_id = random.choice(task_ids)
                    await process_task(client, base_url, api_key, network_id, task_id)
                    await asyncio.sleep(random.uniform(*settings['think_time']))
            
            # Process remaining tasks
            for task_id in task_ids:
                if time.time() >= end_time:
                    break
                    
                await process_task(client, base_url, api_key, network_id, task_id)
                await asyncio.sleep(random.uniform(*settings['think_time']))
    finally:
        # Close the HTTP client to release resources
        await client.close()

async def run_load_test(args):
    """Run the AI Mesh Network load test"""
    global api_semaphore
    
    # Create semaphore to limit concurrent API calls
    api_semaphore = asyncio.Semaphore(args.concurrent * 2)  # Allow 2 concurrent requests per user
    
    print(f"{GREEN}Starting AI Mesh Network Load Test{RESET}")
    print(f"Concurrent users: {args.concurrent}")
    print(f"Test duration: {args.duration} seconds")
    print(f"Intensity: {args.intensity}")
    print(f"API URL: {args.api_url}")
    print(f"Using API key: {bool(args.api_key)}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create user workflows
    user_tasks = []
    for i in range(args.concurrent):
        user_id = f"loadtest_user_{uuid.uuid4().hex[:8]}"
        user_tasks.append(
            user_workflow(
                user_id=user_id,
                base_url=args.api_url,
                api_key=args.api_key,
                intensity=args.intensity,
                test_duration=args.duration
            )
        )
    
    # Start test timer
    start_time = time.time()
    
    # Run all user workflows concurrently
    await asyncio.gather(*user_tasks)
    
    # Calculate test duration
    test_duration = time.time() - start_time
    
    # Print results
    print(f"\n{GREEN}AI Mesh Network Load Test Results:{RESET}")
    print(f"Test duration: {test_duration:.2f} seconds")
    
    # Calculate operation counts and success rates
    total_operations = sum(successful_operations.values()) + sum(error_counts.values()) - error_counts["rate_limited"]
    total_success = sum(successful_operations.values())
    total_errors = sum(error_counts.values()) - error_counts["rate_limited"]
    
    print(f"\n{BLUE}Operation Counts:{RESET}")
    for op, count in successful_operations.items():
        errors = error_counts[op]
        total = count + errors
        if total > 0:
            success_rate = (count / total) * 100
            print(f"  {op}: {count} successful, {errors} failed ({success_rate:.1f}% success)")
    
    print(f"\nRate limited requests: {error_counts['rate_limited']}")
    
    # Calculate overall success rate
    if total_operations > 0:
        overall_success_rate = (total_success / total_operations) * 100
        print(f"\nOverall success rate: {overall_success_rate:.1f}%")
    
    # Calculate throughput
    operations_per_second = total_operations / test_duration
    print(f"Throughput: {operations_per_second:.2f} operations/second")
    
    # Print latency statistics for each operation type
    print(f"\n{BLUE}Latency Statistics (ms):{RESET}")
    for op, latency_list in latencies.items():
        if latency_list:
            avg = statistics.mean(latency_list)
            p50 = statistics.median(latency_list)
            p95 = sorted(latency_list)[int(len(latency_list) * 0.95)] if len(latency_list) >= 20 else "N/A"
            p99 = sorted(latency_list)[int(len(latency_list) * 0.99)] if len(latency_list) >= 100 else "N/A"
            
            print(f"  {op}:")
            print(f"    Average: {avg:.2f} ms")
            print(f"    Median (p50): {p50:.2f} ms")
            print(f"    p95: {p95 if isinstance(p95, str) else f'{p95:.2f} ms'}")
            print(f"    p99: {p99 if isinstance(p99, str) else f'{p99:.2f} ms'}")
    
    # Generate charts
    if args.generate_charts:
        generate_charts()
    
    return overall_success_rate >= 90  # Consider test successful if overall success rate is at least 90%

def generate_charts():
    """Generate charts from test results"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create a new figure for operation counts
    plt.figure(figsize=(10, 6))
    
    # Plot success and error counts for each operation
    operations = list(successful_operations.keys())
    success_counts = [successful_operations[op] for op in operations]
    error_counts_list = [error_counts[op] for op in operations]
    
    x = np.arange(len(operations))
    width = 0.35
    
    plt.bar(x - width/2, success_counts, width, label='Success', color='green')
    plt.bar(x + width/2, error_counts_list, width, label='Error', color='red')
    
    plt.title('Operation Counts')
    plt.xlabel('Operation')
    plt.ylabel('Count')
    plt.xticks(x, operations, rotation=45)
    plt.legend()
    plt.tight_layout()
    
    # Save the chart
    plt.savefig(f'ai_mesh_load_test_ops_{timestamp}.png')
    
    # Create a new figure for latency statistics
    plt.figure(figsize=(10, 6))
    
    # Prepare data for box plot
    latency_data = []
    for op in operations:
        if latencies[op]:
            latency_data.append(latencies[op])
        else:
            latency_data.append([0])  # Empty placeholder
    
    plt.boxplot(latency_data, labels=operations)
    plt.title('Operation Latency (ms)')
    plt.ylabel('Latency (ms)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save the chart
    plt.savefig(f'ai_mesh_load_test_latency_{timestamp}.png')
    
    print(f"\nCharts saved as ai_mesh_load_test_ops_{timestamp}.png and ai_mesh_load_test_latency_{timestamp}.png")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="AI Mesh Network Load Test")
    parser.add_argument("--concurrent", type=int, default=DEFAULT_CONCURRENT_USERS,
                        help=f"Number of concurrent users (default: {DEFAULT_CONCURRENT_USERS})")
    parser.add_argument("--duration", type=int, default=DEFAULT_TEST_DURATION,
                        help=f"Test duration in seconds (default: {DEFAULT_TEST_DURATION})")
    parser.add_argument("--intensity", choices=['low', 'medium', 'high'], 
                        default=DEFAULT_INTENSITY,
                        help=f"Test intensity (default: {DEFAULT_INTENSITY})")
    parser.add_argument("--api-url", default=DEFAULT_API_URL,
                        help=f"API base URL (default: {DEFAULT_API_URL})")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY,
                        help="API key for authentication")
    parser.add_argument("--generate-charts", action="store_true",
                        help="Generate charts for test results")
    return parser.parse_args()

async def main():
    """Main function"""
    args = parse_args()
    success = await run_load_test(args)
    return 0 if success else 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)