#!/usr/bin/env python3
"""
AI Agent Responsiveness Test
This script tests the responsiveness of the AI agent service under various conditions
"""

import time
import random
import argparse
import concurrent.futures
import statistics
import sys
import json
from datetime import datetime

# ANSI Colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

# Default configuration
DEFAULT_ITERATIONS = 50
DEFAULT_CONCURRENT = 5
DEFAULT_COMPLEXITY = 'medium'  # low, medium, high
API_ENDPOINT = "https://api.maily.example.com/ai/agent"

class ComplexitySettings:
    """Settings for different complexity levels"""
    LOW = {
        'token_count': (50, 100),
        'latency_threshold': 1000,  # ms
        'timeout_threshold': 2000,  # ms
    }
    MEDIUM = {
        'token_count': (100, 300),
        'latency_threshold': 2000,  # ms
        'timeout_threshold': 4000,  # ms
    }
    HIGH = {
        'token_count': (300, 800),
        'latency_threshold': 5000,  # ms
        'timeout_threshold': 8000,  # ms
    }

def simulate_ai_agent_request(iteration, complexity='medium'):
    """Simulate an AI agent request with specified complexity"""
    
    # Get complexity settings
    if complexity == 'low':
        settings = ComplexitySettings.LOW
    elif complexity == 'high':
        settings = ComplexitySettings.HIGH
    else:  # medium is default
        settings = ComplexitySettings.MEDIUM
    
    token_count = random.randint(*settings['token_count'])
    
    start_time = time.time()
    
    # In a real test, this would make an actual API call
    # response = requests.post(API_ENDPOINT, json={
    #     'prompt': f"Generate a response with approximately {token_count} tokens",
    #     'settings': {
    #         'max_tokens': token_count * 1.5,
    #         'temperature': 0.7,
    #     }
    # })
    
    # Simulate API call with varying latency based on token count
    # More tokens = longer processing time
    base_latency = 0.2 + (token_count / 500)  # base latency in seconds
    jitter = random.uniform(-0.1, 0.3)  # add some randomness
    
    # Occasionally simulate timeouts or errors
    error = False
    timeout = False
    
    if random.random() < 0.02:  # 2% chance of error
        error = True
        time.sleep(random.uniform(0.1, 0.3))  # Quick error response
    elif random.random() < 0.05:  # 5% chance of slow response/timeout
        timeout = True
        time.sleep(settings['timeout_threshold'] / 1000 + random.uniform(0, 0.5))
    else:
        # Normal response with some jitter
        time.sleep(base_latency + jitter)
    
    end_time = time.time()
    latency_ms = (end_time - start_time) * 1000  # convert to ms
    
    # Simulate token output based on request
    output_tokens = token_count if not error else 0
    
    return {
        'iteration': iteration,
        'latency_ms': latency_ms,
        'complexity': complexity,
        'token_count': token_count,
        'output_tokens': output_tokens,
        'error': error,
        'timeout': timeout or latency_ms > settings['timeout_threshold'],
        'threshold_exceeded': latency_ms > settings['latency_threshold']
    }

