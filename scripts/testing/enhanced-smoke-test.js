#!/usr/bin/env node
/**
 * Maily Enhanced Smoke Test Script
 * This script runs comprehensive smoke tests against a deployed Maily environment
 * It includes API endpoint testing, frontend checks, and service health verification
 */

const https = require('https');
const http = require('http');
const { URL } = require('url');
const fs = require('fs');
const path = require('path');

// ANSI colors for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  magenta: '\x1b[35m'
};

// Environment URLs
const environments = {
  staging: {
    frontend: 'https://staging.maily.vercel.app',
    api: 'https://api-staging.maily.example.com',
    ai: 'https://ai-mesh-staging.justmaily.com',
    monitoring: 'https://monitor-staging.maily.example.com',
    grafana: 'https://grafana-staging.justmaily.com'
  },
  production: {
    frontend: 'https://maily.vercel.app',
    api: 'https://api.maily.example.com',
    ai: 'https://ai-mesh.justmaily.com',
    monitoring: 'https://monitor.maily.example.com',
    grafana: 'https://grafana.justmaily.com'
  }
};

// Default test timeouts
const DEFAULT_TIMEOUT = 15000; // 15 seconds

/**
 * Make an HTTP request and return a promise
 */
function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const parsedUrl = new URL(url);
    const requestOptions = {
      hostname: parsedUrl.hostname,
      port: parsedUrl.port || (parsedUrl.protocol === 'https:' ? 443 : 80),
      path: parsedUrl.pathname + parsedUrl.search,
      method: options.method || 'GET',
      timeout: options.timeout || DEFAULT_TIMEOUT,
      headers: {
        'User-Agent': 'Maily-Enhanced-Smoke-Test/1.0',
        ...(options.headers || {})
      }
    };

    const req = (parsedUrl.protocol === 'https:' ? https : http).request(requestOptions, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        let parsedData = data;
        // Try to parse JSON if content-type is application/json
        if (res.headers['content-type'] && res.headers['content-type'].includes('application/json')) {
          try {
            parsedData = JSON.parse(data);
          } catch (e) {
            // Keep as string if parsing fails
          }
        }
        
        resolve({
          status: res.statusCode,
          headers: res.headers,
          data: parsedData
        });
      });
    });
    
    req.on('error', (error) => {
      reject(error);
    });
    
    req.on('timeout', () => {
      req.destroy();
      reject(new Error(`Request to ${url} timed out after ${requestOptions.timeout}ms`));
    });
    
    if (options.body) {
      req.write(typeof options.body === 'string' ? options.body : JSON.stringify(options.body));
    }
    
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
      return { success: true, data: response.data };
    } else {
      console.log(`${colors.red}✗ ${name} returned non-200 status: ${response.status}${colors.reset}`);
      return { success: false, error: `Non-200 status: ${response.status}` };
    }
  } catch (error) {
    console.log(`${colors.red}✗ ${name} health check failed: ${error.message}${colors.reset}`);
    return { success: false, error: error.message };
  }
}

/**
 * Check frontend for critical page loads and content
 */
