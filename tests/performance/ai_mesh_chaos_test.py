#!/usr/bin/env python3
"""
AI Mesh Network Chaos Test

This script conducts chaos testing for the AI Mesh Network, simulating:
1. Network failures and delays
2. Service outages
3. Redis failures
4. Rate limiting boundary conditions
5. Memory exhaustion scenarios

Usage:
    python ai_mesh_chaos_test.py --scenario=network_delay --duration=300
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
from typing import Dict, List, Any, Optional, Tuple, Callable
import aiohttp
import socket
import traceback
import matplotlib.pyplot as plt
import numpy as np
from contextlib import AsyncExitStack

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ai_mesh_chaos_test.log')
    ]
)
logger = logging.getLogger("ai_mesh_chaos_test")

# ANSI Colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

# Test configuration
DEFAULT_TEST_DURATION = 300  # seconds
DEFAULT_SCENARIO = "network_delay"
DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_API_KEY = ""
DEFAULT_RELIABILITY_THRESHOLD = 70  # min % success rate

# Test metrics
successful_operations = 0
failed_operations = 0
timeouts = 0
rate_limits = 0
latencies = []
retry_count = 0
recovery_times = []

# Chaos scenarios
CHAOS_SCENARIOS = [
    "network_delay",
    "request_flood", 
    "connection_drop",
    "service_restart",
    "memory_pressure",
    "mixed_chaos"
]

class RequestContext:
    """Request context for chaos testing"""
    def __init__(self, chaos_scenario: str, api_url: str, api_key: str):
        self.chaos_scenario = chaos_scenario
        self.api_url = api_url
        self.api_key = api_key
        self.failure_mode_active = False
        self.failure_duration = 0
        self.recovery_start_time = 0
        self.test_network_id = None
        self.test_task_id = None
        self.test_memory_id = None
        self.session = None
        self.max_recovery_time = 0

async def make_api_request(
    context: RequestContext,
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    timeout: float = 10.0,
    retry_attempts: int = 3,
    expected_status: Optional[int] = None
) -> Tuple[bool, Dict[str, Any], float]:
    """
    Make an API request to the AI Mesh Network with chaos injection
    
    Args:
        context: Request context with chaos scenario
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint
        data: Request data
        timeout: Request timeout
        retry_attempts: Number of retry attempts
        expected_status: Expected status code for successful response
        
    Returns:
        Tuple (success, response_data, latency_ms)
    """
    global successful_operations, failed_operations, timeouts, latencies, retry_count, rate_limits
    
    headers = {
        "Content-Type": "application/json",
    }
    
    if context.api_key:
        headers["Authorization"] = f"Bearer {context.api_key}"
    
    start_time = time.time()
    success = False
    response_data = {}
    attempts = 0
    
    while attempts < retry_attempts and not success:
        attempts += 1
        if attempts > 1:
            retry_count += 1
            # Exponential backoff with jitter
            backoff = min(30, 2 ** (attempts - 1)) * (0.5 + random.random())
            await asyncio.sleep(backoff)
        
        try:
            # Introduce chaos based on scenario
            modified_timeout = inject_chaos(context, timeout)
            
            # Make request
            try:
                async with context.session.request(
                    method, 
                    endpoint, 
                    json=data, 
                    headers=headers,
                    timeout=modified_timeout
                ) as response:
                    # Calculate latency
                    request_latency_ms = (time.time() - start_time) * 1000
                    latencies.append(request_latency_ms)
                    
                    # Parse response
                    try:
                        response_data = await response.json()
                    except:
                        response_text = await response.text()
                        response_data = {"text": response_text}
                    
                    # Check for success
                    if expected_status:
                        success = response.status == expected_status
                    else:
                        success = 200 <= response.status < 300
                    
                    # Handle rate limits
                    if response.status == 429 or "rate limit" in str(response_data).lower():
                        rate_limits += 1
                        # Don't retry rate limited requests if we're testing rate limits
                        if context.chaos_scenario == "request_flood":
                            break
                    
                    # Track failures for retry
                    if not success and attempts < retry_attempts:
                        # If we were in failure mode but now getting responses,
                        # record recovery time
                        if context.failure_mode_active and response.status != 0:
                            recovery_time = time.time() - context.recovery_start_time
                            if recovery_time > 0:
                                recovery_times.append(recovery_time)
                                context.max_recovery_time = max(context.max_recovery_time, recovery_time)
                                logger.info(f"System recovered after {recovery_time:.2f} seconds")
                            context.failure_mode_active = False
                    
            except asyncio.TimeoutError:
                timeouts += 1
                request_latency_ms = timeout * 1000  # Max latency is timeout
                response_data = {"error": "Request timed out"}
                
                # If this is our first timeout, record the start of recovery monitoring
                if not context.failure_mode_active:
                    context.failure_mode_active = True
                    context.recovery_start_time = time.time()
                
        except Exception as e:
            failed_operations += 1
            traceback.print_exc()
            logger.error(f"Request error: {str(e)}")
            return False, {"error": str(e)}, (time.time() - start_time) * 1000
    
    # Update metrics
    if success:
        successful_operations += 1
    else:
        failed_operations += 1
    
    return success, response_data, request_latency_ms

def inject_chaos(context: RequestContext, timeout: float) -> float:
    """Inject chaos based on scenario"""
    if context.chaos_scenario == "network_delay":
        # Add random delay
        if random.random() < 0.3:  # 30% of requests affected
            delay = random.uniform(0.1, 0.5)  # 100-500ms delay
            time.sleep(delay)
            return timeout  # Return original timeout
            
    elif context.chaos_scenario == "connection_drop":
        # Randomly drop connections
        if random.random() < 0.1:  # 10% of requests affected
            raise ConnectionError("Chaos test: Simulated connection drop")
            
    elif context.chaos_scenario == "request_flood":
        # No special handling needed - the test itself creates the flood
        return timeout
    
    elif context.chaos_scenario == "service_restart":
        # Occasionally simulate very long delays (like a service restart)
        if random.random() < 0.05:  # 5% of requests affected
            time.sleep(random.uniform(5, 15))  # 5-15 second delay
            return timeout
    
    elif context.chaos_scenario == "memory_pressure":
        # No direct way to simulate memory pressure, but we can make requests larger
        # No need to modify timeout
        return timeout
        
    elif context.chaos_scenario == "mixed_chaos":
        # Randomly select from other scenarios
        chaos_type = random.choice(["delay", "drop", "timeout", "normal"])
        
        if chaos_type == "delay":
            delay = random.uniform(0.1, 1.0)
            time.sleep(delay)
        elif chaos_type == "drop":
            if random.random() < 0.1:
                raise ConnectionError("Chaos test: Simulated connection drop")
        elif chaos_type == "timeout":
            if random.random() < 0.05:
                return 0.01  # Very short timeout to force timeout
                
    # Default: no chaos
    return timeout

async def create_test_network(context: RequestContext) -> bool:
    """Create a test network for chaos testing"""
    network_name = f"Chaos Test Network {uuid.uuid4().hex[:6]}"
    
    data = {
        "name": network_name,
        "description": "Network created for chaos testing",
        "agents": [
            {
                "name": "Chaos Coordinator",
                "type": "coordinator",
                "model": "claude-3-7-sonnet"
            },
            {
                "name": "Chaos Content Agent",
                "type": "content",
                "model": "claude-3-7-sonnet"
            }
        ]
    }
    
    success, response, _ = await make_api_request(
        context,
        "POST",
        f"{context.api_url}/api/mesh/networks",
        data=data
    )
    
    if success and "network_id" in response:
        context.test_network_id = response["network_id"]
        logger.info(f"Created test network {context.test_network_id}")
        return True
        
    logger.error(f"Failed to create test network: {response}")
    return False

async def submit_test_task(context: RequestContext) -> bool:
    """Submit a test task for chaos testing"""
    if not context.test_network_id:
        logger.error("No test network available")
        return False
    
    task_text = f"Analyze the following chaos testing data: {uuid.uuid4().hex}"
    data = {
        "task": task_text,
        "context": {"test_type": "chaos", "timestamp": time.time()},
        "priority": 5
    }
    
    success, response, _ = await make_api_request(
        context,
        "POST",
        f"{context.api_url}/api/mesh/networks/{context.test_network_id}/tasks",
        data=data
    )
    
    if success and "task_id" in response:
        context.test_task_id = response["task_id"]
        logger.info(f"Submitted test task {context.test_task_id}")
        return True
        
    logger.error(f"Failed to submit test task: {response}")
    return False

async def add_test_memory(context: RequestContext) -> bool:
    """Add a test memory for chaos testing"""
    if not context.test_network_id:
        logger.error("No test network available")
        return False
    
    memory_size = 200
    if context.chaos_scenario == "memory_pressure":
        # For memory pressure test, create larger memories
        memory_size = random.randint(1000, 5000)
    
    content = f"Chaos test memory: {uuid.uuid4().hex} " + "x" * memory_size
    data = {
        "content": content,
        "type": "context",
        "confidence": 0.9
    }
    
    success, response, _ = await make_api_request(
        context,
        "POST",
        f"{context.api_url}/api/mesh/networks/{context.test_network_id}/memories",
        data=data
    )
    
    if success and "memory_id" in response:
        context.test_memory_id = response["memory_id"]
        logger.info(f"Added test memory {context.test_memory_id}")
        return True
        
    logger.error(f"Failed to add test memory: {response}")
    return False

async def search_memories(context: RequestContext) -> bool:
    """Search memories with chaos conditions"""
    if not context.test_network_id:
        logger.error("No test network available")
        return False
    
    query = random.choice(["test", "chaos", "data", "memory", "analysis"])
    
    success, response, _ = await make_api_request(
        context,
        "GET",
        f"{context.api_url}/api/mesh/networks/{context.test_network_id}/memories/search?query={query}",
        timeout=15.0  # Longer timeout for search
    )
    
    return success

async def process_test_task(context: RequestContext) -> bool:
    """Process a test task with chaos conditions"""
    if not context.test_network_id or not context.test_task_id:
        logger.error("No test network or task available")
        return False
    
    success, response, _ = await make_api_request(
        context,
        "POST",
        f"{context.api_url}/api/mesh/networks/{context.test_network_id}/tasks/{context.test_task_id}/process",
        timeout=30.0  # Longer timeout for processing
    )
    
    return success

async def get_network_status(context: RequestContext) -> bool:
    """Get network status with chaos conditions"""
    if not context.test_network_id:
        logger.error("No test network available")
        return False
    
    success, response, _ = await make_api_request(
        context,
        "GET",
        f"{context.api_url}/api/mesh/networks/{context.test_network_id}",
    )
    
    return success

async def run_request_flood(context: RequestContext, duration: int) -> None:
    """Run a request flood for rate limit testing"""
    if not context.test_network_id:
        await create_test_network(context)
    
    # Flood parameters
    request_delay = 0.01  # 10ms between requests
    flood_end_time = time.time() + duration
    
    # Memory query flood
    flood_count = 0
    while time.time() < flood_end_time:
        query = f"test{random.randint(1, 100)}"
        await make_api_request(
            context,
            "GET",
            f"{context.api_url}/api/mesh/networks/{context.test_network_id}/memories/search?query={query}",
            retry_attempts=1  # Don't retry during flood
        )
        flood_count += 1
        await asyncio.sleep(request_delay)
    
    logger.info(f"Request flood completed: {flood_count} requests sent")

async def run_chaos_test(args):
    """Run the AI Mesh Network chaos test"""
    global successful_operations, failed_operations, timeouts, rate_limits, latencies, recovery_times
    
    print(f"{GREEN}Starting AI Mesh Network Chaos Test{RESET}")
    print(f"Scenario: {args.scenario}")
    print(f"Test duration: {args.duration} seconds")
    print(f"API URL: {args.api_url}")
    print(f"Using API key: {bool(args.api_key)}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize test metrics
    successful_operations = 0
    failed_operations = 0
    timeouts = 0
    rate_limits = 0
    latencies = []
    recovery_times = []
    
    # Create context
    context = RequestContext(args.scenario, args.api_url, args.api_key)
    
    # Start test timer
    start_time = time.time()
    
    # Use AsyncExitStack to ensure proper cleanup
    async with AsyncExitStack() as stack:
        # Create and register session
        context.session = await stack.enter_async_context(aiohttp.ClientSession())
        
        # Create test network
        if not await create_test_network(context):
            logger.error("Failed to create test network, aborting")
            return False
        
        # Special handling for request_flood scenario
        if args.scenario == "request_flood":
            await run_request_flood(context, args.duration)
        else:
            # Normal test flow
            test_end_time = time.time() + args.duration
            
            while time.time() < test_end_time:
                # Randomize operations
                operation = random.choice([
                    "submit_task",
                    "add_memory",
                    "search_memories",
                    "process_task",
                    "get_network_status"
                ])
                
                # Execute selected operation
                if operation == "submit_task":
                    await submit_test_task(context)
                elif operation == "add_memory":
                    await add_test_memory(context)
                elif operation == "search_memories":
                    await search_memories(context)
                elif operation == "process_task":
                    await process_test_task(context)
                elif operation == "get_network_status":
                    await get_network_status(context)
                
                # Add variable delay between operations
                await asyncio.sleep(random.uniform(0.5, 3.0))
    
    # Calculate test duration
    test_duration = time.time() - start_time
    
    # Print results
    print(f"\n{GREEN}AI Mesh Network Chaos Test Results:{RESET}")
    print(f"Test duration: {test_duration:.2f} seconds")
    print(f"Chaos scenario: {args.scenario}")
    
    total_operations = successful_operations + failed_operations
    success_rate = (successful_operations / total_operations * 100) if total_operations > 0 else 0
    
    print(f"\n{BLUE}Operation Statistics:{RESET}")
    print(f"  Total operations: {total_operations}")
    print(f"  Successful: {successful_operations}")
    print(f"  Failed: {failed_operations}")
    print(f"  Timeouts: {timeouts}")
    print(f"  Rate limits: {rate_limits}")
    print(f"  Retries: {retry_count}")
    print(f"  Success rate: {success_rate:.1f}%")
    
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0
    
    print(f"\n{BLUE}Latency Statistics:{RESET}")
    print(f"  Average: {avg_latency:.2f} ms")
    print(f"  Maximum: {max_latency:.2f} ms")
    
    # Recovery statistics
    if recovery_times:
        avg_recovery = sum(recovery_times) / len(recovery_times)
        max_recovery = max(recovery_times)
        print(f"\n{BLUE}Recovery Statistics:{RESET}")
        print(f"  Recovery events: {len(recovery_times)}")
        print(f"  Average recovery time: {avg_recovery:.2f} seconds")
        print(f"  Maximum recovery time: {max_recovery:.2f} seconds")
    
    # Generate chart if requested
    if args.generate_chart:
        generate_chaos_chart(args.scenario, latencies, recovery_times)
    
    # Calculate success against threshold
    reliability_result = success_rate >= args.reliability_threshold
    result_color = GREEN if reliability_result else RED
    print(f"\n{result_color}Reliability threshold: {success_rate:.1f}% vs {args.reliability_threshold}% required{RESET}")
    print(f"{result_color}Test {'PASSED' if reliability_result else 'FAILED'}{RESET}")
    
    return reliability_result

def generate_chaos_chart(scenario, latencies, recovery_times):
    """Generate chart for chaos test results"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create latency histogram
    plt.figure(figsize=(10, 6))
    plt.hist(latencies, bins=50, alpha=0.7, color='blue')
    plt.title(f'Request Latency Distribution - {scenario}')
    plt.xlabel('Latency (ms)')
    plt.ylabel('Frequency')
    plt.grid(True, alpha=0.3)
    
    # Add recovery time markers if available
    if recovery_times:
        for recovery_time in recovery_times:
            plt.axvline(x=recovery_time * 1000, color='red', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    chart_filename = f'chaos_test_{scenario}_{timestamp}.png'
    plt.savefig(chart_filename)
    print(f"\nChart saved as {chart_filename}")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="AI Mesh Network Chaos Test")
    parser.add_argument("--scenario", choices=CHAOS_SCENARIOS, 
                        default=DEFAULT_SCENARIO,
                        help=f"Chaos test scenario (default: {DEFAULT_SCENARIO})")
    parser.add_argument("--duration", type=int, default=DEFAULT_TEST_DURATION,
                        help=f"Test duration in seconds (default: {DEFAULT_TEST_DURATION})")
    parser.add_argument("--api-url", default=DEFAULT_API_URL,
                        help=f"API base URL (default: {DEFAULT_API_URL})")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY,
                        help="API key for authentication")
    parser.add_argument("--reliability-threshold", type=int, default=DEFAULT_RELIABILITY_THRESHOLD,
                        help=f"Minimum success rate percentage to pass (default: {DEFAULT_RELIABILITY_THRESHOLD})")
    parser.add_argument("--generate-chart", action="store_true",
                        help="Generate charts for test results")
    return parser.parse_args()

async def main():
    """Main function"""
    args = parse_args()
    success = await run_chaos_test(args)
    return 0 if success else 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)