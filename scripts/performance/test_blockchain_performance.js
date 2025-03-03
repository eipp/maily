/**
 * Blockchain Verification Performance Test
 * 
 * This script tests the performance of our blockchain verification infrastructure
 * by simulating concurrent verification requests.
 */

const axios = require('axios');
const { performance } = require('perf_hooks');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');

// Parse command line arguments
const argv = yargs(hideBin(process.argv))
  .option('operations', {
    alias: 'o',
    description: 'Number of verification operations to perform',
    type: 'number',
    default: 100
  })
  .option('concurrency', {
    alias: 'c',
    description: 'Maximum number of concurrent operations',
    type: 'number',
    default: 10
  })
  .option('api', {
    description: 'API base URL',
    type: 'string',
    default: process.env.API_URL || 'http://localhost:3000/api'
  })
  .help()
  .alias('help', 'h')
  .argv;

// Sample certificates to verify
const sampleCertificates = [
  { id: 'cert-123456789abcdef', content_hash: 'a1b2c3d4e5f6g7h8i9j0' },
  { id: 'cert-abcdef123456789', content_hash: '1a2b3c4d5e6f7g8h9i0j' },
  { id: 'cert-987654321fedcba', content_hash: 'j0i9h8g7f6e5d4c3b2a1' },
  { id: 'cert-fedcba987654321', content_hash: '0j9i8h7g6f5e4d3c2b1a' },
  { id: 'cert-abcdef987654321', content_hash: 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6' },
];

// Helper to generate random certificates for testing
function generateTestCertificates(count) {
  const certificates = [];
  for (let i = 0; i < count; i++) {
    const randomId = `cert-${Math.random().toString(36).substring(2, 15)}`;
    const randomHash = Array.from({length: 32}, () => Math.floor(Math.random() * 16).toString(16)).join('');
    certificates.push({ id: randomId, content_hash: randomHash });
  }
  return certificates;
}

// Helper to chunk array into batches
function chunk(array, size) {
  const chunked = [];
  for (let i = 0; i < array.length; i += size) {
    chunked.push(array.slice(i, i + size));
  }
  return chunked;
}

// Verify a single certificate
async function verifyBlockchainCertificate(certificate) {
  const startTime = performance.now();
  try {
    const response = await axios.post(`${argv.api}/blockchain/verify`, {
      certificate_id: certificate.id,
      content_hash: certificate.content_hash
    });
    
    const duration = performance.now() - startTime;
    return {
      certificate_id: certificate.id,
      success: response.data.verified === true,
      duration,
      error: null
    };
  } catch (error) {
    const duration = performance.now() - startTime;
    return {
      certificate_id: certificate.id,
      success: false,
      duration,
      error: error.message
    };
  }
}

// Process a batch of operations
async function processBatch(batch) {
  return Promise.all(batch.map(certificate => verifyBlockchainCertificate(certificate)));
}

// Main test function
async function runTest() {
  console.log(`Starting blockchain verification performance test...`);
  console.log(`Operations: ${argv.operations}, Concurrency: ${argv.concurrency}, API: ${argv.api}\n`);
  
  const testStart = performance.now();
  
  // Generate test certificates with some duplicates to test caching
  const testCertificates = [
    ...sampleCertificates,
    ...generateTestCertificates(Math.max(0, argv.operations - sampleCertificates.length))
  ];
  
  // Add some duplicates to test caching
  for (let i = 0; i < Math.min(10, argv.operations / 10); i++) {
    const randomIndex = Math.floor(Math.random() * testCertificates.length);
    testCertificates.push(testCertificates[randomIndex]);
  }
  
  // Shuffle to distribute duplicates
  testCertificates.sort(() => Math.random() - 0.5);
  
  // Limit to requested operation count
  const certificates = testCertificates.slice(0, argv.operations);
  
  // Split into batches based on concurrency
  const batches = chunk(certificates, argv.concurrency);
  
  console.log(`Processing ${certificates.length} certificates in ${batches.length} batches...\n`);
  
  const results = [];
  let batchIndex = 0;
  
  for (const batch of batches) {
    console.log(`Processing batch ${++batchIndex} of ${batches.length}...`);
    const batchResults = await processBatch(batch);
    results.push(...batchResults);
    
    // Log progress
    const successCount = results.filter(r => r.success).length;
    const failCount = results.filter(r => !r.success).length;
    console.log(`Processed ${results.length}/${certificates.length} verifications (${successCount} succeeded, ${failCount} failed)`);
  }
  
  const testDuration = (performance.now() - testStart) / 1000;
  
  // Calculate statistics
  const durations = results.map(r => r.duration);
  const avgDuration = durations.reduce((sum, d) => sum + d, 0) / durations.length;
  const minDuration = Math.min(...durations);
  const maxDuration = Math.max(...durations);
  const successRate = (results.filter(r => r.success).length / results.length) * 100;
  const opsPerSecond = results.length / testDuration;
  
  // Print results
  console.log('\n========================================');
  console.log('Blockchain Verification Performance Test Results');
  console.log('========================================');
  console.log(`Total operations:    ${results.length}`);
  console.log(`Total time:          ${testDuration.toFixed(2)} seconds`);
  console.log(`Operations/second:   ${opsPerSecond.toFixed(2)}`);
  console.log(`Success rate:        ${successRate.toFixed(2)}%`);
  console.log(`Average duration:    ${avgDuration.toFixed(2)} ms`);
  console.log(`Minimum duration:    ${minDuration.toFixed(2)} ms`);
  console.log(`Maximum duration:    ${maxDuration.toFixed(2)} ms`);
  console.log('========================================');
  
  // Check if performance is acceptable
  const isPerformanceAcceptable = 
    successRate >= 95 && 
    opsPerSecond >= 5 && 
    avgDuration <= 500;
  
  if (isPerformanceAcceptable) {
    console.log('\n✅ Performance test PASSED - Verification throughput meets requirements');
    process.exit(0);
  } else {
    console.log('\n❌ Performance test FAILED - Verification throughput does not meet requirements');
    console.log('Target criteria:');
    console.log('- Success rate: >= 95%');
    console.log('- Operations per second: >= 5');
    console.log('- Average duration: <= 500ms');
    process.exit(1);
  }
}

// Run the test
runTest().catch(error => {
  console.error(`Test failed with error: ${error.message}`);
  process.exit(1);
});