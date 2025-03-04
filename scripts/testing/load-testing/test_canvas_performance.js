#!/usr/bin/env node
/**
 * Maily Canvas Performance Test
 * This script tests the performance of the Maily canvas with simulated collaborative users
 */

const { performance } = require('perf_hooks');
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');
const path = require('path');
const fs = require('fs');

// ANSI colors for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
};

// Configuration defaults
const DEFAULT_USERS = 10;
const DEFAULT_DURATION = 60; // seconds
const API_ENDPOINT = 'https://api.maily.example.com';

/**
 * Worker thread - simulates a single user's canvas operations
 */
if (!isMainThread) {
  const { userId, duration } = workerData;
  const startTime = performance.now();
  const endTime = startTime + (duration * 1000);
  let operations = 0;
  let errors = 0;
  const latencies = [];

  console.log(`Starting canvas simulation for user ${userId}`);
  
  // Simulate user operations
  function simulateOperation() {
    if (performance.now() >= endTime) {
      // Report results back to main thread when done
      parentPort.postMessage({ 
        userId, 
        operations, 
        errors, 
        latencies,
        duration: (performance.now() - startTime) / 1000
      });
      return;
    }

    const opStart = performance.now();
    try {
      // Simulate different canvas operations
      const operationType = Math.floor(Math.random() * 5);
      
      // Random delay to simulate thinking/network latency
      const thinkTime = Math.random() * 500;
      
      // This would be a real API call in production code
      /* 
      await fetch(`${API_ENDPOINT}/api/canvas/operation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId: userId,
          operationType: operationType,
          payload: { x: Math.random() * 800, y: Math.random() * 600 },
          timestamp: Date.now()
        })
      });
      */
      
      // Simulate operation result with random error rate
      if (Math.random() < 0.01) { // 1% error rate
        errors++;
        // Simulate recovery
        setTimeout(simulateOperation, 100 + Math.random() * 400);
      } else {
        operations++;
        const latency = performance.now() - opStart;
        latencies.push(latency);
        
        // Schedule next operation
        setTimeout(simulateOperation, thinkTime);
      }
    } catch (error) {
      console.error(`Error in user ${userId}: ${error.message}`);
      errors++;
      setTimeout(simulateOperation, 500); // Retry with backoff
    }
  }
  
  // Start simulation
  simulateOperation();
}

/**
 * Main thread - manages worker threads and aggregates results
 */
if (isMainThread) {
  function parseArgs() {
    const args = process.argv.slice(2);
    const options = {
      users: DEFAULT_USERS,
      duration: DEFAULT_DURATION
    };
    
    for (let i = 0; i < args.length; i++) {
      if (args[i] === '--users' && i + 1 < args.length) {
        options.users = parseInt(args[i + 1], 10);
        i++;
      } else if (args[i] === '--duration' && i + 1 < args.length) {
        options.duration = parseInt(args[i + 1], 10);
        i++;
      }
    }
    
    return options;
  }
  
  function runTest() {
    const options = parseArgs();
    const { users, duration } = options;
    
    console.log(`${colors.green}Starting canvas performance test with ${users} users for ${duration} seconds${colors.reset}`);
    
    const results = [];
    const workers = [];
    let completedWorkers = 0;
    
    for (let i = 0; i < users; i++) {
      const worker = new Worker(__filename, {
        workerData: { userId: i, duration }
      });
      
      worker.on('message', (result) => {
        results.push(result);
        completedWorkers++;
        console.log(`User ${result.userId} completed: ${result.operations} operations, ${result.errors} errors`);
        
        if (completedWorkers === users) {
          processResults(results, duration);
        }
      });
      
      worker.on('error', (error) => {
        console.error(`Worker error: ${error}`);
        completedWorkers++;
        
        if (completedWorkers === users) {
          processResults(results, duration);
        }
      });
      
      workers.push(worker);
    }
  }
  
  function processResults(results, duration) {
    // Aggregate results
    const totalOperations = results.reduce((sum, r) => sum + r.operations, 0);
    const totalErrors = results.reduce((sum, r) => sum + r.errors, 0);
    const allLatencies = results.flatMap(r => r.latencies);
    const avgLatency = allLatencies.reduce((sum, l) => sum + l, 0) / allLatencies.length;
    
    // Calculate operations per second
    const opsPerSecond = totalOperations / duration;
    
    // Calculate error rate
    const errorRate = (totalErrors / (totalOperations + totalErrors)) * 100;
    
    // Calculate latency percentiles
    allLatencies.sort((a, b) => a - b);
    const p50 = allLatencies[Math.floor(allLatencies.length * 0.5)];
    const p95 = allLatencies[Math.floor(allLatencies.length * 0.95)];
    const p99 = allLatencies[Math.floor(allLatencies.length * 0.99)];
    
    // Print results
    console.log(`\n${colors.green}Canvas Performance Test Results:${colors.reset}`);
    console.log(`Total Operations: ${totalOperations}`);
    console.log(`Operations per Second: ${opsPerSecond.toFixed(2)}`);
    console.log(`Error Rate: ${errorRate.toFixed(2)}%`);
    console.log(`Average Latency: ${avgLatency.toFixed(2)} ms`);
    console.log(`P50 Latency: ${p50.toFixed(2)} ms`);
    console.log(`P95 Latency: ${p95.toFixed(2)} ms`);
    console.log(`P99 Latency: ${p99.toFixed(2)} ms`);
    
    // Check thresholds
    let success = true;
    if (opsPerSecond < 50) {
      console.log(`${colors.red}FAIL: Operations per second (${opsPerSecond.toFixed(2)}) below threshold (50)${colors.reset}`);
      success = false;
    }
    
    if (errorRate > 5) {
      console.log(`${colors.red}FAIL: Error rate (${errorRate.toFixed(2)}%) above threshold (5%)${colors.reset}`);
      success = false;
    }
    
    if (p95 > 200) {
      console.log(`${colors.red}FAIL: P95 latency (${p95.toFixed(2)} ms) above threshold (200 ms)${colors.reset}`);
      success = false;
    }
    
    if (success) {
      console.log(`${colors.green}SUCCESS: All canvas performance metrics within acceptable thresholds${colors.reset}`);
      process.exit(0);
    } else {
      console.log(`${colors.yellow}WARNING: Some canvas performance metrics failed to meet thresholds${colors.reset}`);
      process.exit(1);
    }
  }
  
  // Run the test when executed directly
  runTest();
}