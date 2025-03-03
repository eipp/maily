#!/usr/bin/env node

/**
 * Maily Dependency Checker - March 2025
 * 
 * This script checks all dependencies against the specified versions
 * in the documentation and generates a report with update recommendations.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const https = require('https');

// Color formatting for console output
const colors = {
  reset: "\x1b[0m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  red: "\x1b[31m",
  cyan: "\x1b[36m",
  magenta: "\x1b[35m",
  blue: "\x1b[34m"
};

// March 2025 dependency specifications
const targetDependencies = {
  // Core Framework & UI
  "next": "14.2.1",
  "react": "18.3.0",
  "react-dom": "18.3.0",
  "typescript": "5.4.2",
  "tailwindcss": "3.4.1",
  "@radix-ui/react-primitives": "2.0.2",
  "framer-motion": "11.0.5",
  "lucide-react": "0.344.0",
  "next-themes": "0.2.1",
  "cmdk": "0.2.1",
  
  // Canvas & Visual Creation
  "tldraw": "2.0.0-canary.20",
  "lexical": "0.12.5",
  "@lexical/react": "0.12.5",
  "mjml": "4.15.0",
  "react-email": "1.10.0",
  
  // State Management
  "@reduxjs/toolkit": "2.2.1",
  "react-redux": "9.1.0",
  "zustand": "4.5.0",
  "swr": "2.2.4",
  "@tanstack/react-query": "5.22.2",
  
  // Collaboration
  "yjs": "13.6.1", 
  "y-websocket": "1.5.1",
  "y-indexeddb": "9.0.12",
  "socket.io-client": "4.7.4",
  
  // AI & Machine Learning
  "@anthropic-ai/sdk": "0.11.0",
  "openai": "4.24.7",
  "@google/generative-ai": "0.2.0",
  "ai": "2.2.34",
  "@tensorflow/tfjs": "4.16.0",
  
  // Visualization
  "recharts": "2.12.0",
  "d3": "7.8.5",
  
  // Blockchain
  "ethers": "6.7.1",
  "date-fns": "3.3.1",
  // Web3 packages
  "@web3modal/wagmi": "5.1.11",
  "@web3modal/react": "2.7.1",
  "@web3modal/standalone": "2.4.3",
  "@metamask/sdk-react": "0.15.0"
};

// High-priority packages to specifically verify
const priorityPackages = [
  "next", 
  "react",
  "react-dom",
  "@tensorflow/tfjs",
  "ethers",
  "yjs",
  "@anthropic-ai/sdk",
  "openai",
  "@google/generative-ai"
];

/**
 * Find all package.json files in the project
 */
function findPackageJsonFiles() {
  const results = [];
  
  // Check root package.json
  if (fs.existsSync('package.json')) {
    results.push('package.json');
  }
  
  // Check apps directory
  if (fs.existsSync('apps')) {
    const apps = fs.readdirSync('apps');
    apps.forEach(app => {
      const appPackageJson = path.join('apps', app, 'package.json');
      if (fs.existsSync(appPackageJson)) {
        results.push(appPackageJson);
      }
    });
  }
  
  // Check packages directory
  if (fs.existsSync('packages')) {
    const packages = fs.readdirSync('packages');
    packages.forEach(pkg => {
      const pkgPackageJson = path.join('packages', pkg, 'package.json');
      if (fs.existsSync(pkgPackageJson)) {
        results.push(pkgPackageJson);
      }
    });
  }
  
  return results;
}

/**
 * Get all dependencies from package.json files
 */
function getAllDependencies() {
  const packageJsonFiles = findPackageJsonFiles();
  const allDependencies = {};
  
  packageJsonFiles.forEach(filePath => {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      const packageJson = JSON.parse(content);
      
      // Process regular dependencies
      if (packageJson.dependencies) {
        Object.entries(packageJson.dependencies).forEach(([name, version]) => {
          // Clean version string (remove ^, ~, etc.)
          const cleanVersion = version.replace(/^[\^~]/, '');
          
          if (!allDependencies[name]) {
            allDependencies[name] = [];
          }
          
          allDependencies[name].push({
            file: filePath,
            version: cleanVersion,
            isDev: false
          });
        });
      }
      
      // Process dev dependencies
      if (packageJson.devDependencies) {
        Object.entries(packageJson.devDependencies).forEach(([name, version]) => {
          // Clean version string (remove ^, ~, etc.)
          const cleanVersion = version.replace(/^[\^~]/, '');
          
          if (!allDependencies[name]) {
            allDependencies[name] = [];
          }
          
          allDependencies[name].push({
            file: filePath,
            version: cleanVersion,
            isDev: true
          });
        });
      }
    } catch (error) {
      console.error(`Error processing ${filePath}:`, error.message);
    }
  });
  
  return allDependencies;
}

