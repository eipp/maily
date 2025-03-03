#!/usr/bin/env node

/**
 * AI Service Verifier
 * 
 * This script verifies the deployment of the AI service
 * by checking its health, connectivity, and functionality.
 * 
 * Usage: ./ai-verifier.js <environment> <component> <version>
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');
const axios = require('axios');
const { execSync } = require('child_process');

// ANSI color codes for output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m'
};

// Get arguments from command line
const environment = process.argv[2];
const component = process.argv[3];
const version = process.argv[4];

if (!environment || !component || !version) {
  console.error(`${colors.red}Error: Missing required arguments${colors.reset}`);
  console.error(`Usage: ${path.basename(process.argv[1])} <environment> <component> <version>`);
  process.exit(1);
}

// Paths to configuration files
const configDir = path.resolve(__dirname, '../../config');
const configFile = path.join(configDir, `config.${environment}.yaml`);
const envFile = path.join(configDir, `.env.${environment}`);

// Verification results
const results = {
  passed: [],
  warnings: [],
  failed: []
};

/**
 * Load configuration files
 */
function loadConfig() {
  console.log(`${colors.blue}Loading configuration for ${environment} environment...${colors.reset}`);
  
  try {
    // Load YAML config
    if (!fs.existsSync(configFile)) {
      results.failed.push(`Configuration file not found: ${configFile}`);
      return null;
    }
    
    const config = yaml.load(fs.readFileSync(configFile, 'utf8'));
    results.passed.push(`Loaded configuration file: ${configFile}`);
    
    // Load environment variables
    if (!fs.existsSync(envFile)) {
      results.warnings.push(`Environment file not found: ${envFile}`);
    } else {
      const envVars = {};
      const envContent = fs.readFileSync(envFile, 'utf8');
      
      envContent.split('\n').forEach(line => {
        line = line.trim();
        if (!line || line.startsWith('#')) return;
        
        const [key, value] = line.split('=', 2);
        envVars[key] = value;
      });
      
      // Merge environment variables into config
      config.env = envVars;
      results.passed.push(`Loaded environment file: ${envFile}`);
    }
    
    return config;
  } catch (error) {
    results.failed.push(`Failed to load configuration: ${error.message}`);
    return null;
  }
}

/**
 * Verify Kubernetes deployment
 */
async function verifyKubernetesDeployment(config) {
  console.log(`${colors.blue}Verifying Kubernetes deployment...${colors.reset}`);
  
  const aiServiceConfig = config.components?.['ai-service'];
  if (!aiServiceConfig) {
    results.failed.push('AI service configuration not found in config file');
    return false;
  }
  
  const namespace = aiServiceConfig.namespace || 'maily';
  const deployment = aiServiceConfig.deployment || 'ai-service';
  const kubeContext = config.kubernetes?.context || `maily-${environment}`;
  
  try {
    // Check if deployment exists
    const deploymentOutput = execSync(
      `kubectl --context=${kubeContext} --namespace=${namespace} get deployment ${deployment} -o json`
    ).toString();
    
    const deploymentData = JSON.parse(deploymentOutput);
    
    // Check if deployment is available
    const availableReplicas = deploymentData.status?.availableReplicas || 0;
    const desiredReplicas = deploymentData.spec?.replicas || 0;
    
    if (availableReplicas < desiredReplicas) {
      results.failed.push(`Deployment ${deployment} has ${availableReplicas}/${desiredReplicas} available replicas`);
      return false;
    } else {
      results.passed.push(`Deployment ${deployment} has ${availableReplicas}/${desiredReplicas} available replicas`);
    }
    
    // Check if the correct image is being used
    const containers = deploymentData.spec?.template?.spec?.containers || [];
    let imageFound = false;
    
    for (const container of containers) {
      if (container.name === 'ai-service') {
        imageFound = true;
        const image = container.image;
        
        if (version !== 'latest' && !image.includes(version)) {
          results.failed.push(`Deployment ${deployment} is using image ${image}, expected version ${version}`);
          return false;
        } else {
          results.passed.push(`Deployment ${deployment} is using correct image: ${image}`);
        }
      }
    }
    
    if (!imageFound) {
      results.warnings.push(`Container 'ai-service' not found in deployment ${deployment}`);
    }
    
    // Check if pods are running
    const podsOutput = execSync(
      `kubectl --context=${kubeContext} --namespace=${namespace} get pods -l app=${deployment} -o json`
    ).toString();
    
    const podsData = JSON.parse(podsOutput);
    const pods = podsData.items || [];
    
    if (pods.length === 0) {
      results.failed.push(`No pods found for deployment ${deployment}`);
      return false;
    }
    
    let runningPods = 0;
    for (const pod of pods) {
      const podStatus = pod.status?.phase;
      const podName = pod.metadata?.name;
      
      if (podStatus === 'Running') {
        runningPods++;
        results.passed.push(`Pod ${podName} is running`);
      } else {
        results.warnings.push(`Pod ${podName} is in ${podStatus} state`);
      }
    }
    
    if (runningPods === 0) {
      results.failed.push(`No running pods found for deployment ${deployment}`);
      return false;
    } else {
      results.passed.push(`${runningPods}/${pods.length} pods are running`);
    }
    
    return true;
  } catch (error) {
    results.failed.push(`Failed to verify Kubernetes deployment: ${error.message}`);
    return false;
  }
}