async function checkFrontendPages(frontendUrl) {
  console.log(`${colors.blue}Checking frontend critical pages${colors.reset}`);
  
  const criticalPages = [
    { 
      name: 'Home page', 
      path: '/', 
      expectedContent: ['login', 'sign up', 'email']
    },
    { 
      name: 'Login page', 
      path: '/login', 
      expectedContent: ['email', 'password', 'forgot'] 
    },
    { 
      name: 'Dashboard', 
      path: '/dashboard', 
      expectedContent: ['dashboard', 'campaigns', 'analytics'] 
    },
    { 
      name: 'Canvas page', 
      path: '/canvas', 
      expectedContent: ['canvas', 'design', 'element'] 
    },
    { 
      name: 'Email Templates', 
      path: '/templates', 
      expectedContent: ['template', 'customize', 'design'] 
    }
  ];
  
  const results = [];
  
  for (const page of criticalPages) {
    const pageUrl = `${frontendUrl}${page.path}`;
    try {
      console.log(`${colors.cyan}Testing ${page.name} at ${pageUrl}${colors.reset}`);
      const response = await makeRequest(pageUrl);
      
      // Check for successful status code
      const hasSuccessStatus = response.status >= 200 && response.status < 300;
      
      // Check for expected content
      let hasExpectedContent = true;
      if (page.expectedContent && page.expectedContent.length > 0) {
        const lowercaseData = typeof response.data === 'string' ? response.data.toLowerCase() : JSON.stringify(response.data).toLowerCase();
        
        for (const expectedText of page.expectedContent) {
          if (!lowercaseData.includes(expectedText.toLowerCase())) {
            hasExpectedContent = false;
            console.log(`${colors.yellow}! Expected content '${expectedText}' not found on ${page.name}${colors.reset}`);
          }
        }
      }
      
      if (hasSuccessStatus && hasExpectedContent) {
        console.log(`${colors.green}✓ ${page.name} loaded successfully (Status: ${response.status})${colors.reset}`);
        results.push({ page: page.name, success: true });
      } else if (hasSuccessStatus) {
        console.log(`${colors.yellow}! ${page.name} loaded but missing expected content (Status: ${response.status})${colors.reset}`);
        results.push({ page: page.name, success: false, error: 'Missing expected content' });
      } else {
        console.log(`${colors.red}✗ ${page.name} returned error status: ${response.status}${colors.reset}`);
        results.push({ page: page.name, success: false, error: `Error status: ${response.status}` });
      }
    } catch (error) {
      console.log(`${colors.red}✗ ${page.name} failed to load: ${error.message}${colors.reset}`);
      results.push({ page: page.name, success: false, error: error.message });
    }
  }
  
  const successCount = results.filter(r => r.success).length;
  console.log(`${colors.blue}Frontend pages: ${successCount}/${criticalPages.length} passed${colors.reset}`);
  
  return {
    success: successCount === criticalPages.length,
    results
  };
}

/**
 * Test API endpoints
 */
async function testApiEndpoints(apiUrl) {
  console.log(`${colors.blue}Testing API critical endpoints${colors.reset}`);
  
  const endpoints = [
    { 
      name: 'Version endpoint', 
      path: '/api/version', 
      method: 'GET', 
      expectedStatus: 200,
      validate: (data) => data && data.version 
    },
    { 
      name: 'Status endpoint', 
      path: '/api/status', 
      method: 'GET', 
      expectedStatus: 200,
      validate: (data) => data && data.status === 'ok' 
    },
    { 
      name: 'User creation validation', 
      path: '/api/users/validate', 
      method: 'POST', 
      body: { email: 'test@example.com' },
      headers: { 'Content-Type': 'application/json' },
      expectedStatus: 200,
      validate: (data) => data && data.valid === false 
    },
    { 
      name: 'Public API docs', 
      path: '/api/docs', 
      method: 'GET', 
      expectedStatus: 200,
      validate: (data) => typeof data === 'string' && data.includes('API Documentation') 
    }
  ];
  
  const results = [];
  
  for (const endpoint of endpoints) {
    const endpointUrl = `${apiUrl}${endpoint.path}`;
    try {
      console.log(`${colors.cyan}Testing ${endpoint.name} (${endpoint.method} ${endpointUrl})${colors.reset}`);
      
      const response = await makeRequest(endpointUrl, {
        method: endpoint.method,
        headers: endpoint.headers,
        body: endpoint.body
      });
      
      // Check status
      const hasCorrectStatus = response.status === endpoint.expectedStatus;
      
      // Check validation function if provided
      let isValidData = true;
      if (endpoint.validate) {
        isValidData = endpoint.validate(response.data);
      }
      
      if (hasCorrectStatus && isValidData) {
        console.log(`${colors.green}✓ ${endpoint.name} passed (Status: ${response.status})${colors.reset}`);
        results.push({ endpoint: endpoint.name, success: true });
      } else if (hasCorrectStatus) {
        console.log(`${colors.yellow}! ${endpoint.name} returned correct status but invalid data (Status: ${response.status})${colors.reset}`);
        results.push({ endpoint: endpoint.name, success: false, error: 'Invalid response data' });
      } else {
        console.log(`${colors.red}✗ ${endpoint.name} returned unexpected status: ${response.status} (expected: ${endpoint.expectedStatus})${colors.reset}`);
        results.push({ endpoint: endpoint.name, success: false, error: `Wrong status: ${response.status}` });
      }
    } catch (error) {
      console.log(`${colors.red}✗ ${endpoint.name} request failed: ${error.message}${colors.reset}`);
      results.push({ endpoint: endpoint.name, success: false, error: error.message });
    }
  }
  
  const successCount = results.filter(r => r.success).length;
  console.log(`${colors.blue}API endpoints: ${successCount}/${endpoints.length} passed${colors.reset}`);
  
  return {
    success: successCount === endpoints.length,
    results
  };
}

