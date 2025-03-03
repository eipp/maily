#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Required dependencies
const requiredDeps = {
  'ethers': '^6.7.1',
  '@metamask/sdk-react': '^0.15.0',
  '@web3modal/wagmi': '^5.1.11',
  '@web3modal/react': '^2.7.1',
  '@web3modal/standalone': '^2.4.3'
};

// Path to package.json
const packageJsonPath = path.join(__dirname, '..', 'package.json');

// Check if package.json exists
if (!fs.existsSync(packageJsonPath)) {
  console.error('❌ package.json not found!');
  process.exit(1);
}

// Read package.json
const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
const dependencies = packageJson.dependencies || {};

// Check dependencies
let missingDeps = [];
let outdatedDeps = [];

for (const [dep, version] of Object.entries(requiredDeps)) {
  if (!dependencies[dep]) {
    missingDeps.push(dep);
  } else if (!dependencies[dep].startsWith(version.replace('^', ''))) {
    outdatedDeps.push(`${dep}@${version}`);
  }
}

// Report results
if (missingDeps.length === 0 && outdatedDeps.length === 0) {
  console.log('✅ All Web3 dependencies are correctly installed!');
  process.exit(0);
}

console.log('\n🔍 Web3 Dependencies Check:');

if (missingDeps.length > 0) {
  console.log('\n❌ Missing dependencies:');
  console.log(missingDeps.join('\n'));
}

if (outdatedDeps.length > 0) {
  console.log('\n⚠️ Outdated dependencies:');
  console.log(outdatedDeps.join('\n'));
}

// Suggest installation command
if (missingDeps.length > 0 || outdatedDeps.length > 0) {
  const depsToInstall = [...missingDeps, ...outdatedDeps].map(dep => {
    return dep.includes('@') ? dep : `${dep}@${requiredDeps[dep]}`;
  });
  
  console.log('\n📦 Run the following command to install missing/outdated dependencies:');
  console.log(`npm install ${depsToInstall.join(' ')} --save\n`);
}

process.exit(missingDeps.length > 0 ? 1 : 0); 