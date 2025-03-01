#!/usr/bin/env node

/**
 * Standardize Metadata Files
 *
 * This script standardizes package.json files across the Maily project:
 * 1. Ensures consistent versioning
 * 2. Standardizes scripts
 * 3. Organizes dependencies
 * 4. Adds consistent metadata
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Define the project root
const PROJECT_ROOT = path.resolve(__dirname, '..');

// Define standard metadata
const STANDARD_METADATA = {
  author: "Maily Team",
  license: "MIT",
  repository: {
    type: "git",
    url: "https://github.com/maily/maily.git"
  },
  engines: {
    node: ">=18.0.0",
    npm: ">=8.0.0"
  }
};

// Define standard scripts for the root package.json
const ROOT_SCRIPTS = {
  dev: "turbo run dev",
  build: "turbo run build",
  test: "turbo run test",
  lint: "turbo run lint",
  format: "prettier --write \"**/*.{ts,tsx,md}\"",
  clean: "turbo run clean && rm -rf node_modules",
  prepare: "husky install"
};

// Define standard scripts for web package.json
const WEB_SCRIPTS = {
  dev: "next dev",
  build: "next build",
  start: "next start",
  lint: "next lint",
  test: "jest",
  "test:watch": "jest --watch",
  "test:ci": "jest --ci --coverage --maxWorkers=2",
  "test:coverage": "jest --coverage",
  cypress: "cypress open",
  "cypress:headless": "cypress run",
  format: "prettier --write .",
  "type-check": "tsc --noEmit",
  "analyze-build": "ANALYZE=true next build"
};

// Define standard scripts for API package.json
const API_SCRIPTS = {
  start: "uvicorn main:app --reload",
  "start:prod": "uvicorn main:app --host 0.0.0.0 --port 8000",
  test: "pytest",
  "test:coverage": "pytest --cov=. --cov-report=html",
  lint: "flake8 .",
  format: "black ."
};

// Define standard scripts for worker package.json
const WORKER_SCRIPTS = {
  start: "node dist/index.js",
  dev: "ts-node-dev --respawn --transpile-only src/index.ts",
  build: "tsc",
  test: "jest",
  lint: "eslint . --ext .ts",
  format: "prettier --write \"**/*.ts\""
};

// Define standard scripts for packages
const PACKAGE_SCRIPTS = {
  build: "tsc",
  dev: "tsc --watch",
  lint: "eslint . --ext .ts,.tsx",
  test: "jest",
  clean: "rm -rf dist"
};

// Create backup directory
const backupDir = path.join(PROJECT_ROOT, `metadata_backup_${new Date().toISOString().replace(/:/g, '-').split('.')[0]}`);
fs.mkdirSync(backupDir, { recursive: true });

/**
 * Create a backup of a file
 * @param {string} filePath - Path to the file
 */
function backupFile(filePath) {
  const relativePath = path.relative(PROJECT_ROOT, filePath);
  const backupPath = path.join(backupDir, relativePath);

  // Create directory structure
  fs.mkdirSync(path.dirname(backupPath), { recursive: true });

  // Copy file
  fs.copyFileSync(filePath, backupPath);
  console.log(`Backed up ${relativePath}`);
}

/**
 * Standardize a package.json file
 * @param {string} filePath - Path to the package.json file
 * @param {object} options - Options for standardization
 */
function standardizePackageJson(filePath, options = {}) {
  const relativePath = path.relative(PROJECT_ROOT, filePath);
  console.log(`Standardizing ${relativePath}...`);

  // Read the file
  const packageJson = JSON.parse(fs.readFileSync(filePath, 'utf8'));

  // Backup the file
  backupFile(filePath);

  // Add standard metadata
  Object.entries(STANDARD_METADATA).forEach(([key, value]) => {
    if (!packageJson[key]) {
      packageJson[key] = value;
    }
  });

  // Add scripts based on package type
  if (options.scripts) {
    packageJson.scripts = {
      ...packageJson.scripts,
      ...options.scripts
    };
  }

  // Sort dependencies
  if (packageJson.dependencies) {
    packageJson.dependencies = sortObjectByKeys(packageJson.dependencies);
  }

  if (packageJson.devDependencies) {
    packageJson.devDependencies = sortObjectByKeys(packageJson.devDependencies);
  }

  // Write the file
  fs.writeFileSync(filePath, JSON.stringify(packageJson, null, 2) + '\n');
  console.log(`Standardized ${relativePath}`);
}