/**
 * Check NPM registry for latest version of a package
 */
async function getLatestPackageVersion(packageName) {
  return new Promise((resolve, reject) => {
    https.get(`https://registry.npmjs.org/${packageName}/latest`, (res) => {
      if (res.statusCode === 404) {
        resolve(null); // Package not found
        return;
      }
      
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          const packageInfo = JSON.parse(data);
          resolve(packageInfo.version);
        } catch (e) {
          reject(e);
        }
      });
    }).on('error', (e) => {
      reject(e);
    });
  });
}

/**
 * Compare actual dependencies with target dependencies and get latest versions
 */
async function analyzePackages() {
  console.log(`\n${colors.blue}Analyzing dependencies against March 2025 specifications...${colors.reset}`);
  
  const installedDependencies = getAllDependencies();
  const results = {
    matching: {},
    outdated: {},
    missing: {},
    notSpecified: {}
  };
  
  // Check all target dependencies
  for (const [name, targetVersion] of Object.entries(targetDependencies)) {
    try {
      let latestVersion;
      
      try {
        // Only query npm for priority packages to avoid rate limiting
        if (priorityPackages.includes(name)) {
          latestVersion = await getLatestPackageVersion(name);
          console.log(`  Checking ${colors.cyan}${name}${colors.reset} (Target: ${targetVersion}, Latest: ${latestVersion || 'unknown'})`);
        } else {
          console.log(`  Checking ${colors.cyan}${name}${colors.reset} (Target: ${targetVersion})`);
          latestVersion = targetVersion; // Assume target is latest for non-priority
        }
      } catch (error) {
        console.log(`  ${colors.yellow}⚠️ Couldn't fetch latest version for ${name}${colors.reset}`);
        latestVersion = targetVersion; // Fall back to target version
      }
      
      if (!installedDependencies[name]) {
        // Package is missing
        results.missing[name] = {
          targetVersion,
          latestVersion
        };
      } else {
        // Package is installed, check version
        const instances = installedDependencies[name];
        const versions = [...new Set(instances.map(i => i.version))];
        
        if (versions.length === 1 && versions[0] === targetVersion) {
          // Version matches target
          results.matching[name] = {
            version: versions[0],
            instances
          };
        } else {
          // Version doesn't match target
          results.outdated[name] = {
            currentVersions: versions,
            targetVersion,
            latestVersion,
            instances
          };
        }
        
        // Remove from installed dependencies to track what's not in spec
        delete installedDependencies[name];
      }
    } catch (error) {
      console.error(`Error analyzing ${name}:`, error.message);
    }
  }
  
  // Remaining dependencies are not in target specs
  results.notSpecified = installedDependencies;
  
  return results;
}

/**
 * Generate installation commands based on analysis
 */
function generateInstallCommands(results) {
  const commands = [];
  
  // Handle missing and outdated dependencies
  const toInstall = [];
  
  // Start with priority packages
  const priorityToInstall = priorityPackages
    .filter(name => results.missing[name] || results.outdated[name])
    .map(name => {
      const info = results.missing[name] || results.outdated[name];
      return `${name}@${info.targetVersion}`;
    });
  
  if (priorityToInstall.length > 0) {
    commands.push(`# Install priority packages first (Next.js, React, etc.)`);
    commands.push(`npm install ${priorityToInstall.join(' ')}`);
    commands.push('');
  }
  
  // Group remaining packages by category
  const categories = {
    ui: ['tailwindcss', '@radix-ui/react-primitives', 'framer-motion', 'lucide-react', 'next-themes', 'cmdk'],
    canvas: ['tldraw', 'lexical', '@lexical/react', 'mjml', 'react-email'],
    state: ['@reduxjs/toolkit', 'react-redux', 'zustand', 'swr', '@tanstack/react-query'],
    collaboration: ['yjs', 'y-websocket', 'y-indexeddb', 'socket.io-client'],
    ai: ['@anthropic-ai/sdk', 'openai', '@google/generative-ai', 'ai', '@tensorflow/tfjs'],
    visualization: ['recharts', 'd3'],
    blockchain: ['ethers', '@web3modal/wagmi', '@web3modal/react', '@web3modal/standalone', '@metamask/sdk-react']
  };
  
  // Generate install commands by category
  Object.entries(categories).forEach(([category, packages]) => {
    const categoryPackages = packages
      .filter(name => (results.missing[name] || results.outdated[name]) && !priorityPackages.includes(name))
      .map(name => {
        const info = results.missing[name] || results.outdated[name];
        return `${name}@${info.targetVersion}`;
      });
    
    if (categoryPackages.length > 0) {
      commands.push(`# Install ${category} packages`);
      for (let i = 0; i < categoryPackages.length; i += 5) {
        const chunk = categoryPackages.slice(i, i + 5);
        commands.push(`npm install ${chunk.join(' ')}`);
      }
      commands.push('');
    }
  });
  
  // Add shadcn/ui commands
  commands.push(`# Install shadcn/ui components`);
  commands.push(`npx shadcn-ui@0.6.0 init`);
  commands.push(`npx shadcn-ui@0.6.0 add button card dialog dropdown-menu avatar toast`);
  commands.push('');
  
  return commands.join('\n');
}

