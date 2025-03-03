#!/usr/bin/env node

/**
 * Canvas WebSocket Server Verifier
 * 
 * This script verifies the deployment of the Canvas WebSocket server
 * by checking its health, connectivity, and functionality.
 * 
 * Usage: ./canvas-verifier.js <environment> <component> <version>
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');
const WebSocket = require('ws');
const axios = require('axios');
const { v4: uuidv4 } = require('uuid');
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
  
  const websocketConfig = config.components?.websocket;
  if (!websocketConfig) {
    results.failed.push('WebSocket configuration not found in config file');
    return false;
  }
  
  const namespace = websocketConfig.namespace || 'maily';
  const deployment = websocketConfig.deployment || 'websocket';
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
      if (container.name === 'websocket') {
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
      results.warnings.push(`Container 'websocket' not found in deployment ${deployment}`);
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
  const websocketDomain = domains.websocket;
  
  if (!websocketDomain) {
    results.warnings.push('WebSocket domain not specified in configuration');
    return false;
  }
  
  try {
    // Check health endpoint
    const response = await axios.get(`https://${websocketDomain}/health`, {
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
 * Verify WebSocket connectivity
 */
async function verifyWebSocketConnectivity(config) {
  console.log(`${colors.blue}Verifying WebSocket connectivity...${colors.reset}`);
  
  const domains = config.domains || {};
  const websocketDomain = domains.websocket;
  
  if (!websocketDomain) {
    results.warnings.push('WebSocket domain not specified in configuration');
    return false;
  }
  
  return new Promise((resolve) => {
    try {
      // Connect to WebSocket server
      const ws = new WebSocket(`wss://${websocketDomain}/canvas`);
      
      // Set a timeout
      const timeout = setTimeout(() => {
        results.failed.push('WebSocket connection timed out');
        ws.terminate();
        resolve(false);
      }, 10000);
      
      // Handle connection open
      ws.on('open', () => {
        results.passed.push('Successfully connected to WebSocket server');
        
        // Send a ping message
        const pingMessage = {
          type: 'ping',
          id: uuidv4(),
          timestamp: Date.now()
        };
        
        ws.send(JSON.stringify(pingMessage));
        
        // Set a timeout for ping response
        const pingTimeout = setTimeout(() => {
          results.failed.push('WebSocket ping timed out');
          clearTimeout(timeout);
          ws.terminate();
          resolve(false);
        }, 5000);
        
        // Handle messages
        ws.on('message', (data) => {
          try {
            const message = JSON.parse(data);
            
            if (message.type === 'pong' && message.id === pingMessage.id) {
              results.passed.push('Received pong response from WebSocket server');
              clearTimeout(pingTimeout);
              clearTimeout(timeout);
              
              // Close the connection
              ws.close();
              resolve(true);
            }
          } catch (error) {
            results.warnings.push(`Failed to parse WebSocket message: ${error.message}`);
          }
        });
      });
      
      // Handle connection error
      ws.on('error', (error) => {
        results.failed.push(`WebSocket connection error: ${error.message}`);
        clearTimeout(timeout);
        resolve(false);
      });
      
      // Handle connection close
      ws.on('close', (code, reason) => {
        if (code !== 1000) {
          results.warnings.push(`WebSocket connection closed with code ${code}: ${reason}`);
        }
      });
    } catch (error) {
      results.failed.push(`Failed to connect to WebSocket server: ${error.message}`);
      resolve(false);
    }
  });
}

/**
 * Verify Canvas functionality
 */
async function verifyCanvasFunctionality(config) {
  console.log(`${colors.blue}Verifying Canvas functionality...${colors.reset}`);
  
  const domains = config.domains || {};
  const websocketDomain = domains.websocket;
  
  if (!websocketDomain) {
    results.warnings.push('WebSocket domain not specified in configuration');
    return false;
  }
  
  return new Promise((resolve) => {
    try {
      // Connect to WebSocket server
      const ws = new WebSocket(`wss://${websocketDomain}/canvas`);
      
      // Set a timeout
      const timeout = setTimeout(() => {
        results.failed.push('Canvas functionality test timed out');
        ws.terminate();
        resolve(false);
      }, 15000);
      
      // Handle connection open
      ws.on('open', () => {
        // Create a test session
        const sessionId = uuidv4();
        const userId = uuidv4();
        
        // Join session
        const joinMessage = {
          type: 'join',
          id: uuidv4(),
          sessionId,
          userId,
          username: 'Verifier Bot',
          timestamp: Date.now()
        };
        
        ws.send(JSON.stringify(joinMessage));
        
        // Handle messages
        ws.on('message', (data) => {
          try {
            const message = JSON.parse(data);
            
            if (message.type === 'joined' && message.sessionId === sessionId) {
              results.passed.push('Successfully joined Canvas session');
              
              // Send a test stroke
              const strokeMessage = {
                type: 'stroke',
                id: uuidv4(),
                sessionId,
                userId,
                points: [
                  { x: 100, y: 100, pressure: 0.5 },
                  { x: 200, y: 200, pressure: 0.5 },
                  { x: 300, y: 300, pressure: 0.5 }
                ],
                color: '#000000',
                width: 2,
                timestamp: Date.now()
              };
              
              ws.send(JSON.stringify(strokeMessage));
              
              // Wait for stroke acknowledgement
              setTimeout(() => {
                // Leave session
                const leaveMessage = {
                  type: 'leave',
                  id: uuidv4(),
                  sessionId,
                  userId,
                  timestamp: Date.now()
                };
                
                ws.send(JSON.stringify(leaveMessage));
                
                // Close the connection
                setTimeout(() => {
                  results.passed.push('Canvas functionality test completed successfully');
                  clearTimeout(timeout);
                  ws.close();
                  resolve(true);
                }, 1000);
              }, 1000);
            } else if (message.type === 'error') {
              results.failed.push(`Canvas error: ${message.error}`);
              clearTimeout(timeout);
              ws.close();
              resolve(false);
            }
          } catch (error) {
            results.warnings.push(`Failed to parse WebSocket message: ${error.message}`);
          }
        });
      });
      
      // Handle connection error
      ws.on('error', (error) => {
        results.failed.push(`WebSocket connection error: ${error.message}`);
        clearTimeout(timeout);
        resolve(false);
      });
      
      // Handle connection close
      ws.on('close', (code, reason) => {
        if (code !== 1000) {
          results.warnings.push(`WebSocket connection closed with code ${code}: ${reason}`);
        }
      });
    } catch (error) {
      results.failed.push(`Failed to connect to WebSocket server: ${error.message}`);
      resolve(false);
    }
  });
}

/**
 * Print verification results
 */
function printResults() {
  console.log('\n' + '='.repeat(80));
  console.log(`${colors.blue}Canvas WebSocket Server Verification Results${colors.reset}`);
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
    
    // Verify WebSocket connectivity
    const connectivityVerified = await verifyWebSocketConnectivity(config);
    if (!connectivityVerified) {
      printResults();
      return;
    }
    
    // Verify Canvas functionality
    await verifyCanvasFunctionality(config);
    
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