def run_ai_agent_test(iterations=DEFAULT_ITERATIONS, 
                      concurrent=DEFAULT_CONCURRENT, 
                      complexity=DEFAULT_COMPLEXITY):
    """Run the AI agent responsiveness test"""
    
    print(f"{GREEN}Starting AI Agent Responsiveness Test{RESET}")
    print(f"Iterations: {iterations}")
    print(f"Concurrent requests: {concurrent}")
    print(f"Complexity: {complexity}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    start_time = time.time()
    
    # Run concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent) as executor:
        futures = []
        for i in range(iterations):
            futures.append(executor.submit(simulate_ai_agent_request, i, complexity))
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            try:
                result = future.result()
                results.append(result)
                
                # Show progress
                if (i + 1) % 10 == 0 or (i + 1) == iterations:
                    print(f"Completed {i + 1}/{iterations} requests", end='\r')
            except Exception as e:
                print(f"{RED}Error in request: {e}{RESET}")
    
    # Calculate statistics
    latencies = [r['latency_ms'] for r in results]
    errors = sum(1 for r in results if r['error'])
    timeouts = sum(1 for r in results if r['timeout'])
    threshold_exceeded = sum(1 for r in results if r['threshold_exceeded'])
    
    if latencies:
        avg_latency = statistics.mean(latencies)
        median_latency = statistics.median(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        
        latencies_no_timeouts = [l for l, t in zip(latencies, [r['timeout'] for r in results]) if not t]
        avg_latency_no_timeouts = statistics.mean(latencies_no_timeouts) if latencies_no_timeouts else 0
    else:
        avg_latency = median_latency = min_latency = max_latency = p95_latency = avg_latency_no_timeouts = 0
    
    error_rate = (errors / iterations) * 100 if iterations > 0 else 0
    timeout_rate = (timeouts / iterations) * 100 if iterations > 0 else 0
    threshold_exceeded_rate = (threshold_exceeded / iterations) * 100 if iterations > 0 else 0
    
    # Define settings based on complexity
    if complexity == 'low':
        settings = ComplexitySettings.LOW
    elif complexity == 'high':
        settings = ComplexitySettings.HIGH
    else:  # medium is default
        settings = ComplexitySettings.MEDIUM
    
    # Print results
    print(f"\n{GREEN}AI Agent Responsiveness Test Results:{RESET}")
    print(f"Total Requests: {iterations}")
    print(f"Errors: {errors} ({error_rate:.2f}%)")
    print(f"Timeouts: {timeouts} ({timeout_rate:.2f}%)")
    print(f"Requests exceeding latency threshold: {threshold_exceeded} ({threshold_exceeded_rate:.2f}%)")
    print(f"Average Latency: {avg_latency:.2f} ms")
    print(f"Median Latency: {median_latency:.2f} ms")
    print(f"Min Latency: {min_latency:.2f} ms")
    print(f"Max Latency: {max_latency:.2f} ms")
    print(f"P95 Latency: {p95_latency:.2f} ms")
    print(f"Average Latency (excluding timeouts): {avg_latency_no_timeouts:.2f} ms")
    print(f"Total Test Duration: {time.time() - start_time:.2f} seconds")
    
    # Check against thresholds
    success = True
    
    if error_rate > 5:
        print(f"{RED}FAIL: Error rate ({error_rate:.2f}%) exceeds threshold (5%){RESET}")
        success = False
    
    if timeout_rate > 10:
        print(f"{RED}FAIL: Timeout rate ({timeout_rate:.2f}%) exceeds threshold (10%){RESET}")
        success = False
    
    if p95_latency > settings['latency_threshold'] * 1.5:
        print(f"{RED}FAIL: P95 latency ({p95_latency:.2f} ms) exceeds 1.5x threshold ({settings['latency_threshold'] * 1.5} ms){RESET}")
        success = False
    
    if success:
        print(f"{GREEN}SUCCESS: All AI agent responsiveness metrics within acceptable thresholds{RESET}")
    else:
        print(f"{YELLOW}WARNING: Some AI agent responsiveness metrics failed to meet thresholds{RESET}")
    
    return success

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="AI Agent Responsiveness Test")
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS,
                        help=f"Number of test iterations (default: {DEFAULT_ITERATIONS})")
    parser.add_argument("--concurrent", type=int, default=DEFAULT_CONCURRENT,
                        help=f"Number of concurrent requests (default: {DEFAULT_CONCURRENT})")
    parser.add_argument("--complexity", choices=['low', 'medium', 'high'], 
                        default=DEFAULT_COMPLEXITY,
                        help=f"Request complexity (default: {DEFAULT_COMPLEXITY})")
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_args()
    success = run_ai_agent_test(
        iterations=args.iterations,
        concurrent=args.concurrent,
        complexity=args.complexity
    )
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())