/**
 * Generate a detailed report based on analysis
 */
function generateReport(results) {
  const totalPackages = Object.keys(targetDependencies).length;
  const matching = Object.keys(results.matching).length;
  const outdated = Object.keys(results.outdated).length;
  const missing = Object.keys(results.missing).length;
  
  console.log('\n' + '='.repeat(80));
  console.log(`${colors.magenta}MAILY DEPENDENCY ANALYSIS REPORT - MARCH 2025${colors.reset}`);
  console.log('='.repeat(80));
  
  console.log(`\n📊 ${colors.blue}Summary:${colors.reset}`);
  console.log(`  Total target packages: ${totalPackages}`);
  console.log(`  ✅ Matching: ${matching} (${Math.round(matching/totalPackages*100)}%)`);
  console.log(`  ⚠️ Outdated: ${outdated} (${Math.round(outdated/totalPackages*100)}%)`);
  console.log(`  ❌ Missing: ${missing} (${Math.round(missing/totalPackages*100)}%)`);
  
  if (missing > 0) {
    console.log(`\n🔍 ${colors.yellow}Missing packages:${colors.reset}`);
    Object.entries(results.missing).forEach(([name, info]) => {
      console.log(`  • ${name}@${info.targetVersion}`);
    });
  }
  
  if (outdated > 0) {
    console.log(`\n🔄 ${colors.yellow}Outdated packages:${colors.reset}`);
    Object.entries(results.outdated).forEach(([name, info]) => {
      console.log(`  • ${name}: ${info.currentVersions.join(', ')} → ${info.targetVersion}`);
      
      // Show where this package is used
      if (info.instances.length > 1) {
        info.instances.forEach(instance => {
          console.log(`    - ${instance.file}: ${instance.version}`);
        });
      }
    });
  }
  
  // Create update plan
  console.log(`\n📝 ${colors.green}Update Plan:${colors.reset}`);
  console.log(generateInstallCommands(results));
  
  // Create update script
  const scriptPath = 'scripts/update-dependencies.sh';
  fs.writeFileSync(scriptPath, `#!/bin/bash
# Maily Dependency Update Script - Generated ${new Date().toISOString()}
set -e

echo "🚀 Updating Maily dependencies to March 2025 versions..."

${generateInstallCommands(results)}

echo "✅ Dependencies updated successfully!"
`);
  
  fs.chmodSync(scriptPath, '755'); // Make executable
  console.log(`\n📄 ${colors.green}Update script created:${colors.reset} ${scriptPath}`);
  console.log(`   Run with: ./scripts/update-dependencies.sh`);
  
  // Generate markdown report
  const reportPath = 'dependency-report.md';
  let reportContent = `# Maily Dependency Report - ${new Date().toLocaleDateString()}

## Summary
- Total target packages: ${totalPackages}
- ✅ Matching: ${matching} (${Math.round(matching/totalPackages*100)}%)
- ⚠️ Outdated: ${outdated} (${Math.round(outdated/totalPackages*100)}%)
- ❌ Missing: ${missing} (${Math.round(missing/totalPackages*100)}%)

`;

  if (missing > 0) {
    reportContent += `## Missing Packages\n\n`;
    Object.entries(results.missing).forEach(([name, info]) => {
      reportContent += `- ${name}@${info.targetVersion}\n`;
    });
    reportContent += '\n';
  }

  if (outdated > 0) {
    reportContent += `## Outdated Packages\n\n`;
    Object.entries(results.outdated).forEach(([name, info]) => {
      reportContent += `- ${name}: ${info.currentVersions.join(', ')} → ${info.targetVersion}\n`;
    });
    reportContent += '\n';
  }

  reportContent += `## Update Commands\n\n\`\`\`bash\n${generateInstallCommands(results)}\`\`\`\n`;
  
  fs.writeFileSync(reportPath, reportContent);
  console.log(`   Report saved to: ${reportPath}`);
}

/**
 * Main function
 */
async function main() {
  console.log(`${colors.green}🚀 Maily Dependency Checker - March 2025${colors.reset}`);
  
  try {
    const results = await analyzePackages();
    generateReport(results);
  } catch (error) {
    console.error(`${colors.red}❌ Error:${colors.reset}`, error.message);
    process.exit(1);
  }
}

// Run the script
main(); 