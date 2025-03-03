#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Core dependencies to install
const coreDeps = {
  next: '14.2.1',
  react: '18.3.0',
  'react-dom': '18.3.0',
  typescript: '5.4.2',
  tailwindcss: '3.4.1'
};

// Function to install dependencies in a specific workspace
function installDepsInWorkspace(workspacePath) {
  console.log(`\n\n📦 Installing core dependencies in ${workspacePath}...`);
  
  // Read the package.json
  const packageJsonPath = path.join(workspacePath, 'package.json');
  if (!fs.existsSync(packageJsonPath)) {
    console.log(`⚠️ No package.json found in ${workspacePath}, skipping.`);
    return;
  }
  
  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
  
  // Check which core dependencies are needed in this workspace
  const depsToInstall = [];
  for (const [dep, version] of Object.entries(coreDeps)) {
    if (packageJson.dependencies && packageJson.dependencies[dep]) {
      depsToInstall.push(`${dep}@${version}`);
    }
  }
  
  if (depsToInstall.length === 0) {
    console.log(`ℹ️ No core dependencies needed in ${workspacePath}, skipping.`);
    return;
  }
  
  // Install the dependencies
  try {
    const command = `cd ${workspacePath} && npm install ${depsToInstall.join(' ')} --force`;
    console.log(`🔄 Running: ${command}`);
    execSync(command, { stdio: 'inherit' });
    console.log(`✅ Successfully installed dependencies in ${workspacePath}`);
  } catch (error) {
    console.error(`❌ Error installing dependencies in ${workspacePath}:`, error.message);
  }
}

// Main function
function main() {
  console.log('🚀 Starting core dependency installation...');
  
  // Install in root
  installDepsInWorkspace('.');
  
  // Install in apps
  const appsDir = path.join('.', 'apps');
  if (fs.existsSync(appsDir)) {
    const apps = fs.readdirSync(appsDir).filter(app => 
      fs.statSync(path.join(appsDir, app)).isDirectory()
    );
    
    for (const app of apps) {
      installDepsInWorkspace(path.join(appsDir, app));
    }
  }
  
  // Install in packages
  const packagesDir = path.join('.', 'packages');
  if (fs.existsSync(packagesDir)) {
    const packages = fs.readdirSync(packagesDir).filter(pkg => 
      fs.statSync(path.join(packagesDir, pkg)).isDirectory()
    );
    
    for (const pkg of packages) {
      installDepsInWorkspace(path.join(packagesDir, pkg));
    }
  }
  
  console.log('\n✨ Core dependency installation completed!');
}

main(); 