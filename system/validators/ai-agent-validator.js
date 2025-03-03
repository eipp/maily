#!/usr/bin/env node

/**
 * AI Service Validator
 * 
 * This script validates the configuration and dependencies for the AI service
 * before deployment. It checks for required environment variables, API connectivity,
 * model availability, and other prerequisites.
 * 
 * Usage: ./ai-agent-validator.js <environment>
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
 * Validate AI service configuration
 */
function validateAIServiceConfig(config) {
  console.log(`${colors.blue}Validating AI service configuration...${colors.reset}`);
  
  const aiServiceConfig = config.components?.['ai-service'];
  if (!aiServiceConfig) {
    results.failed.push('AI service configuration not found in config file');
    return false;
  }
  
  // Check deployment method
  if (aiServiceConfig.deploy_method !== 'kubernetes') {
    results.warnings.push(`Unexpected deployment method: ${aiServiceConfig.deploy_method} (expected: kubernetes)`);
  } else {
    results.passed.push('Deployment method is valid: kubernetes');
  }
  
  // Check required fields
  const requiredFields = ['namespace', 'deployment', 'image'];
  for (const field of requiredFields) {
    if (!aiServiceConfig[field]) {
      results.failed.push(`Missing required field in AI service configuration: ${field}`);
    } else {
      results.passed.push(`AI service configuration has required field: ${field}`);
    }
  }
  
  // Check resources
  if (!aiServiceConfig.resources) {
    results.warnings.push('Resources not specified for AI service');
  } else {
    if (!aiServiceConfig.resources.requests?.cpu) {
      results.warnings.push('CPU requests not specified for AI service');
    } else if (parseFloat(aiServiceConfig.resources.requests.cpu) < 1) {
      results.warnings.push(`CPU requests may be too low for AI service: ${aiServiceConfig.resources.requests.cpu} (recommended: >= 1000m)`);
    }
    
    if (!aiServiceConfig.resources.requests?.memory) {
      results.warnings.push('Memory requests not specified for AI service');
    } else if (parseFloat(aiServiceConfig.resources.requests.memory.replace('Gi', '')) < 2) {
      results.warnings.push(`Memory requests may be too low for AI service: ${aiServiceConfig.resources.requests.memory} (recommended: >= 2Gi)`);
    }
    
    if (!aiServiceConfig.resources.limits?.cpu) {
      results.warnings.push('CPU limits not specified for AI service');
    }
    
    if (!aiServiceConfig.resources.limits?.memory) {
      results.warnings.push('Memory limits not specified for AI service');
    }
  }
  
  // Check replicas
  if (!aiServiceConfig.replicas) {
    results.warnings.push('Replicas not specified for AI service');
  } else if (environment === 'production' && aiServiceConfig.replicas < 2) {
    results.warnings.push(`Insufficient replicas for production: ${aiServiceConfig.replicas} (recommended: >= 2)`);
  } else {
    results.passed.push(`AI service replicas: ${aiServiceConfig.replicas}`);
  }
  
  // Check autoscaling for production
  if (environment === 'production' && !aiServiceConfig.autoscaling?.enabled) {
    results.warnings.push('Autoscaling not enabled for AI service in production');
  } else if (environment === 'production') {
    results.passed.push('Autoscaling is enabled for AI service in production');
  }
  
  return true;
}

/**
 * Validate environment variables
 */
