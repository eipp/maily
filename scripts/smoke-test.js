#!/usr/bin/env node
/**
 * Smoke Test Script for Maily
 *
 * This script runs a series of tests against the deployed Maily platform
 * to verify that all components are working as expected.
 *
 * Usage:
 *   node smoke-test.js [environment]
 */

const https = require('https');
const fs = require('fs');
const { execSync } = require('child_process');
const { promisify } = require('util');
const path = require('path');

// Configuration
const environment = process.argv[2] || 'production';
const config = {
  production: {
    frontendUrl: 'https://justmaily.com',
    apiUrl: 'https://api.justmaily.com',
    timeout: 30000
  },
  staging: {
    frontendUrl: 'https://staging.justmaily.com',
    apiUrl: 'https://api-staging.justmaily.com',
    timeout: 30000
  },
  development: {
    frontendUrl: 'http://localhost:3000',
    apiUrl: 'http://localhost:3001',
    timeout: 10000
  }
};

// Validate environment
if (!config[environment]) {
  console.error(`Invalid environment: ${environment}`);
  console.error('Valid environments: production, staging, development');
  process.exit(1);
}

// Output styling
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

// Current configuration
const { frontendUrl, apiUrl, timeout } = config[environment];

// Create report directory
const reportDir = path.join(__dirname, '../deployment_logs');
if (!fs.existsSync(reportDir)) {
  fs.mkdirSync(reportDir, { recursive: true });
}

// Initialize report data
const report = {
  timestamp: new Date().toISOString(),
  environment,
  tests: [],
  summary: {
    total: 0,
    passed: 0,
    failed: 0,
    skipped: 0
  }
};

// Helper functions
async function httpRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const req = https.request(url, options, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          data
        });
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.on('timeout', () => {
      req.destroy();
      reject(new Error(`Request timed out: ${url}`));
    });

    req.setTimeout(timeout);

    if (options.body) {
      req.write(options.body);
    }

    req.end();
  });
}

function addTestResult(name, category, result, error = null, details = null) {
  const testResult = {
    name,
    category,
    result,
    timestamp: new Date().toISOString()
  };

  if (error) {
    testResult.error = typeof error === 'object' ? error.message : error;
  }

  if (details) {
    testResult.details = details;
  }

  report.tests.push(testResult);
  report.summary.total++;

  if (result === 'passed') {
    report.summary.passed++;
    console.log(`${colors.green}✓ PASS${colors.reset} [${category}] ${name}`);
  } else if (result === 'failed') {
    report.summary.failed++;
    console.log(`${colors.red}✗ FAIL${colors.reset} [${category}] ${name}: ${error}`);
  } else {
    report.summary.skipped++;
    console.log(`${colors.yellow}○ SKIP${colors.reset} [${category}] ${name}`);
  }
}