/**
 * Test AI service functionality
 */
async function testAiService(aiUrl) {
  console.log(`${colors.blue}Testing AI service functionality${colors.reset}`);
  
  const tests = [
    {
      name: 'AI Service Health',
      path: '/health',
      method: 'GET',
      expectedStatus: 200,
      validate: (data) => data && data.status === 'ok'
    },
    {
      name: 'AI Models Endpoint',
      path: '/api/models',
      method: 'GET',
      expectedStatus: 200,
      validate: (data) => Array.isArray(data) && data.length > 0
    },
    {
      name: 'AI Readiness Check',
      path: '/ready',
      method: 'GET',
      expectedStatus: 200,
      validate: (data) => data && data.ready === true
    }
  ];
  
  const results = [];
  
  for (const test of tests) {
    const testUrl = `${aiUrl}${test.path}`;
    try {
      console.log(`${colors.cyan}Testing ${test.name} (${test.method} ${testUrl})${colors.reset}`);
      
      const response = await makeRequest(testUrl, {
        method: test.method,
        headers: test.headers,
        body: test.body
      });
      
      // Check status
      const hasCorrectStatus = response.status === test.expectedStatus;
      
      // Check validation function if provided
      let isValidData = true;
      if (test.validate) {
        isValidData = test.validate(response.data);
      }
      
      if (hasCorrectStatus && isValidData) {
        console.log(`${colors.green}✓ ${test.name} passed (Status: ${response.status})${colors.reset}`);
        results.push({ test: test.name, success: true });
      } else if (hasCorrectStatus) {
        console.log(`${colors.yellow}! ${test.name} returned correct status but invalid data (Status: ${response.status})${colors.reset}`);
        results.push({ test: test.name, success: false, error: 'Invalid response data' });
      } else {
        console.log(`${colors.red}✗ ${test.name} returned unexpected status: ${response.status} (expected: ${test.expectedStatus})${colors.reset}`);
        results.push({ test: test.name, success: false, error: `Wrong status: ${response.status}` });
      }
    } catch (error) {
      console.log(`${colors.red}✗ ${test.name} request failed: ${error.message}${colors.reset}`);
      results.push({ test: test.name, success: false, error: error.message });
    }
  }
  
  const successCount = results.filter(r => r.success).length;
  console.log(`${colors.blue}AI service tests: ${successCount}/${tests.length} passed${colors.reset}`);
  
  return {
    success: successCount === tests.length,
    results
  };
}

/**
 * Test monitoring services
 */
async function testMonitoring(monitoringUrl, grafanaUrl) {
  console.log(`${colors.blue}Testing monitoring services${colors.reset}`);
  
  const tests = [
    {
      name: 'Prometheus Health',
      url: `${monitoringUrl}/-/healthy`,
      method: 'GET',
      expectedStatus: 200
    },
    {
      name: 'Grafana Login Page',
      url: `${grafanaUrl}/login`,
      method: 'GET',
      expectedStatus: 200,
      validate: (data) => typeof data === 'string' && data.includes('login')
    }
  ];
  
  const results = [];
  
  for (const test of tests) {
    try {
      console.log(`${colors.cyan}Testing ${test.name} (${test.method} ${test.url})${colors.reset}`);
      
      const response = await makeRequest(test.url, {
        method: test.method
      });
      
      // Check status
      const hasCorrectStatus = response.status === test.expectedStatus;
      
      // Check validation function if provided
      let isValidData = true;
      if (test.validate) {
        isValidData = test.validate(response.data);
      }
      
      if (hasCorrectStatus && isValidData) {
        console.log(`${colors.green}✓ ${test.name} passed (Status: ${response.status})${colors.reset}`);
        results.push({ test: test.name, success: true });
      } else if (hasCorrectStatus) {
        console.log(`${colors.yellow}! ${test.name} returned correct status but invalid data (Status: ${response.status})${colors.reset}`);
        results.push({ test: test.name, success: false, error: 'Invalid response data' });
      } else {
        console.log(`${colors.red}✗ ${test.name} returned unexpected status: ${response.status} (expected: ${test.expectedStatus})${colors.reset}`);
        results.push({ test: test.name, success: false, error: `Wrong status: ${response.status}` });
      }
    } catch (error) {
      console.log(`${colors.red}✗ ${test.name} request failed: ${error.message}${colors.reset}`);
      results.push({ test: test.name, success: false, error: error.message });
    }
  }
  
  const successCount = results.filter(r => r.success).length;
  console.log(`${colors.blue}Monitoring tests: ${successCount}/${tests.length} passed${colors.reset}`);
  
  return {
    success: successCount === tests.length,
    results
  };
}