/**
 * Verify HTTP health endpoint
 */
async function verifyHealthEndpoint(config) {
  console.log(`${colors.blue}Verifying HTTP health endpoint...${colors.reset}`);
  
  const domains = config.domains || {};
  const aiDomain = domains.ai;
  
  if (!aiDomain) {
    results.warnings.push('AI domain not specified in configuration');
    return false;
  }
  
  try {
    // Check health endpoint
    const response = await axios.get(`https://${aiDomain}/health`, {
      timeout: 10000,
      validateStatus: null // Accept any status code
    });
    
    if (response.status === 200) {
      results.passed.push(`Health endpoint returned status 200`);
      
      // Check version if available
      const data = response.data;
      if (data.version) {
        if (version !== 'latest' && data.version !== version) {
          results.warnings.push(`Health endpoint reports version ${data.version}, expected ${version}`);
        } else {
          results.passed.push(`Health endpoint reports correct version: ${data.version}`);
        }
      } else {
        results.warnings.push('Health endpoint does not report version');
      }
      
      // Check status
      if (data.status === 'ok') {
        results.passed.push(`Health endpoint reports status: ${data.status}`);
      } else {
        results.warnings.push(`Health endpoint reports status: ${data.status}`);
      }
      
      return true;
    } else {
      results.failed.push(`Health endpoint returned status ${response.status}`);
      return false;
    }
  } catch (error) {
    results.failed.push(`Failed to access health endpoint: ${error.message}`);
    return false;
  }
}

/**
 * Verify AI service functionality
 */
async function verifyAIServiceFunctionality(config) {
  console.log(`${colors.blue}Verifying AI service functionality...${colors.reset}`);
  
  const domains = config.domains || {};
  const aiDomain = domains.ai;
  
  if (!aiDomain) {
    results.warnings.push('AI domain not specified in configuration');
    return false;
  }
  
  try {
    // Test text generation endpoint
    const response = await axios.post(
      `https://${aiDomain}/api/v1/generation/text`,
      {
        prompt: "Hello, this is a test prompt. Please respond with a short greeting.",
        max_tokens: 50,
        temperature: 0.7
      },
      {
        timeout: 30000,
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': config.env?.API_KEY || 'test-verification-key'
        }
      }
    );
    
    if (response.status === 200) {
      results.passed.push('Successfully called text generation endpoint');
      
      const data = response.data;
      if (data.text && data.text.length > 0) {
        results.passed.push(`Received valid response from AI service: "${data.text.substring(0, 50)}${data.text.length > 50 ? '...' : ''}"`);
      } else {
        results.warnings.push('Received empty or invalid response from AI service');
      }
      
      // Check response time
      if (data.processing_time) {
        const processingTime = parseFloat(data.processing_time);
        if (processingTime > 5) {
          results.warnings.push(`AI service response time is high: ${processingTime.toFixed(2)}s`);
        } else {
          results.passed.push(`AI service response time is acceptable: ${processingTime.toFixed(2)}s`);
        }
      }
      
      return true;
    } else {
      results.failed.push(`Text generation endpoint returned status ${response.status}`);
      return false;
    }
  } catch (error) {
    if (error.response) {
      results.failed.push(`AI service error: ${error.response.status} ${error.response.statusText}`);
      if (error.response.data && error.response.data.error) {
        results.failed.push(`Error message: ${error.response.data.error}`);
      }
    } else if (error.request) {
      results.failed.push('AI service request failed: No response received');
    } else {
      results.failed.push(`AI service request failed: ${error.message}`);
    }
    return false;
  }
}

