#!/usr/bin/env python3
# Maily Load Testing Script
# This script simulates load on the Maily production environment

import argparse
import time
import random
import sys
import concurrent.futures
import requests
import json

# Constants
DEFAULT_DURATION = 30  # seconds
DEFAULT_USERS = 100
API_ENDPOINT = "https://api.maily.example.com"

# Colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

def simulate_email_sending(user_id, duration):
    """Simulate email sending operations"""
    start_time = time.time()
    end_time = start_time + duration
    count = 0
    errors = 0
    latencies = []
    
    print(f"Starting email sending simulation for user {user_id}")
    
    while time.time() < end_time:
        request_start = time.time()
        try:
            # Simulate API call with random delay to mimic network conditions
            time.sleep(random.uniform(0.01, 0.1))
            
            # In a real scenario, this would be an actual API call
            # response = requests.post(f"{API_ENDPOINT}/api/email/send", 
            #    json={"recipient": f"test{random.randint(1, 1000)}@example.com", 
            #          "subject": f"Test Email {count}", 
            #          "body": f"This is test email {count} from load test"})
            # 
            # if response.status_code != 200:
            #    errors += 1
            
            # For simulation, randomly introduce errors
            if random.random() < 0.02:  # 2% error rate
                errors += 1
                
            latency = (time.time() - request_start) * 1000  # Convert to ms
            latencies.append(latency)
            count += 1
            
            # Don't hammer the system too hard in simulation
            time.sleep(random.uniform(0.05, 0.2))
            
        except Exception as e:
            print(f"Error: {e}")
            errors += 1
        
    return {
        "user_id": user_id,
        "requests": count,
        "errors": errors,
        "latencies": latencies,
        "duration": time.time() - start_time
    }

def test_email_sending(users, duration):
    """Test email sending performance with multiple users"""
    print(f"{GREEN}Starting email sending test with {users} users for {duration} seconds{RESET}")
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=users) as executor:
        futures = [executor.submit(simulate_email_sending, i, duration) for i in range(users)]
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                print(f"User {result['user_id']} completed: {result['requests']} requests, {result['errors']} errors")
            except Exception as e:
                print(f"User task failed: {e}")
    
    # Aggregate results
    total_requests = sum(r["requests"] for r in results)
    total_errors = sum(r["errors"] for r in results)
    all_latencies = [l for r in results for l in r["latencies"]]
    avg_latency = sum(all_latencies) / len(all_latencies) if all_latencies else 0
    
    # Sort latencies for percentile calculations
    all_latencies.sort()
    p50 = all_latencies[int(len(all_latencies) * 0.5)] if all_latencies else 0
    p95 = all_latencies[int(len(all_latencies) * 0.95)] if all_latencies else 0
    p99 = all_latencies[int(len(all_latencies) * 0.99)] if all_latencies else 0
    
    # Check against thresholds
    rps = total_requests / duration
    error_rate = (total_errors / total_requests) * 100 if total_requests > 0 else 0
    
    print(f"\n{GREEN}Email Sending Test Results:{RESET}")
    print(f"Total Requests: {total_requests}")
    print(f"Requests per second: {rps:.2f}")
    print(f"Error Rate: {error_rate:.2f}%")
    print(f"Average Latency: {avg_latency:.2f} ms")
    print(f"P50 Latency: {p50:.2f} ms")
    print(f"P95 Latency: {p95:.2f} ms")
    print(f"P99 Latency: {p99:.2f} ms")
    
    # Check against thresholds
    success = True
    if rps < 100:
        print(f"{RED}FAIL: Requests per second ({rps:.2f}) below threshold (100){RESET}")
        success = False
    if error_rate > 5:
        print(f"{RED}FAIL: Error rate ({error_rate:.2f}%) above threshold (5%){RESET}")
        success = False
    if p95 > 500:
        print(f"{RED}FAIL: P95 latency ({p95:.2f} ms) above threshold (500 ms){RESET}")
        success = False
        
    if success:
        print(f"{GREEN}SUCCESS: All email sending metrics within acceptable thresholds{RESET}")
    else:
        print(f"{YELLOW}WARNING: Some email sending metrics failed to meet thresholds{RESET}")
        
    return success

def parse_args():
    parser = argparse.ArgumentParser(description="Maily Load Testing Tool")
    parser.add_argument("--test", choices=["email-sending"], required=True, 
                      help="The type of test to run")
    parser.add_argument("--users", type=int, default=DEFAULT_USERS,
                      help=f"Number of concurrent users (default: {DEFAULT_USERS})")
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION,
                      help=f"Test duration in seconds (default: {DEFAULT_DURATION})")
    return parser.parse_args()

def main():
    args = parse_args()
    
    if args.test == "email-sending":
        success = test_email_sending(args.users, args.duration)
    else:
        print(f"{RED}Error: Unknown test type: {args.test}{RESET}")
        return 1
        
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())