#!/usr/bin/env node
/**
 * Maily Deployment Verification Script
 * This script verifies that a deployment was successful by running a set of checks
 */

const https = require('https');
const http = require('http');
const { URL } = require('url');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

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

/**
 * Parse command line arguments
 */
function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    environment: 'staging',
    outputFile: null,
    verbose: false
  };
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    
    if (arg === '--environment' || arg === '-e') {
      options.environment = args[++i] || 'staging';
    } else if (arg === '--output' || arg === '-o') {
      options.outputFile = args[++i];
    } else if (arg === '--verbose' || arg === '-v') {
      options.verbose = true;
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
${colors.cyan}Maily Deployment Verification Script${colors.reset}

Usage: node verify-deployment.js [options]

Options:
  --environment, -e <env>    Set the environment to test (staging, production)
  --output, -o <file>        Save verification results to the specified JSON file
  --verbose, -v              Show verbose output
  --help, -h                 Show this help message

Examples:
  node verify-deployment.js
  node verify-deployment.js --environment production
  node verify-deployment.js -e staging -v -o verification-report.json
`);
}

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
      timeout: options.timeout || 15000,
      headers: {
        'User-Agent': 'Maily-Deployment-Verification/1.0',
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
 * Run kubectl command and return the result
 */
function runKubectl(command) {
  try {
    const output = execSync(`kubectl ${command}`, { encoding: 'utf8' });
    return { success: true, output };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * Check if all required pods are running
 */
async function checkPodsStatus(namespace) {
  console.log(`${colors.blue}Checking pod status in ${namespace} namespace...${colors.reset}`);
  
  const result = runKubectl(`get pods -n ${namespace} -o json`);
  
  if (!result.success) {
    console.log(`${colors.red}Failed to get pods: ${result.error}${colors.reset}`);
    return { success: false, error: result.error };
  }
  
  try {
    const pods = JSON.parse(result.output).items;
    
    const podStatuses = pods.map(pod => {
      const name = pod.metadata.name;
      const phase = pod.status.phase;
      const ready = pod.status.containerStatuses ? 
        pod.status.containerStatuses.every(container => container.ready) : 
        false;
      const restarts = pod.status.containerStatuses ? 
        pod.status.containerStatuses.reduce((sum, container) => sum + container.restartCount, 0) : 
        0;
      
      const isReady = phase === 'Running' && ready;
      
      if (isReady) {
        console.log(`${colors.green}✓ Pod ${name} is running and ready (Restarts: ${restarts})${colors.reset}`);
      } else {
        console.log(`${colors.red}✗ Pod ${name} is not ready - Phase: ${phase}, Ready: ${ready}, Restarts: ${restarts}${colors.reset}`);
      }
      
      return { name, phase, ready, restarts, isReady };
    });
    
    const allReady = podStatuses.every(pod => pod.isReady);
    const readyCount = podStatuses.filter(pod => pod.isReady).length;
    
    console.log(`${colors.blue}Pods ready: ${readyCount}/${podStatuses.length}${colors.reset}`);
    
    return {
      success: allReady,
      pods: podStatuses,
      readyCount,
      totalCount: podStatuses.length
    };
  } catch (error) {
    console.log(`${colors.red}Error parsing pod information: ${error.message}${colors.reset}`);
    return { success: false, error: error.message };
  }
}

/**
 * Check all deployments in the namespace
 */
async function checkDeployments(namespace) {
  console.log(`${colors.blue}Checking deployment status in ${namespace} namespace...${colors.reset}`);
  
  const result = runKubectl(`get deployments -n ${namespace} -o json`);
  
  if (!result.success) {
    console.log(`${colors.red}Failed to get deployments: ${result.error}${colors.reset}`);
    return { success: false, error: result.error };
  }
  
  try {
    const deployments = JSON.parse(result.output).items;
    
    const deploymentStatuses = deployments.map(deployment => {
      const name = deployment.metadata.name;
      const replicas = deployment.spec.replicas;
      const availableReplicas = deployment.status.availableReplicas || 0;
      const updatedReplicas = deployment.status.updatedReplicas || 0;
      
      const isReady = availableReplicas === replicas && updatedReplicas === replicas;
      
      if (isReady) {
        console.log(`${colors.green}✓ Deployment ${name} is ready - ${availableReplicas}/${replicas} replicas available${colors.reset}`);
      } else {
        console.log(`${colors.red}✗ Deployment ${name} is not ready - ${availableReplicas}/${replicas} replicas available${colors.reset}`);
      }
      
      return { 
        name, 
        replicas, 
        availableReplicas, 
        updatedReplicas, 
        isReady,
        readyPercentage: replicas > 0 ? (availableReplicas / replicas) * 100 : 0
      };
    });
    
    const allReady = deploymentStatuses.every(deployment => deployment.isReady);
    const readyCount = deploymentStatuses.filter(deployment => deployment.isReady).length;
    
    console.log(`${colors.blue}Deployments ready: ${readyCount}/${deploymentStatuses.length}${colors.reset}`);
    
    return {
      success: allReady,
      deployments: deploymentStatuses,
      readyCount,
      totalCount: deploymentStatuses.length
    };
  } catch (error) {
    console.log(`${colors.red}Error parsing deployment information: ${error.message}${colors.reset}`);
    return { success: false, error: error.message };
  }
}

/**
 * Check all services in the namespace
 */
async function checkServices(namespace) {
  console.log(`${colors.blue}Checking service status in ${namespace} namespace...${colors.reset}`);
  
  const result = runKubectl(`get services -n ${namespace} -o json`);
  
  if (!result.success) {
    console.log(`${colors.red}Failed to get services: ${result.error}${colors.reset}`);
    return { success: false, error: result.error };
  }
  
  try {
    const services = JSON.parse(result.output).items;
    
    const serviceStatuses = services.map(service => {
      const name = service.metadata.name;
      const type = service.spec.type;
      const ports = service.spec.ports.map(port => ({
        name: port.name,
        port: port.port,
        targetPort: port.targetPort,
        nodePort: port.nodePort
      }));
      
      console.log(`${colors.green}✓ Service ${name} - Type: ${type}, Ports: ${ports.map(p => p.port).join(', ')}${colors.reset}`);
      
      return { name, type, ports };
    });
    
    console.log(`${colors.blue}Services: ${serviceStatuses.length}${colors.reset}`);
    
    return {
      success: true,
      services: serviceStatuses,
      count: serviceStatuses.length
    };
  } catch (error) {
    console.log(`${colors.red}Error parsing service information: ${error.message}${colors.reset}`);
    return { success: false, error: error.message };
  }
}

/**
 * Check recent events in the namespace
 */
async function checkEvents(namespace) {
  console.log(`${colors.blue}Checking recent events in ${namespace} namespace...${colors.reset}`);
  
  const result = runKubectl(`get events -n ${namespace} --sort-by='.lastTimestamp' -o json`);
  
  if (!result.success) {
    console.log(`${colors.red}Failed to get events: ${result.error}${colors.reset}`);
    return { success: false, error: result.error };
  }
  
  try {
    const events = JSON.parse(result.output).items;
    
    // Get events from the last hour
    const oneHourAgo = new Date();
    oneHourAgo.setHours(oneHourAgo.getHours() - 1);
    
    const recentEvents = events.filter(event => {
      const lastTimestamp = new Date(event.lastTimestamp);
      return lastTimestamp > oneHourAgo;
    });
    
    // Filter error events
    const errorEvents = recentEvents.filter(event => 
      event.type === 'Warning' || 
      event.reason.includes('Failed') || 
      event.reason.includes('Error')
    );
    
    if (errorEvents.length > 0) {
      console.log(`${colors.yellow}Found ${errorEvents.length} warning/error events in the last hour:${colors.reset}`);
      
      errorEvents.forEach(event => {
        console.log(`${colors.yellow}- [${event.lastTimestamp}] ${event.reason}: ${event.message} (${event.involvedObject.kind}/${event.involvedObject.name})${colors.reset}`);
      });
    } else {
      console.log(`${colors.green}✓ No error events found in the last hour${colors.reset}`);
    }
    
    return {
      success: errorEvents.length === 0,
      recentEvents: recentEvents.map(event => ({
        timestamp: event.lastTimestamp,
        type: event.type,
        reason: event.reason,
        message: event.message,
        object: `${event.involvedObject.kind}/${event.involvedObject.name}`
      })),
      errorEvents: errorEvents.map(event => ({
        timestamp: event.lastTimestamp,
        type: event.type,
        reason: event.reason,
        message: event.message,
        object: `${event.involvedObject.kind}/${event.involvedObject.name}`
      })),
      totalRecentEvents: recentEvents.length,
      totalErrorEvents: errorEvents.length
    };
  } catch (error) {
    console.log(`${colors.red}Error parsing event information: ${error.message}${colors.reset}`);
    return { success: false, error: error.message };
  }
}

/**
 * Check service endpoints
 */
async function checkEndpoints(urls) {
  console.log(`${colors.blue}Checking service endpoints...${colors.reset}`);
  
  const results = [];
  
  for (const [name, url] of Object.entries(urls)) {
    console.log(`${colors.cyan}Checking ${name} at ${url}...${colors.reset}`);
    
    try {
      const response = await makeRequest(`${url}/health`);
      
      if (response.status >= 200 && response.status < 300) {
        console.log(`${colors.green}✓ ${name} is healthy (Status: ${response.status})${colors.reset}`);
        results.push({ name, url, success: true, status: response.status });
      } else {
        console.log(`${colors.red}✗ ${name} returned error status: ${response.status}${colors.reset}`);
        results.push({ name, url, success: false, status: response.status });
      }
    } catch (error) {
      console.log(`${colors.red}✗ ${name} check failed: ${error.message}${colors.reset}`);
      results.push({ name, url, success: false, error: error.message });
    }
  }
  
  const successCount = results.filter(result => result.success).length;
  console.log(`${colors.blue}Endpoints: ${successCount}/${results.length} healthy${colors.reset}`);
  
  return {
    success: successCount === results.length,
    endpoints: results,
    successCount,
    totalCount: results.length
  };
}

/**
 * Main verification function
 */
async function verifyDeployment(options) {
  console.log(`${colors.green}Starting deployment verification for ${options.environment} environment${colors.reset}`);
  console.log(`Timestamp: ${new Date().toISOString()}`);
  
  const urls = environments[options.environment];
  if (!urls) {
    console.log(`${colors.red}Unknown environment: ${options.environment}${colors.reset}`);
    console.log(`Available environments: ${Object.keys(environments).join(', ')}`);
    process.exit(1);
  }
  
  const namespace = options.environment === 'production' ? 'maily' : 'staging';
  
  // Verify kubernetes resources
  const results = {
    timestamp: new Date().toISOString(),
    environment: options.environment,
    namespace,
    kubernetesStatus: {
      podsStatus: null,
      deploymentsStatus: null,
      servicesStatus: null,
      eventsStatus: null
    },
    endpointsStatus: null,
    overallStatus: null
  };
  
  // Check kubernetes resources
  console.log(`\n${colors.magenta}=== Kubernetes Resource Verification ===${colors.reset}`);
  results.kubernetesStatus.podsStatus = await checkPodsStatus(namespace);
  results.kubernetesStatus.deploymentsStatus = await checkDeployments(namespace);
  results.kubernetesStatus.servicesStatus = await checkServices(namespace);
  results.kubernetesStatus.eventsStatus = await checkEvents(namespace);
  
  // Check endpoints
  console.log(`\n${colors.magenta}=== Service Endpoint Verification ===${colors.reset}`);
  results.endpointsStatus = await checkEndpoints({
    frontend: urls.frontend,
    api: urls.api,
    ai: urls.ai
  });
  
  // Calculate overall status
  const kubernetesSuccess = 
    results.kubernetesStatus.podsStatus.success &&
    results.kubernetesStatus.deploymentsStatus.success &&
    results.kubernetesStatus.eventsStatus.success;
  
  const endpointsSuccess = results.endpointsStatus.success;
  
  results.overallStatus = {
    success: kubernetesSuccess && endpointsSuccess,
    kubernetesSuccess,
    endpointsSuccess
  };
  
  // Generate summary
  console.log(`\n${colors.magenta}=== Verification Summary ===${colors.reset}`);
  
  const kubernetesStatus = kubernetesSuccess ? 
    `${colors.green}PASS${colors.reset}` : 
    `${colors.red}FAIL${colors.reset}`;
  
  const endpointsStatus = endpointsSuccess ? 
    `${colors.green}PASS${colors.reset}` : 
    `${colors.red}FAIL${colors.reset}`;
  
  const overallStatus = results.overallStatus.success ? 
    `${colors.green}PASS${colors.reset}` : 
    `${colors.red}FAIL${colors.reset}`;
  
  console.log(`Kubernetes Resources: ${kubernetesStatus}`);
  console.log(`Service Endpoints: ${endpointsStatus}`);
  console.log(`\nOverall Status: ${overallStatus}`);
  
  // Output to file if requested
  if (options.outputFile) {
    try {
      fs.writeFileSync(options.outputFile, JSON.stringify(results, null, 2));
      console.log(`\n${colors.green}Results saved to ${options.outputFile}${colors.reset}`);
    } catch (error) {
      console.log(`\n${colors.red}Error saving results to ${options.outputFile}: ${error.message}${colors.reset}`);
    }
  }
  
  return results;
}

// Main script execution
async function main() {
  const options = parseArgs();
  
  try {
    const results = await verifyDeployment(options);
    process.exit(results.overallStatus.success ? 0 : 1);
  } catch (error) {
    console.error(`${colors.red}Error running verification: ${error.message}${colors.reset}`);
    process.exit(1);
  }
}

// Run the script
main();