// Main test function
async function runTests() {
  console.log(`\n${colors.cyan}=== Maily Smoke Tests (${environment}) ===${colors.reset}`);
  console.log(`Frontend URL: ${frontendUrl}`);
  console.log(`API URL: ${apiUrl}`);
  console.log(`Timestamp: ${new Date().toISOString()}`);
  console.log(`\n${colors.cyan}=== Running Tests ===${colors.reset}\n`);

  try {
    // ==== API Health Check ====
    try {
      const healthResponse = await httpRequest(`${apiUrl}/health`);
      if (healthResponse.statusCode === 200) {
        addTestResult('API Health Endpoint', 'API', 'passed', null, {
          statusCode: healthResponse.statusCode
        });
      } else {
        addTestResult('API Health Endpoint', 'API', 'failed',
          `Unexpected status code: ${healthResponse.statusCode}`);
      }
    } catch (error) {
      addTestResult('API Health Endpoint', 'API', 'failed', error);
    }

    // ==== Frontend Check ====
    try {
      const frontendResponse = await httpRequest(frontendUrl);
      if (frontendResponse.statusCode === 200) {
        addTestResult('Frontend Loads', 'Frontend', 'passed', null, {
          statusCode: frontendResponse.statusCode
        });
      } else {
        addTestResult('Frontend Loads', 'Frontend', 'failed',
          `Unexpected status code: ${frontendResponse.statusCode}`);
      }
    } catch (error) {
      addTestResult('Frontend Loads', 'Frontend', 'failed', error);
    }

    // ==== API Authentication ====
    try {
      const authResponse = await httpRequest(`${apiUrl}/auth/status`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (authResponse.statusCode === 200 || authResponse.statusCode === 401) {
        addTestResult('Authentication Endpoint', 'API', 'passed', null, {
          statusCode: authResponse.statusCode
        });
      } else {
        addTestResult('Authentication Endpoint', 'API', 'failed',
          `Unexpected status code: ${authResponse.statusCode}`);
      }
    } catch (error) {
      addTestResult('Authentication Endpoint', 'API', 'failed', error);
    }

    // ==== AI Service Check ====
    try {
      const aiResponse = await httpRequest(`${apiUrl}/ai/status`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (aiResponse.statusCode === 200) {
        addTestResult('AI Service Status', 'AI Services', 'passed', null, {
          statusCode: aiResponse.statusCode
        });
      } else {
        addTestResult('AI Service Status', 'AI Services', 'failed',
          `Unexpected status code: ${aiResponse.statusCode}`);
      }
    } catch (error) {
      addTestResult('AI Service Status', 'AI Services', 'failed', error);
    }

    // ==== Database Connection Check ====
    try {
      const dbResponse = await httpRequest(`${apiUrl}/db/status`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (dbResponse.statusCode === 200) {
        addTestResult('Database Connection', 'Database', 'passed', null, {
          statusCode: dbResponse.statusCode
        });
      } else {
        addTestResult('Database Connection', 'Database', 'failed',
          `Unexpected status code: ${dbResponse.statusCode}`);
      }
    } catch (error) {
      addTestResult('Database Connection', 'Database', 'failed', error);
    }

    // ==== Redis Connection Check ====
    try {
      const redisResponse = await httpRequest(`${apiUrl}/cache/status`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (redisResponse.statusCode === 200) {
        addTestResult('Redis Connection', 'Cache', 'passed', null, {
          statusCode: redisResponse.statusCode
        });
      } else {
        addTestResult('Redis Connection', 'Cache', 'failed',
          `Unexpected status code: ${redisResponse.statusCode}`);
      }
    } catch (error) {
      addTestResult('Redis Connection', 'Cache', 'failed', error);
    }

    // ==== Blockchain Status Check ====
    try {
      const blockchainResponse = await httpRequest(`${apiUrl}/blockchain/status`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (blockchainResponse.statusCode === 200) {
        addTestResult('Blockchain Status', 'Blockchain', 'passed', null, {
          statusCode: blockchainResponse.statusCode
        });
      } else {
        addTestResult('Blockchain Status', 'Blockchain', 'failed',
          `Unexpected status code: ${blockchainResponse.statusCode}`);
      }
    } catch (error) {
      addTestResult('Blockchain Status', 'Blockchain', 'failed', error);
    }

  } catch (error) {
    console.error(`${colors.red}Error running tests:${colors.reset}`, error);
  }

  // Generate final report
  const { total, passed, failed, skipped } = report.summary;
  const success = failed === 0;

  console.log(`\n${colors.cyan}=== Test Summary ===${colors.reset}`);
  console.log(`Total tests: ${total}`);
  console.log(`${colors.green}Passed: ${passed}${colors.reset}`);
  console.log(`${colors.red}Failed: ${failed}${colors.reset}`);
  console.log(`${colors.yellow}Skipped: ${skipped}${colors.reset}`);

  const reportPath = path.join(reportDir, `smoke_test_${environment}_${Date.now()}.json`);
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

  console.log(`\nReport saved to: ${reportPath}`);

  // Return exit code based on tests
  process.exit(success ? 0 : 1);
}

// Run the tests
runTests().catch(error => {
  console.error('Test execution failed:', error);
  process.exit(1);
});