/**
 * Run the enhanced smoke tests
 */
async function runEnhancedSmokeTests(environment, options = {}) {
  console.log(`${colors.green}Running Enhanced Maily Smoke Tests for ${environment} environment${colors.reset}`);
  console.log(`Timestamp: ${new Date().toISOString()}`);
  
  const urls = environments[environment];
  if (!urls) {
    console.log(`${colors.red}Unknown environment: ${environment}${colors.reset}`);
    console.log(`Available environments: ${Object.keys(environments).join(', ')}`);
    process.exit(1);
  }
  
  console.log(`${colors.blue}Environment URLs:
Frontend: ${urls.frontend}
API: ${urls.api}
AI Service: ${urls.ai}
Monitoring: ${urls.monitoring}
Grafana: ${urls.grafana}
${colors.reset}`);
  
  // Track all test results
  const results = {
    serviceHealth: {},
    frontendTests: null,
    apiTests: null,
    aiTests: null,
    monitoringTests: null
  };
  
  // Service health checks
  console.log(`\n${colors.magenta}=== Service Health Checks ===${colors.reset}`);
  if (!options.skipFrontend) results.serviceHealth.frontend = await checkServiceHealth('Frontend', urls.frontend);
  if (!options.skipApi) results.serviceHealth.api = await checkServiceHealth('API', urls.api);
  if (!options.skipAi) results.serviceHealth.ai = await checkServiceHealth('AI Service', urls.ai);
  if (!options.skipMonitoring) results.serviceHealth.monitoring = await checkServiceHealth('Monitoring', urls.monitoring);
  
  // Detailed tests
  console.log(`\n${colors.magenta}=== Detailed Tests ===${colors.reset}`);
  
  // Frontend page tests
  if (!options.skipFrontend) {
    console.log(`\n${colors.magenta}Frontend Tests${colors.reset}`);
    results.frontendTests = await checkFrontendPages(urls.frontend);
  }
  
  // API tests
  if (!options.skipApi) {
    console.log(`\n${colors.magenta}API Tests${colors.reset}`);
    results.apiTests = await testApiEndpoints(urls.api);
  }
  
  // AI Service tests
  if (!options.skipAi) {
    console.log(`\n${colors.magenta}AI Service Tests${colors.reset}`);
    results.aiTests = await testAiService(urls.ai);
  }
  
  // Monitoring tests
  if (!options.skipMonitoring) {
    console.log(`\n${colors.magenta}Monitoring Tests${colors.reset}`);
    results.monitoringTests = await testMonitoring(urls.monitoring, urls.grafana);
  }
  
  // Generate test summary
  console.log(`\n${colors.magenta}=== Test Summary ===${colors.reset}`);
  
  let allPassed = true;
  let totalTests = 0;
  let passedTests = 0;
  
  // Check service health results
  const healthResults = Object.entries(results.serviceHealth);
  totalTests += healthResults.length;
  const healthPassed = healthResults.filter(([_, result]) => result.success).length;
  passedTests += healthPassed;
  
  console.log(`Service Health: ${healthPassed}/${healthResults.length} passed`);
  if (healthPassed !== healthResults.length) allPassed = false;
  
  // Check frontend test results
  if (results.frontendTests) {
    const frontendResults = results.frontendTests.results;
    totalTests += frontendResults.length;
    const frontendPassed = frontendResults.filter(result => result.success).length;
    passedTests += frontendPassed;
    
    console.log(`Frontend Tests: ${frontendPassed}/${frontendResults.length} passed`);
    if (frontendPassed !== frontendResults.length) allPassed = false;
  }
  
  // Check API test results
  if (results.apiTests) {
    const apiResults = results.apiTests.results;
    totalTests += apiResults.length;
    const apiPassed = apiResults.filter(result => result.success).length;
    passedTests += apiPassed;
    
    console.log(`API Tests: ${apiPassed}/${apiResults.length} passed`);
    if (apiPassed !== apiResults.length) allPassed = false;
  }
  
  // Check AI service test results
  if (results.aiTests) {
    const aiResults = results.aiTests.results;
    totalTests += aiResults.length;
    const aiPassed = aiResults.filter(result => result.success).length;
    passedTests += aiPassed;
    
    console.log(`AI Service Tests: ${aiPassed}/${aiResults.length} passed`);
    if (aiPassed !== aiResults.length) allPassed = false;
  }
  
  // Check monitoring test results
  if (results.monitoringTests) {
    const monitoringResults = results.monitoringTests.results;
    totalTests += monitoringResults.length;
    const monitoringPassed = monitoringResults.filter(result => result.success).length;
    passedTests += monitoringPassed;
    
    console.log(`Monitoring Tests: ${monitoringPassed}/${monitoringResults.length} passed`);
    if (monitoringPassed !== monitoringResults.length) allPassed = false;
  }
  
  // Overall summary
  console.log(`\n${colors.magenta}=== Overall Results ===${colors.reset}`);
  console.log(`Tests Passed: ${passedTests}/${totalTests} (${Math.round(passedTests/totalTests*100)}%)`);
  
  if (allPassed) {
    console.log(`\n${colors.green}✓ All smoke tests passed!${colors.reset}`);
  } else {
    console.log(`\n${colors.yellow}! Some smoke tests failed.${colors.reset}`);
  }
  
  // Generate output report if requested
  if (options.outputFile) {
    const reportData = {
      timestamp: new Date().toISOString(),
      environment,
      summary: {
        totalTests,
        passedTests,
        allPassed
      },
      results
    };
    
    try {
      fs.writeFileSync(options.outputFile, JSON.stringify(reportData, null, 2));
      console.log(`\n${colors.green}Report saved to ${options.outputFile}${colors.reset}`);
    } catch (error) {
      console.log(`\n${colors.red}Failed to save report: ${error.message}${colors.reset}`);
    }
  }
  
  return {
    success: allPassed,
    totalTests,
    passedTests,
    results
  };
}