/**
 * Verify AI service metrics
 */
async function verifyMetrics(config) {
  console.log(`${colors.blue}Verifying AI service metrics...${colors.reset}`);
  
  const domains = config.domains || {};
  const aiDomain = domains.ai;
  
  if (!aiDomain) {
    results.warnings.push('AI domain not specified in configuration');
    return false;
  }
  
  try {
    // Check metrics endpoint
    const response = await axios.get(`https://${aiDomain}/metrics`, {
      timeout: 10000,
      validateStatus: null // Accept any status code
    });
    
    if (response.status === 200) {
      results.passed.push('Successfully accessed metrics endpoint');
      
      const metricsData = response.data;
      
      // Check for required metrics
      const requiredMetrics = [
        'http_requests_total',
        'http_request_duration_seconds',
        'ai_service_generation_duration_seconds',
        'ai_service_token_usage_total'
      ];
      
      for (const metric of requiredMetrics) {
        if (metricsData.includes(metric)) {
          results.passed.push(`Metric found: ${metric}`);
        } else {
          results.warnings.push(`Required metric not found: ${metric}`);
        }
      }
      
      return true;
    } else {
      results.warnings.push(`Metrics endpoint returned status ${response.status}`);
      return false;
    }
  } catch (error) {
    results.warnings.push(`Failed to access metrics endpoint: ${error.message}`);
    return false;
  }
}

/**
 * Print verification results
 */
function printResults() {
  console.log('\n' + '='.repeat(80));
  console.log(`${colors.blue}AI Service Verification Results${colors.reset}`);
  console.log('='.repeat(80));
  
  console.log(`\n${colors.green}Passed (${results.passed.length})${colors.reset}`);
  results.passed.forEach(msg => console.log(`✅ ${msg}`));
  
  if (results.warnings.length > 0) {
    console.log(`\n${colors.yellow}Warnings (${results.warnings.length})${colors.reset}`);
    results.warnings.forEach(msg => console.log(`⚠️ ${msg}`));
  }
  
  if (results.failed.length > 0) {
    console.log(`\n${colors.red}Failed (${results.failed.length})${colors.reset}`);
    results.failed.forEach(msg => console.log(`❌ ${msg}`));
  }
  
  console.log('\n' + '='.repeat(80));
  
  if (results.failed.length > 0) {
    console.log(`${colors.red}Verification failed with ${results.failed.length} errors${colors.reset}`);
    process.exit(1);
  } else if (results.warnings.length > 0) {
    console.log(`${colors.yellow}Verification passed with ${results.warnings.length} warnings${colors.reset}`);
    process.exit(0);
  } else {
    console.log(`${colors.green}Verification passed successfully${colors.reset}`);
    process.exit(0);
  }
}

/**
 * Main function
 */
async function main() {
  try {
    // Load configuration
    const config = loadConfig();
    if (!config) {
      printResults();
      return;
    }
    
    // Verify Kubernetes deployment
    const deploymentVerified = await verifyKubernetesDeployment(config);
    if (!deploymentVerified) {
      printResults();
      return;
    }
    
    // Verify health endpoint
    const healthVerified = await verifyHealthEndpoint(config);
    if (!healthVerified) {
      printResults();
      return;
    }
    
    // Verify AI service functionality
    await verifyAIServiceFunctionality(config);
    
    // Verify metrics
    await verifyMetrics(config);
    
    // Print results
    printResults();
  } catch (error) {
    console.error(`${colors.red}Verification failed with an unexpected error: ${error.message}${colors.reset}`);
    console.error(error.stack);
    process.exit(1);
  }
}

// Run the main function
main();
