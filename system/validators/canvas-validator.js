#!/usr/bin/env node

/**
 * Canvas WebSocket Server Validator
 * 
 * This script validates the configuration and dependencies for the Canvas WebSocket server
 * before deployment. It checks for required environment variables, network connectivity,
 * Redis connection, and other prerequisites.
 * 
 * Usage: ./canvas-validator.js <environment>
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');
const Redis = require('ioredis');
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

// Get environment from command line arguments
const environment = process.argv[2];
if (!environment) {
  console.error(`${colors.red}Error: Environment not specified${colors.reset}`);
  console.error(`Usage: ${path.basename(process.argv[1])} <environment>`);
  process.exit(1);
}

// Paths to configuration files
const configDir = path.resolve(__dirname, '../../config');
const configFile = path.join(configDir, `config.${environment}.yaml`);
const envFile = path.join(configDir, `.env.${environment}`);

// Validation results
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
 * Validate WebSocket server configuration
 */
function validateWebSocketConfig(config) {
  console.log(`${colors.blue}Validating WebSocket server configuration...${colors.reset}`);
  
  const websocketConfig = config.components?.websocket;
  if (!websocketConfig) {
    results.failed.push('WebSocket configuration not found in config file');
    return false;
  }
  
  // Check deployment method
  if (websocketConfig.deploy_method !== 'kubernetes') {
    results.warnings.push(`Unexpected deployment method: ${websocketConfig.deploy_method} (expected: kubernetes)`);
  } else {
    results.passed.push('Deployment method is valid: kubernetes');
  }
  
  // Check required fields
  const requiredFields = ['namespace', 'deployment', 'image'];
  for (const field of requiredFields) {
    if (!websocketConfig[field]) {
      results.failed.push(`Missing required field in WebSocket configuration: ${field}`);
    } else {
      results.passed.push(`WebSocket configuration has required field: ${field}`);
    }
  }
  
  // Check resources
  if (!websocketConfig.resources) {
    results.warnings.push('Resources not specified for WebSocket server');
  } else {
    if (!websocketConfig.resources.requests?.cpu) {
      results.warnings.push('CPU requests not specified for WebSocket server');
    }
    if (!websocketConfig.resources.requests?.memory) {
      results.warnings.push('Memory requests not specified for WebSocket server');
    }
    if (!websocketConfig.resources.limits?.cpu) {
      results.warnings.push('CPU limits not specified for WebSocket server');
    }
    if (!websocketConfig.resources.limits?.memory) {
      results.warnings.push('Memory limits not specified for WebSocket server');
    }
  }
  
  // Check replicas
  if (!websocketConfig.replicas) {
    results.warnings.push('Replicas not specified for WebSocket server');
  } else if (environment === 'production' && websocketConfig.replicas < 3) {
    results.warnings.push(`Insufficient replicas for production: ${websocketConfig.replicas} (recommended: >= 3)`);
  } else {
    results.passed.push(`WebSocket server replicas: ${websocketConfig.replicas}`);
  }
  
  // Check autoscaling for production
  if (environment === 'production' && !websocketConfig.autoscaling?.enabled) {
    results.warnings.push('Autoscaling not enabled for WebSocket server in production');
  } else if (environment === 'production') {
    results.passed.push('Autoscaling is enabled for WebSocket server in production');
  }
  
  return true;
}

/**
 * Validate environment variables
 */
function validateEnvironmentVariables(config) {
  console.log(`${colors.blue}Validating environment variables...${colors.reset}`);
  
  const requiredEnvVars = ['REDIS_URL'];
  
  for (const envVar of requiredEnvVars) {
    if (!config.env?.[envVar]) {
      results.failed.push(`Missing required environment variable: ${envVar}`);
    } else {
      results.passed.push(`Environment variable present: ${envVar}`);
    }
  }
  
  // Check optional environment variables
  const optionalEnvVars = ['LOG_LEVEL', 'ENABLE_REQUEST_LOGGING', 'ENABLE_PERFORMANCE_LOGGING'];
  
  for (const envVar of optionalEnvVars) {
    if (!config.env?.[envVar]) {
      results.warnings.push(`Optional environment variable not set: ${envVar}`);
    } else {
      results.passed.push(`Optional environment variable present: ${envVar}`);
    }
  }
}

/**
 * Validate Redis connection
 */