/**
 * Parse command line arguments
 */
function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    environment: 'staging',
    outputFile: null,
    skipFrontend: false,
    skipApi: false,
    skipAi: false,
    skipMonitoring: false
  };
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    
    if (arg === '--environment' || arg === '-e') {
      options.environment = args[++i] || 'staging';
    } else if (arg === '--output' || arg === '-o') {
      options.outputFile = args[++i];
    } else if (arg === '--skip-frontend') {
      options.skipFrontend = true;
    } else if (arg === '--skip-api') {
      options.skipApi = true;
    } else if (arg === '--skip-ai') {
      options.skipAi = true;
    } else if (arg === '--skip-monitoring') {
      options.skipMonitoring = true;
    } else if (arg === '--help' || arg === '-h') {
      showHelp();
      process.exit(0);
    } else if (arg.startsWith('--')) {
      console.log(`${colors.yellow}Warning: Unknown option ${arg}${colors.reset}`);
    } else {
      options.environment = arg;
    }
  }
  
  return options;
}

/**
 * Show help text
 */
function showHelp() {
  console.log(`
${colors.cyan}Maily Enhanced Smoke Test Script${colors.reset}

Usage: node enhanced-smoke-test.js [options]

Options:
  --environment, -e <env>    Set the environment to test (staging, production)
  --output, -o <file>        Save test results to the specified JSON file
  --skip-frontend            Skip frontend tests
  --skip-api                 Skip API tests
  --skip-ai                  Skip AI service tests
  --skip-monitoring          Skip monitoring tests
  --help, -h                 Show this help message

Examples:
  node enhanced-smoke-test.js
  node enhanced-smoke-test.js --environment production
  node enhanced-smoke-test.js -e staging -o test-results.json
  node enhanced-smoke-test.js --skip-frontend --skip-monitoring
`);
}

// Main script execution
async function main() {
  const options = parseArgs();
  
  try {
    const result = await runEnhancedSmokeTests(options.environment, options);
    process.exit(result.success ? 0 : 1);
  } catch (error) {
    console.error(`${colors.red}Error running smoke tests: ${error.message}${colors.reset}`);
    process.exit(1);
  }
}

// Run the script
main();