#!/usr/bin/env node

/**
 * Blockchain Service Validator
 * 
 * This script validates the configuration and dependencies for the blockchain service
 * before deployment. It checks for required environment variables, network connectivity,
 * smart contract compatibility, and other prerequisites.
 * 
 * Usage: ./blockchain-validator.js <environment>
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');
const axios = require('axios');
const { execSync } = require('child_process');
const { ethers } = require('ethers');

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
 * Validate blockchain service configuration
 */
function validateBlockchainServiceConfig(config) {
  console.log(`${colors.blue}Validating blockchain service configuration...${colors.reset}`);
  
  const blockchainConfig = config.components?.blockchain;
  if (!blockchainConfig) {
    results.failed.push('Blockchain service configuration not found in config file');
    return false;
  }
  
  // Check deployment method
  if (blockchainConfig.deploy_method !== 'kubernetes') {
    results.warnings.push(`Unexpected deployment method: ${blockchainConfig.deploy_method} (expected: kubernetes)`);
  } else {
    results.passed.push('Deployment method is valid: kubernetes');
  }
  
  // Check required fields
  const requiredFields = ['namespace', 'deployment', 'image'];
  for (const field of requiredFields) {
    if (!blockchainConfig[field]) {
      results.failed.push(`Missing required field in blockchain service configuration: ${field}`);
    } else {
      results.passed.push(`Blockchain service configuration has required field: ${field}`);
    }
  }
  
  // Check resources
  if (!blockchainConfig.resources) {
    results.warnings.push('Resources not specified for blockchain service');
  } else {
    if (!blockchainConfig.resources.requests?.cpu) {
      results.warnings.push('CPU requests not specified for blockchain service');
    }
    
    if (!blockchainConfig.resources.requests?.memory) {
      results.warnings.push('Memory requests not specified for blockchain service');
    }
    
    if (!blockchainConfig.resources.limits?.cpu) {
      results.warnings.push('CPU limits not specified for blockchain service');
    }
    
    if (!blockchainConfig.resources.limits?.memory) {
      results.warnings.push('Memory limits not specified for blockchain service');
    }
  }
  
  // Check replicas
  if (!blockchainConfig.replicas) {
    results.warnings.push('Replicas not specified for blockchain service');
  } else if (environment === 'production' && blockchainConfig.replicas < 2) {
    results.warnings.push(`Insufficient replicas for production: ${blockchainConfig.replicas} (recommended: >= 2)`);
  } else {
    results.passed.push(`Blockchain service replicas: ${blockchainConfig.replicas}`);
  }
  
  // Check autoscaling for production
  if (environment === 'production' && !blockchainConfig.autoscaling?.enabled) {
    results.warnings.push('Autoscaling not enabled for blockchain service in production');
  } else if (environment === 'production') {
    results.passed.push('Autoscaling is enabled for blockchain service in production');
  }
  
  return true;
}

/**
 * Validate environment variables
 */
function validateEnvironmentVariables(config) {
  console.log(`${colors.blue}Validating environment variables...${colors.reset}`);
  
  const requiredEnvVars = ['ETHEREUM_RPC_URL', 'BLOCKCHAIN_PRIVATE_KEY'];
  
  for (const envVar of requiredEnvVars) {
    if (!config.env?.[envVar]) {
      results.failed.push(`Missing required environment variable: ${envVar}`);
    } else {
      results.passed.push(`Environment variable present: ${envVar}`);
      
      // Validate private key format
      if (envVar === 'BLOCKCHAIN_PRIVATE_KEY') {
        const privateKey = config.env[envVar];
        if (!privateKey.startsWith('0x') || privateKey.length !== 66) {
          results.warnings.push('BLOCKCHAIN_PRIVATE_KEY does not have the expected format (should be 0x followed by 64 hex characters)');
        }
      }
      
      // Validate RPC URL format
      if (envVar === 'ETHEREUM_RPC_URL') {
        const rpcUrl = config.env[envVar];
        if (!rpcUrl.startsWith('http')) {
          results.warnings.push('ETHEREUM_RPC_URL does not have the expected format (should start with http:// or https://)');
        }
      }
    }
  }
  
  // Check optional environment variables
  const optionalEnvVars = ['LOG_LEVEL', 'ENABLE_REQUEST_LOGGING', 'ENABLE_PERFORMANCE_LOGGING', 'GAS_PRICE_MULTIPLIER'];
  
  for (const envVar of optionalEnvVars) {
    if (!config.env?.[envVar]) {
      results.warnings.push(`Optional environment variable not set: ${envVar}`);
    } else {
      results.passed.push(`Optional environment variable present: ${envVar}`);
    }
  }
}