async function validateRedisConnection(config) {
  console.log(`${colors.blue}Validating Redis connection...${colors.reset}`);
  
  const redisUrl = config.env?.REDIS_URL;
  if (!redisUrl) {
    results.failed.push('Redis URL not found in environment variables');
    return;
  }
  
  try {
    // Create a Redis client with a short timeout
    const redis = new Redis(redisUrl, {
      connectTimeout: 5000,
      maxRetriesPerRequest: 1
    });
    
    // Test connection
    await new Promise((resolve, reject) => {
      redis.ping((err, result) => {
        if (err) {
          reject(err);
        } else {
          resolve(result);
        }
      });
      
      // Set a timeout
      setTimeout(() => {
        reject(new Error('Redis connection timeout'));
      }, 5000);
    });
    
    results.passed.push('Successfully connected to Redis');
    
    // Close the connection
    redis.disconnect();
  } catch (error) {
    results.failed.push(`Failed to connect to Redis: ${error.message}`);
  }
}

/**
 * Validate network connectivity
 */
async function validateNetworkConnectivity(config) {
  console.log(`${colors.blue}Validating network connectivity...${colors.reset}`);
  
  const domains = config.domains || {};
  const websocketDomain = domains.websocket;
  
  if (!websocketDomain) {
    results.warnings.push('WebSocket domain not specified in configuration');
    return;
  }
  
  try {
    // Check DNS resolution
    execSync(`dig +short ${websocketDomain}`);
    results.passed.push(`DNS resolution successful for ${websocketDomain}`);
  } catch (error) {
    results.warnings.push(`DNS resolution failed for ${websocketDomain}: ${error.message}`);
  }
  
  // Check HTTP connectivity (for health endpoint)
  try {
    await axios.get(`https://${websocketDomain}/health`, {
      timeout: 5000,
      validateStatus: null // Accept any status code
    });
    results.passed.push(`HTTP connectivity successful for ${websocketDomain}`);
  } catch (error) {
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      results.passed.push(`HTTP connectivity successful for ${websocketDomain} (status: ${error.response.status})`);
    } else if (error.request) {
      // The request was made but no response was received
      results.warnings.push(`HTTP connectivity failed for ${websocketDomain}: no response`);
    } else {
      // Something happened in setting up the request that triggered an Error
      results.warnings.push(`HTTP connectivity failed for ${websocketDomain}: ${error.message}`);
    }
  }
}

/**
 * Validate WebSocket server dependencies
 */
function validateDependencies() {
  console.log(`${colors.blue}Validating WebSocket server dependencies...${colors.reset}`);
  
  try {
    // Check for required Node.js version
    const nodeVersion = execSync('node --version').toString().trim();
    const versionMatch = nodeVersion.match(/v(\d+)\./);
    
    if (versionMatch && parseInt(versionMatch[1]) >= 16) {
      results.passed.push(`Node.js version is compatible: ${nodeVersion}`);
    } else {
      results.warnings.push(`Node.js version may not be compatible: ${nodeVersion} (recommended: >= 16.x)`);
    }
    
    // Check for required npm packages
    const requiredPackages = ['ws', 'ioredis', 'uuid', 'express'];
    
    for (const pkg of requiredPackages) {
      try {
        require.resolve(pkg);
        results.passed.push(`Required package is available: ${pkg}`);
      } catch (error) {
        results.failed.push(`Required package is missing: ${pkg}`);
      }
    }
  } catch (error) {
    results.warnings.push(`Failed to validate dependencies: ${error.message}`);
  }
}

/**
 * Print validation results
 */
function printResults() {
  console.log('\n' + '='.repeat(80));
  console.log(`${colors.blue}Canvas WebSocket Server Validation Results${colors.reset}`);
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
    console.log(`${colors.red}Validation failed with ${results.failed.length} errors${colors.reset}`);
    process.exit(1);
  } else if (results.warnings.length > 0) {
    console.log(`${colors.yellow}Validation passed with ${results.warnings.length} warnings${colors.reset}`);
    process.exit(0);
  } else {
    console.log(`${colors.green}Validation passed successfully${colors.reset}`);
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
    
    // Validate configuration
    const configValid = validateWebSocketConfig(config);
    if (!configValid) {
      printResults();
      return;
    }
    
    // Validate environment variables
    validateEnvironmentVariables(config);
    
    // Validate dependencies
    validateDependencies();
    
    // Validate Redis connection
    await validateRedisConnection(config);
    
    // Validate network connectivity
    await validateNetworkConnectivity(config);
    
    // Print results
    printResults();
  } catch (error) {
    console.error(`${colors.red}Validation failed with an unexpected error: ${error.message}${colors.reset}`);
    console.error(error.stack);
    process.exit(1);
  }
}

// Run the main function
main();