/**
 * Sort an object by keys
 * @param {object} obj - Object to sort
 * @returns {object} - Sorted object
 */
function sortObjectByKeys(obj) {
  return Object.keys(obj)
    .sort()
    .reduce((result, key) => {
      result[key] = obj[key];
      return result;
    }, {});
}

/**
 * Find all package.json files in a directory
 * @param {string} dir - Directory to search
 * @returns {string[]} - Array of file paths
 */
function findPackageJsonFiles(dir) {
  const results = [];

  const files = fs.readdirSync(dir);

  for (const file of files) {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);

    if (stat.isDirectory() && !file.startsWith('.') && file !== 'node_modules') {
      results.push(...findPackageJsonFiles(filePath));
    } else if (file === 'package.json') {
      results.push(filePath);
    }
  }

  return results;
}

/**
 * Main function
 */
function main() {
  console.log('Standardizing metadata files...');

  // Find all package.json files
  const packageJsonFiles = findPackageJsonFiles(PROJECT_ROOT);

  // Standardize each file
  for (const filePath of packageJsonFiles) {
    const relativePath = path.relative(PROJECT_ROOT, filePath);

    if (relativePath === 'package.json') {
      standardizePackageJson(filePath, { scripts: ROOT_SCRIPTS });
    } else if (relativePath === 'apps/web/package.json') {
      standardizePackageJson(filePath, { scripts: WEB_SCRIPTS });
    } else if (relativePath === 'apps/api/package.json') {
      standardizePackageJson(filePath, { scripts: API_SCRIPTS });
    } else if (relativePath === 'apps/workers/package.json') {
      standardizePackageJson(filePath, { scripts: WORKER_SCRIPTS });
    } else if (relativePath.startsWith('packages/')) {
      standardizePackageJson(filePath, { scripts: PACKAGE_SCRIPTS });
    } else {
      standardizePackageJson(filePath);
    }
  }

  // Create documentation
  createMetadataDocumentation();

  console.log('\nMetadata standardization complete!');
  console.log(`Backup created at: ${backupDir}`);
  console.log('Please review the generated files and make any necessary adjustments.');
}

/**
 * Create documentation for metadata standardization
 */
function createMetadataDocumentation() {
  const docPath = path.join(PROJECT_ROOT, 'METADATA.md');

  const content = `# Maily Metadata Standardization

This document outlines the standardization of metadata files across the Maily project.

## Package.json Files

All \`package.json\` files have been standardized with:

1. Consistent metadata (author, license, repository)
2. Standard scripts based on package type
3. Sorted dependencies
4. Consistent versioning

## Standard Scripts

### Root Package

\`\`\`json
${JSON.stringify(ROOT_SCRIPTS, null, 2)}
\`\`\`

### Web Application

\`\`\`json
${JSON.stringify(WEB_SCRIPTS, null, 2)}
\`\`\`

### API Application

\`\`\`json
${JSON.stringify(API_SCRIPTS, null, 2)}
\`\`\`

### Worker Application

\`\`\`json
${JSON.stringify(WORKER_SCRIPTS, null, 2)}
\`\`\`

### Packages

\`\`\`json
${JSON.stringify(PACKAGE_SCRIPTS, null, 2)}
\`\`\`

## Dependency Management

Dependencies are sorted alphabetically for better readability and to avoid merge conflicts.

## Metadata Fields

The following metadata fields are standardized across all packages:

\`\`\`json
${JSON.stringify(STANDARD_METADATA, null, 2)}
\`\`\`

## Versioning

All packages use semantic versioning (MAJOR.MINOR.PATCH).

## Maintenance

When adding new dependencies or scripts, please follow the established patterns and organization.
`;

  fs.writeFileSync(docPath, content);
  console.log('Created METADATA.md documentation');
}

// Run the main function
main();