/**
 * Validate Ethereum network connectivity
 */
async function validateEthereumConnectivity(config) {
  console.log(`${colors.blue}Validating Ethereum network connectivity...${colors.reset}`);
  
  const rpcUrl = config.env?.ETHEREUM_RPC_URL;
  if (!rpcUrl) {
    results.failed.push('Ethereum RPC URL not found in environment variables');
    return;
  }
  
  try {
    // Create a provider
    const provider = new ethers.providers.JsonRpcProvider(rpcUrl);
    
    // Check network connectivity
    const network = await provider.getNetwork();
    results.passed.push(`Successfully connected to Ethereum network: ${network.name} (chainId: ${network.chainId})`);
    
    // Check if we're on the right network
    if (environment === 'production') {
      if (network.name !== 'homestead' && network.chainId !== 1) {
        results.warnings.push(`Production environment should use mainnet, but connected to ${network.name} (chainId: ${network.chainId})`);
      } else {
        results.passed.push('Connected to correct network for production: mainnet');
      }
    } else {
      if (network.name === 'homestead' || network.chainId === 1) {
        results.warnings.push(`Non-production environment should not use mainnet, but connected to ${network.name} (chainId: ${network.chainId})`);
      } else {
        results.passed.push(`Connected to test network for ${environment}: ${network.name} (chainId: ${network.chainId})`);
      }
    }
    
    // Check block height
    const blockNumber = await provider.getBlockNumber();
    results.passed.push(`Current block number: ${blockNumber}`);
    
    // Check gas price
    const gasPrice = await provider.getGasPrice();
    const gasPriceGwei = ethers.utils.formatUnits(gasPrice, 'gwei');
    results.passed.push(`Current gas price: ${gasPriceGwei} Gwei`);
    
    // Check account balance
    const privateKey = config.env?.BLOCKCHAIN_PRIVATE_KEY;
    if (privateKey) {
      try {
        const wallet = new ethers.Wallet(privateKey, provider);
        const balance = await wallet.getBalance();
        const balanceEth = ethers.utils.formatEther(balance);
        
        results.passed.push(`Account balance: ${balanceEth} ETH`);
        
        if (parseFloat(balanceEth) < 0.1) {
          results.warnings.push(`Low account balance: ${balanceEth} ETH (recommended: >= 0.1 ETH)`);
        }
      } catch (error) {
        results.warnings.push(`Failed to check account balance: ${error.message}`);
      }
    }
  } catch (error) {
    results.failed.push(`Failed to connect to Ethereum network: ${error.message}`);
  }
}

/**
 * Validate smart contracts
 */
