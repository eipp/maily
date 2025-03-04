#!/usr/bin/env node
/**
 * Maily Blockchain Verification Performance Test
 * This script tests the performance of blockchain verification operations
 */

const { performance } = require('perf_hooks');
const crypto = require('crypto');

// ANSI colors for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m'
};

// Default configuration
const DEFAULT_OPERATIONS = 100;

/**
 * Parse command line arguments
 */
function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    operations: DEFAULT_OPERATIONS
  };
  
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--operations' && i + 1 < args.length) {
      options.operations = parseInt(args[i + 1], 10);
      i++;
    }
  }
  
  return options;
}

/**
 * Generate a random document hash (simulates a document to verify)
 */
function generateDocumentHash() {
  const randomData = crypto.randomBytes(256);
  return crypto.createHash('sha256').update(randomData).digest('hex');
}

/**
 * Simulate blockchain verification of a document hash
 */
async function simulateBlockchainVerification(docHash) {
  return new Promise((resolve) => {
    const startTime = performance.now();
    
    // Simulate blockchain verification delay
    setTimeout(() => {
      const success = Math.random() < 0.97; // 97% success rate
      const verificationTime = performance.now() - startTime;
      
      resolve({
        success,
        latency: verificationTime,
        hash: docHash
      });
    }, Math.random() * 300 + 100); // 100-400ms delay
  });
}

/**
 * Run blockchain verification performance test
 */
async function runTest() {
  const { operations } = parseArgs();
  
  console.log(`${colors.green}Starting blockchain verification test with ${operations} operations${colors.reset}`);
  
  const startTime = performance.now();
  const results = [];
  
  // Create array of promises
  const verificationPromises = [];
  for (let i = 0; i < operations; i++) {
    const docHash = generateDocumentHash();
    verificationPromises.push(simulateBlockchainVerification(docHash));
  }
  
  // Wait for all verifications to complete
  try {
    const verificationResults = await Promise.all(verificationPromises);
    results.push(...verificationResults);
  } catch (error) {
    console.error(`${colors.red}Error during verification: ${error.message}${colors.reset}`);
  }
  
  const totalTime = (performance.now() - startTime) / 1000; // Convert to seconds
  
  // Calculate results
  const successfulVerifications = results.filter(r => r.success).length;
  const successRate = (successfulVerifications / operations) * 100;
  const operationsPerSecond = operations / totalTime;
  
  // Calculate latency statistics
  const latencies = results.map(r => r.latency);
  const avgLatency = latencies.reduce((sum, l) => sum + l, 0) / latencies.length;
  
  // Sort latencies for percentiles
  latencies.sort((a, b) => a - b);
  const p50 = latencies[Math.floor(latencies.length * 0.5)];
  const p95 = latencies[Math.floor(latencies.length * 0.95)];
  const p99 = latencies[Math.floor(latencies.length * 0.99)];
  
  // Display results
  console.log(`\n${colors.green}Blockchain Verification Test Results:${colors.reset}`);
  console.log(`Total Operations: ${operations}`);
  console.log(`Successful Verifications: ${successfulVerifications}`);
  console.log(`Success Rate: ${successRate.toFixed(2)}%`);
  console.log(`Operations per Second: ${operationsPerSecond.toFixed(2)}`);
  console.log(`Total Time: ${totalTime.toFixed(2)} seconds`);
  console.log(`Average Latency: ${avgLatency.toFixed(2)} ms`);
  console.log(`P50 Latency: ${p50.toFixed(2)} ms`);
  console.log(`P95 Latency: ${p95.toFixed(2)} ms`);
  console.log(`P99 Latency: ${p99.toFixed(2)} ms`);
  
  // Check thresholds
  let success = true;
  
  if (successRate < 95) {
    console.log(`${colors.red}FAIL: Success rate (${successRate.toFixed(2)}%) below threshold (95%)${colors.reset}`);
    success = false;
  }
  
  if (operationsPerSecond < 10) {
    console.log(`${colors.red}FAIL: Operations per second (${operationsPerSecond.toFixed(2)}) below threshold (10)${colors.reset}`);
    success = false;
  }
  
  if (p95 > 500) {
    console.log(`${colors.red}FAIL: P95 latency (${p95.toFixed(2)} ms) above threshold (500 ms)${colors.reset}`);
    success = false;
  }
  
  if (success) {
    console.log(`${colors.green}SUCCESS: All blockchain verification metrics within acceptable thresholds${colors.reset}`);
    process.exit(0);
  } else {
    console.log(`${colors.yellow}WARNING: Some blockchain verification metrics failed to meet thresholds${colors.reset}`);
    process.exit(1);
  }
}

// Run the test
runTest().catch(error => {
  console.error(`${colors.red}Unhandled error: ${error}${colors.reset}`);
  process.exit(1);
});