#!/usr/bin/env node
/**
 * Maily Smoke Test Script
 * This script runs basic smoke tests against a deployed Maily environment
 */

const https = require('https');
const http = require('http');
const { URL } = require('url');

// ANSI colors for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  blue: '\x1b[34m'
};

// Environment URLs
const environments = {
  staging: {
    frontend: 'https://staging.maily.vercel.app',
    api: 'https://api-staging.maily.example.com',
    monitoring: 'https://monitor-staging.maily.example.com'
  },
  production: {
    frontend: 'https://maily.vercel.app',
    api: 'https://api.maily.example.com',
    monitoring: 'https://monitor.maily.example.com'
  }
};

/**
 * Make an HTTP request and return a promise
 */
function makeRequest(url) {
  return new Promise((resolve, reject) => {
    const parsedUrl = new URL(url);
    const options = {
      hostname: parsedUrl.hostname,
      port: parsedUrl.port || (parsedUrl.protocol === 'https:' ? 443 : 80),
      path: parsedUrl.pathname + parsedUrl.search,
      method: 'GET',
      timeout: 10000, // 10 second timeout
      headers: {
        'User-Agent': 'Maily-Smoke-Test/1.0'
      }
    };

    const req = (parsedUrl.protocol === 'https:' ? https : http).request(options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        resolve({
          status: res.statusCode,
          headers: res.headers,
          data: data
        });
      });
    });
    
    req.on('error', (error) => {
      reject(error);
    });
    
    req.on('timeout', () => {
      req.destroy();
      reject(new Error(`Request to ${url} timed out`));
    });
    
    req.end();
  });
}

/**
 * Check if a service is up by verifying its health endpoint returns 200 OK
 */
async function checkServiceHealth(name, url) {
  const healthUrl = `${url}/health`;
  console.log(`${colors.blue}Checking ${name} health at ${healthUrl}${colors.reset}`);
  
  try {
    const response = await makeRequest(healthUrl);
    
    if (response.status === 200) {
      console.log(`${colors.green}✓ ${name} is healthy (Status: ${response.status})${colors.reset}`);
      return true;
    } else {
      console.log(`${colors.red}✗ ${name} returned non-200 status: ${response.status}${colors.reset}`);
      return false;
    }
  } catch (error) {
    console.log(`${colors.red}✗ ${name} health check failed: ${error.message}${colors.reset}`);
    return false;
  }
}

/**
 * Check frontend for critical page loads
 */
async function checkFrontendPages(frontendUrl) {
  console.log(`${colors.blue}Checking frontend critical pages${colors.reset}`);
  
  const criticalPages = [
    { name: 'Home page', path: '/' },
    { name: 'Login page', path: '/login' },
    { name: 'Dashboard', path: '/dashboard' },
    { name: 'Canvas page', path: '/canvas' }
  ];
  
  let passedChecks = 0;
  
  for (const page of criticalPages) {
    const pageUrl = `${frontendUrl}${page.path}`;
    try {
      const response = await makeRequest(pageUrl);
      
      // For this simple check, we consider any 200-299 response as success
      // In a real test, we might check for specific content
      if (response.status >= 200 && response.status < 300) {
        console.log(`${colors.green}✓ ${page.name} loaded successfully (Status: ${response.status})${colors.reset}`);
        passedChecks++;
      } else {
        console.log(`${colors.red}✗ ${page.name} returned error status: ${response.status}${colors.reset}`);
      }
    } catch (error) {
      console.log(`${colors.red}✗ ${page.name} failed to load: ${error.message}${colors.reset}`);
    }
  }
  
  return passedChecks === criticalPages.length;
}

/**
 * Check API endpoints
 */
async function checkApiEndpoints(apiUrl) {
  console.log(`${colors.blue}Checking API critical endpoints${colors.reset}`);
  
  const endpoints = [
    { name: 'Version endpoint', path: '/api/version' },
    { name: 'Status endpoint', path: '/api/status' }
  ];
  
  let passedChecks = 0;
  
  for (const endpoint of endpoints) {
    const endpointUrl = `${apiUrl}${endpoint.path}`;
    try {
      const response = await makeRequest(endpointUrl);
      
      if (response.status >= 200 && response.status < 300) {
        console.log(`${colors.green}✓ ${endpoint.name} available (Status: ${response.status})${colors.reset}`);
        passedChecks++;
      } else {
        console.log(`${colors.red}✗ ${endpoint.name} returned error status: ${response.status}${colors.reset}`);
      }
    } catch (error) {
      console.log(`${colors.red}✗ ${endpoint.name} failed: ${error.message}${colors.reset}`);
    }
  }
  
  return passedChecks === endpoints.length;
}

/**
 * Run the smoke tests
 */
async function runSmokeTests(environment) {
  console.log(`${colors.green}Running Maily smoke tests for ${environment} environment${colors.reset}`);
  
  const urls = environments[environment];
  if (!urls) {
    console.log(`${colors.red}Unknown environment: ${environment}${colors.reset}`);
    console.log(`Available environments: ${Object.keys(environments).join(', ')}`);
    process.exit(1);
  }
  
  console.log(`Environment URLs:
Frontend: ${urls.frontend}
API: ${urls.api}
Monitoring: ${urls.monitoring}
`);
  
  // Track all test results
  const results = {
    frontendHealth: false,
    apiHealth: false,
    monitoringHealth: false,
    frontendPages: false,
    apiEndpoints: false
  };
  
  // Service health checks
  results.frontendHealth = await checkServiceHealth('Frontend', urls.frontend);
  results.apiHealth = await checkServiceHealth('API', urls.api);
  results.monitoringHealth = await checkServiceHealth('Monitoring', urls.monitoring);
  
  // Frontend page checks
  results.frontendPages = await checkFrontendPages(urls.frontend);
  
  // API endpoint checks
  results.apiEndpoints = await checkApiEndpoints(urls.api);
  
  // Summary
  console.log(`\n${colors.green}Smoke Test Results:${colors.reset}`);
  
  const allPassed = Object.values(results).every(result => result === true);
  const passedCount = Object.values(results).filter(result => result === true).length;
  const totalTests = Object.values(results).length;
  
  console.log(`Tests passed: ${passedCount}/${totalTests}`);
  
  for (const [test, passed] of Object.entries(results)) {
    const status = passed ? `${colors.green}PASS${colors.reset}` : `${colors.red}FAIL${colors.reset}`;
    console.log(`${test}: ${status}`);
  }
  
  if (allPassed) {
    console.log(`\n${colors.green}✓ All smoke tests passed!${colors.reset}`);
    return true;
  } else {
    console.log(`\n${colors.red}✗ Some smoke tests failed.${colors.reset}`);
    return false;
  }
}

// Main script execution
async function main() {
  const args = process.argv.slice(2);
  const environment = args[0] || 'staging';
  
  try {
    const passed = await runSmokeTests(environment);
    process.exit(passed ? 0 : 1);
  } catch (error) {
    console.error(`${colors.red}Error running smoke tests: ${error.message}${colors.reset}`);
    process.exit(1);
  }
}

// Run the script
main();