function validateEnvironmentVariables(config) {
  console.log(`${colors.blue}Validating environment variables...${colors.reset}`);
  
  const requiredEnvVars = ['OPENAI_API_KEY'];
  
  for (const envVar of requiredEnvVars) {
    if (!config.env?.[envVar]) {
      results.failed.push(`Missing required environment variable: ${envVar}`);
    } else {
      results.passed.push(`Environment variable present: ${envVar}`);
      
      // Validate API key format
      if (envVar === 'OPENAI_API_KEY') {
        const apiKey = config.env[envVar];
        if (!apiKey.startsWith('sk-')) {
          results.warnings.push('OPENAI_API_KEY does not have the expected format (should start with "sk-")');
        }
      }
    }
  }
  
  // Check optional environment variables
  const optionalEnvVars = ['AI_MODEL', 'LOG_LEVEL', 'ENABLE_REQUEST_LOGGING', 'ENABLE_PERFORMANCE_LOGGING'];
  
  for (const envVar of optionalEnvVars) {
    if (!config.env?.[envVar]) {
      results.warnings.push(`Optional environment variable not set: ${envVar}`);
    } else {
      results.passed.push(`Optional environment variable present: ${envVar}`);
      
      // Validate AI model
      if (envVar === 'AI_MODEL') {
        const model = config.env[envVar];
        const supportedModels = ['gpt-4o', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo'];
        
        if (!supportedModels.includes(model)) {
          results.warnings.push(`AI_MODEL value "${model}" may not be supported (recommended: ${supportedModels.join(', ')})`);
        }
      }
    }
  }
}

/**
 * Validate OpenAI API connectivity
 */
async function validateOpenAIAPI(config) {
  console.log(`${colors.blue}Validating OpenAI API connectivity...${colors.reset}`);
  
  const apiKey = config.env?.OPENAI_API_KEY;
  if (!apiKey) {
    results.failed.push('OpenAI API key not found in environment variables');
    return;
  }
  
  try {
    // Check API connectivity
    const response = await axios.get('https://api.openai.com/v1/models', {
      headers: {
        'Authorization': `Bearer ${apiKey}`
      },
      timeout: 10000
    });
    
    if (response.status === 200) {
      results.passed.push('Successfully connected to OpenAI API');
      
      // Check if required models are available
      const models = response.data.data || [];
      const modelIds = models.map(model => model.id);
      
      const requiredModel = config.env?.AI_MODEL || 'gpt-4o';
      
      if (modelIds.includes(requiredModel)) {
        results.passed.push(`Required model "${requiredModel}" is available`);
      } else {
        results.warnings.push(`Required model "${requiredModel}" not found in available models`);
      }
    } else {
      results.failed.push(`Failed to connect to OpenAI API: ${response.status} ${response.statusText}`);
    }
  } catch (error) {
    if (error.response) {
      results.failed.push(`OpenAI API error: ${error.response.status} ${error.response.statusText}`);
    } else if (error.request) {
      results.failed.push('OpenAI API request failed: No response received');
    } else {
      results.failed.push(`OpenAI API request failed: ${error.message}`);
    }
  }
}

/**
 * Validate network connectivity
 */
async function validateNetworkConnectivity(config) {
  console.log(`${colors.blue}Validating network connectivity...${colors.reset}`);
  
  const domains = config.domains || {};
  const aiDomain = domains.ai;
  
  if (!aiDomain) {
    results.warnings.push('AI domain not specified in configuration');
    return;
  }
  
  try {
    // Check DNS resolution
    execSync(`dig +short ${aiDomain}`);
    results.passed.push(`DNS resolution successful for ${aiDomain}`);
  } catch (error) {
    results.warnings.push(`DNS resolution failed for ${aiDomain}: ${error.message}`);
  }
  
  // Check HTTP connectivity (for health endpoint)
  try {
    await axios.get(`https://${aiDomain}/health`, {
      timeout: 5000,
      validateStatus: null // Accept any status code
    });
    results.passed.push(`HTTP connectivity successful for ${aiDomain}`);
  } catch (error) {
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      results.passed.push(`HTTP connectivity successful for ${aiDomain} (status: ${error.response.status})`);
    } else if (error.request) {
      // The request was made but no response was received
      results.warnings.push(`HTTP connectivity failed for ${aiDomain}: no response`);
    } else {
      // Something happened in setting up the request that triggered an Error
      results.warnings.push(`HTTP connectivity failed for ${aiDomain}: ${error.message}`);
    }
  }
}

/**
 * Validate AI service dependencies
 */
function validateDependencies() {
  console.log(`${colors.blue}Validating AI service dependencies...${colors.reset}`);
  
  try {
    // Check for required Python version
    const pythonVersion = execSync('python --version').toString().trim();
    const versionMatch = pythonVersion.match(/Python (\d+)\.(\d+)/);
    
    if (versionMatch && (parseInt(versionMatch[1]) > 3 || (parseInt(versionMatch[1]) === 3 && parseInt(versionMatch[2]) >= 8))) {
      results.passed.push(`Python version is compatible: ${pythonVersion}`);
    } else {
      results.warnings.push(`Python version may not be compatible: ${pythonVersion} (recommended: >= 3.8)`);
    }
    
    // Check for required Python packages
    const requiredPackages = ['fastapi', 'uvicorn', 'openai', 'redis', 'prometheus-client'];
    
    for (const pkg of requiredPackages) {
      try {
        execSync(`pip show ${pkg}`);
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
  console.log(`${colors.blue}AI Service Validation Results${colors.reset}`);
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
    const configValid = validateAIServiceConfig(config);
    if (!configValid) {
      printResults();
      return;
    }
    
    // Validate environment variables
    validateEnvironmentVariables(config);
    
    // Validate dependencies
    validateDependencies();
    
    // Validate OpenAI API connectivity
    await validateOpenAIAPI(config);
    
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
