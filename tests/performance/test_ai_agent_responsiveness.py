#!/usr/bin/env python3
"""
AI Agent Responsiveness Test

This script tests the responsiveness of the AI agents under various loads
to ensure they meet performance requirements for production.
"""

import asyncio
import argparse
import time
import json
import random
import statistics
from datetime import datetime
import logging
import sys
import aiohttp
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Sample prompts for testing various agent capabilities
SAMPLE_PROMPTS = [
    "Suggest a good email subject line for a marketing campaign about sustainable products",
    "Write a short paragraph for an email about our new product launch",
    "Summarize this email thread into 3 bullet points",
    "What's the best time to send emails to customers in different time zones?",
    "Analyze these email open rates and suggest improvements",
    "Create a personalized email greeting for a VIP customer",
    "Draft a response to a customer complaint about late delivery",
    "Generate 5 ideas for our monthly newsletter",
    "Rewrite this paragraph to sound more professional",
    "What's the optimal length for a cold outreach email?",
]

# Agent types to test
AGENT_TYPES = [
    "email_composer",
    "canvas_assistant",
    "content_analyzer",
    "email_analyzer",
    "conversation_assistant",
]

class AIAgentPerformanceTester:
    """Test AI Agent performance and responsiveness"""
    
    def __init__(self, 
                 base_url: str, 
                 concurrency: int = 5, 
                 total_requests: int = 50,
                 timeout: int = 30):
        """
        Initialize performance tester
        
        Args:
            base_url: API base URL
            concurrency: Max concurrent requests
            total_requests: Total number of requests to make
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.concurrency = concurrency
        self.total_requests = total_requests
        self.timeout = timeout
        self.results = []
        self.semaphore = asyncio.Semaphore(concurrency)
        
    async def test_agent(self, agent_type: str, prompt: str) -> Dict[str, Any]:
        """
        Test a single agent request
        
        Args:
            agent_type: Type of agent to test
            prompt: The prompt to send to the agent
            
        Returns:
            Test result with timing and status info
        """
        async with self.semaphore:
            start_time = time.time()
            result = {
                "agent_type": agent_type,
                "prompt_length": len(prompt),
                "success": False,
                "duration": 0,
                "error": None,
                "response_length": 0,
                "timestamp": datetime.now().isoformat()
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    request_url = f"{self.base_url}/ai/agent/{agent_type}"
                    payload = {
                        "prompt": prompt,
                        "max_tokens": 500,
                        "temperature": 0.7
                    }
                    
                    # Make the request
                    async with session.post(
                        request_url, 
                        json=payload,
                        timeout=self.timeout
                    ) as response:
                        end_time = time.time()
                        duration = end_time - start_time
                        
                        if response.status == 200:
                            response_data = await response.json()
                            result.update({
                                "success": True,
                                "duration": duration,
                                "status_code": response.status,
                                "response_length": len(response_data.get("response", "")),
                                "tokens_used": response_data.get("tokens_used", 0)
                            })
                        else:
                            error_text = await response.text()
                            result.update({
                                "success": False,
                                "duration": duration,
                                "status_code": response.status,
                                "error": f"HTTP {response.status}: {error_text}"
                            })
            except asyncio.TimeoutError:
                end_time = time.time()
                result.update({
                    "success": False,
                    "duration": end_time - start_time,
                    "error": f"Request timed out after {self.timeout} seconds"
                })
            except Exception as e:
                end_time = time.time()
                result.update({
                    "success": False,
                    "duration": end_time - start_time,
                    "error": str(e)
                })
                
            return result
    
    async def run_tests(self) -> List[Dict[str, Any]]:
        """
        Run all agent tests
        
        Returns:
            List of test results
        """
        logger.info(f"Starting AI agent performance tests with {self.concurrency} concurrent requests")
        logger.info(f"Total requests: {self.total_requests}")
        
        # Generate test cases
        test_cases = []
        for _ in range(self.total_requests):
            agent_type = random.choice(AGENT_TYPES)
            prompt = random.choice(SAMPLE_PROMPTS)
            test_cases.append((agent_type, prompt))
        
        # Create tasks for all test cases
        tasks = [self.test_agent(agent_type, prompt) for agent_type, prompt in test_cases]
        
        # Execute tests and collect results
        results = await asyncio.gather(*tasks)
        self.results = results
        
        return results
    
    def analyze_results(self) -> Dict[str, Any]:
        """
        Analyze test results
        
        Returns:
            Analysis of test results
        """
        if not self.results:
            return {"error": "No test results available"}
        
        # Calculate overall statistics
        success_count = sum(1 for r in self.results if r["success"])
        success_rate = (success_count / len(self.results)) * 100
        
        # Get durations for successful requests
        success_durations = [r["duration"] for r in self.results if r["success"]]
        
        if not success_durations:
            return {
                "success_rate": 0,
                "total_requests": len(self.results),
                "error": "No successful requests"
            }
        
        # Calculate timing statistics
        avg_duration = statistics.mean(success_durations)
        median_duration = statistics.median(success_durations)
        p95_duration = sorted(success_durations)[int(len(success_durations) * 0.95)]
        min_duration = min(success_durations)
        max_duration = max(success_durations)
        
        # Calculate per-agent statistics
        agent_stats = {}
        for agent_type in AGENT_TYPES:
            agent_results = [r for r in self.results if r["agent_type"] == agent_type]
            if not agent_results:
                continue
                
            agent_success = [r for r in agent_results if r["success"]]
            agent_stats[agent_type] = {
                "requests": len(agent_results),
                "success_rate": (len(agent_success) / len(agent_results)) * 100 if agent_results else 0,
                "avg_duration": statistics.mean([r["duration"] for r in agent_success]) if agent_success else 0,
            }
        
        # Determine if performance meets requirements
        meets_requirements = (
            success_rate >= 95 and  # At least 95% success rate
            avg_duration <= 3.0 and  # Average response under 3 seconds 
            p95_duration <= 5.0      # 95% of requests under 5 seconds
        )
        
        return {
            "success_rate": success_rate,
            "total_requests": len(self.results),
            "successful_requests": success_count,
            "avg_duration": avg_duration,
            "median_duration": median_duration,
            "p95_duration": p95_duration,
            "min_duration": min_duration,
            "max_duration": max_duration,
            "agent_stats": agent_stats,
            "meets_requirements": meets_requirements
        }

def print_results(analysis: Dict[str, Any]):
    """Print formatted analysis results"""
    print("\n" + "="*50)
    print("AI AGENT PERFORMANCE TEST RESULTS")
    print("="*50)
    print(f"Total Requests:      {analysis['total_requests']}")
    print(f"Successful Requests: {analysis['successful_requests']}")
    print(f"Success Rate:        {analysis['success_rate']:.2f}%")
    print(f"Average Duration:    {analysis['avg_duration']:.2f} seconds")
    print(f"Median Duration:     {analysis['median_duration']:.2f} seconds")
    print(f"95th Percentile:     {analysis['p95_duration']:.2f} seconds")
    print(f"Min Duration:        {analysis['min_duration']:.2f} seconds")
    print(f"Max Duration:        {analysis['max_duration']:.2f} seconds")
    
    print("\nPer-Agent Statistics:")
    for agent, stats in analysis.get('agent_stats', {}).items():
        print(f"  {agent}: {stats['requests']} requests, {stats['success_rate']:.2f}% success, {stats['avg_duration']:.2f}s avg")
    
    print("\nPerformance Requirements:")
    print(f"  Success Rate >= 95%:               {'✅' if analysis['success_rate'] >= 95 else '❌'}")
    print(f"  Average Duration <= 3.0 seconds:   {'✅' if analysis['avg_duration'] <= 3.0 else '❌'}")
    print(f"  95th Percentile <= 5.0 seconds:    {'✅' if analysis['p95_duration'] <= 5.0 else '❌'}")
    
    if analysis.get('meets_requirements'):
        print("\n✅ Performance test PASSED - AI agents meet responsiveness requirements")
    else:
        print("\n❌ Performance test FAILED - AI agents do not meet responsiveness requirements")
    
    print("="*50)

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Test AI agent responsiveness')
    parser.add_argument('--api', default='http://localhost:3000/api', help='API base URL')
    parser.add_argument('--concurrency', type=int, default=5, help='Concurrent requests')
    parser.add_argument('--requests', type=int, default=50, help='Total requests to make')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout in seconds')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    args = parser.parse_args()
    
    # Create tester
    tester = AIAgentPerformanceTester(
        base_url=args.api,
        concurrency=args.concurrency,
        total_requests=args.requests,
        timeout=args.timeout
    )
    
    # Run tests
    await tester.run_tests()
    
    # Analyze results
    analysis = tester.analyze_results()
    
    # Output results
    if args.json:
        print(json.dumps(analysis, indent=2))
    else:
        print_results(analysis)
    
    # Exit with appropriate status code
    sys.exit(0 if analysis.get('meets_requirements') else 1)

if __name__ == "__main__":
    asyncio.run(main())