async function validateSmartContracts(config) {
  console.log(`${colors.blue}Validating smart contracts...${colors.reset}`);
  
  try {
    // Check if blockchain directory exists
    const blockchainDir = path.resolve(__dirname, '../../blockchain');
    if (!fs.existsSync(blockchainDir)) {
      results.warnings.push('Blockchain directory not found');
      return;
    }
    
    // Check if contracts directory exists
    const contractsDir = path.join(blockchainDir, 'contracts');
    if (!fs.existsSync(contractsDir)) {
      results.warnings.push('Contracts directory not found');
      return;
    }
    
    // Check if there are any contracts
    const contractFiles = fs.readdirSync(contractsDir).filter(file => file.endsWith('.sol'));
    if (contractFiles.length === 0) {
      results.warnings.push('No smart contracts found');
      return;
    }
    
    results.passed.push(`Found ${contractFiles.length} smart contract(s): ${contractFiles.join(', ')}`);
    
    // Check if hardhat.config.js exists
    const hardhatConfigPath = path.join(blockchainDir, 'hardhat.config.js');
    if (!fs.existsSync(hardhatConfigPath)) {
      results.warnings.push('Hardhat configuration file not found');
      return;
    }
    
    results.passed.push('Hardhat configuration file found');
    
    // Check if deployment scripts exist
    const scriptsDir = path.join(blockchainDir, 'scripts');
    if (!fs.existsSync(scriptsDir)) {
      results.warnings.push('Deployment scripts directory not found');
      return;
    }
    
    const deploymentScripts = fs.readdirSync(scriptsDir).filter(file => file.includes('deploy'));
    if (deploymentScripts.length === 0) {
      results.warnings.push('No deployment scripts found');
    } else {
      results.passed.push(`Found ${deploymentScripts.length} deployment script(s): ${deploymentScripts.join(', ')}`);
    }
    
    // Check if test directory exists
    const testDir = path.join(blockchainDir, 'test');
    if (!fs.existsSync(testDir)) {
      results.warnings.push('Test directory not found');
    } else {
      const testFiles = fs.readdirSync(testDir).filter(file => file.endsWith('.js') || file.endsWith('.ts'));
      if (testFiles.length === 0) {
        results.warnings.push('No test files found');
      } else {
        results.passed.push(`Found ${testFiles.length} test file(s): ${testFiles.join(', ')}`);
      }
    }
    
    // Try to compile contracts
    try {
      console.log(`${colors.blue}Compiling smart contracts...${colors.reset}`);
      
      // Change to blockchain directory
      process.chdir(blockchainDir);
      
      // Run hardhat compile
      execSync('npx hardhat compile', { stdio: 'pipe' });
      
      results.passed.push('Successfully compiled smart contracts');
      
      // Check if artifacts directory exists
      const artifactsDir = path.join(blockchainDir, 'artifacts/contracts');
      if (fs.existsSync(artifactsDir)) {
        const artifactFiles = fs.readdirSync(artifactsDir, { recursive: true })
          .filter(file => file.endsWith('.json') && !file.endsWith('.dbg.json'));
        
        if (artifactFiles.length > 0) {
          results.passed.push(`Found ${artifactFiles.length} compiled artifact(s)`);
        } else {
          results.warnings.push('No compiled artifacts found');
        }
      }
    } catch (error) {
      results.failed.push(`Failed to compile smart contracts: ${error.message}`);
    }
  } catch (error) {
    results.warnings.push(`Failed to validate smart contracts: ${error.message}`);
  }
}

/**
 * Validate network connectivity
 */
async function validateNetworkConnectivity(config) {
  console.log(`${colors.blue}Validating network connectivity...${colors.reset}`);
  
  const domains = config.domains || {};
  const blockchainDomain = domains.blockchain;
  
  if (!blockchainDomain) {
    results.warnings.push('Blockchain domain not specified in configuration');
    return;
  }
  
  try {
    // Check DNS resolution
    execSync(`dig +short ${blockchainDomain}`);
    results.passed.push(`DNS resolution successful for ${blockchainDomain}`);
  } catch (error) {
    results.warnings.push(`DNS resolution failed for ${blockchainDomain}: ${error.message}`);
  }
  
  // Check HTTP connectivity (for health endpoint)
  try {
    await axios.get(`https://${blockchainDomain}/health`, {
      timeout: 5000,
      validateStatus: null // Accept any status code
    });
    results.passed.push(`HTTP connectivity successful for ${blockchainDomain}`);
  } catch (error) {
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      results.passed.push(`HTTP connectivity successful for ${blockchainDomain} (status: ${error.response.status})`);
    } else if (error.request) {
      // The request was made but no response was received
      results.warnings.push(`HTTP connectivity failed for ${blockchainDomain}: no response`);
    } else {
      // Something happened in setting up the request that triggered an Error
      results.warnings.push(`HTTP connectivity failed for ${blockchainDomain}: ${error.message}`);
    }
  }
}

/**
 * Validate blockchain service dependencies
 */
function validateDependencies() {
  console.log(`${colors.blue}Validating blockchain service dependencies...${colors.reset}`);
  
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
    const requiredPackages = ['ethers', 'hardhat', 'express', 'prometheus-client'];
    
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
  console.log(`${colors.blue}Blockchain Service Validation Results${colors.reset}`);
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
    const configValid = validateBlockchainServiceConfig(config);
    if (!configValid) {
      printResults();
      return;
    }
    
    // Validate environment variables
    validateEnvironmentVariables(config);
    
    // Validate dependencies
    validateDependencies();
    
    // Validate Ethereum network connectivity
    await validateEthereumConnectivity(config);
    
    // Validate smart contracts
    await validateSmartContracts(config);
    
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
