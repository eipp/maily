#!/usr/bin/env node

/**
 * This script helps migrate from Next.js Pages Router to App Router.
 * It identifies pages that need to be migrated and provides guidance on the migration process.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Configuration
const PAGES_DIR = path.join(process.cwd(), 'apps/web/pages');
const APP_DIR = path.join(process.cwd(), 'apps/web/app');
const COMPONENTS_DIR = path.join(process.cwd(), 'apps/web/components');

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m',
};

/**
 * Print a colored message to the console
 */
function colorLog(message, color = 'white') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

/**
 * Check if a directory exists
 */
function directoryExists(dirPath) {
  try {
    return fs.statSync(dirPath).isDirectory();
  } catch (err) {
    return false;
  }
}

/**
 * Get all files in a directory recursively
 */
function getFilesRecursively(dir, fileList = []) {
  if (!directoryExists(dir)) return fileList;

  const files = fs.readdirSync(dir);

  files.forEach(file => {
    const filePath = path.join(dir, file);

    if (fs.statSync(filePath).isDirectory()) {
      fileList = getFilesRecursively(filePath, fileList);
    } else {
      fileList.push(filePath);
    }
  });

  return fileList;
}

/**
 * Get all page files from the pages directory
 */
function getPageFiles() {
  if (!directoryExists(PAGES_DIR)) {
    colorLog('Pages directory not found.', 'red');
    return [];
  }

  const allFiles = getFilesRecursively(PAGES_DIR);

  // Filter out non-page files (like _app.js, _document.js, etc.)
  return allFiles.filter(file => {
    const relativePath = path.relative(PAGES_DIR, file);
    return (
      !relativePath.startsWith('_') &&
      !relativePath.includes('/_') &&
      (file.endsWith('.js') || file.endsWith('.jsx') || file.endsWith('.ts') || file.endsWith('.tsx'))
    );
  });
}

/**
 * Get all app router files
 */
function getAppFiles() {
  if (!directoryExists(APP_DIR)) {
    colorLog('App directory not found.', 'red');
    return [];
  }

  return getFilesRecursively(APP_DIR);
}

/**
 * Convert a pages path to an app path
 */
function convertPagePathToAppPath(pagePath) {
  const relativePath = path.relative(PAGES_DIR, pagePath);
  const parsedPath = path.parse(relativePath);
  const isApiRoute = relativePath.startsWith('api/');

  // Handle API routes
  if (isApiRoute) {
    // Handle index files in API routes
    if (parsedPath.name === 'index') {
      return path.join(APP_DIR, parsedPath.dir, 'route' + parsedPath.ext);
    }

    // Handle dynamic routes in API routes
    if (parsedPath.name.startsWith('[') && parsedPath.name.endsWith(']')) {
      return path.join(APP_DIR, parsedPath.dir, parsedPath.name, 'route' + parsedPath.ext);
    }

    // Handle regular API routes
    return path.join(APP_DIR, parsedPath.dir, 'route' + parsedPath.ext);
  }

  // Handle index files
  if (parsedPath.name === 'index') {
    return path.join(APP_DIR, parsedPath.dir, 'page' + parsedPath.ext);
  }

  // Handle dynamic routes
  if (parsedPath.name.startsWith('[') && parsedPath.name.endsWith(']')) {
    return path.join(APP_DIR, parsedPath.dir, parsedPath.name, 'page' + parsedPath.ext);
  }

  // Handle regular pages
  return path.join(APP_DIR, parsedPath.dir, parsedPath.name, 'page' + parsedPath.ext);
}

/**
 * Check if a page has been migrated
 */
function isPageMigrated(pagePath, appFiles) {
  const appPath = convertPagePathToAppPath(pagePath);
  return appFiles.some(file => file === appPath);
}

/**
 * Generate a migration report
 */
function generateMigrationReport() {
  colorLog('Generating migration report...', 'blue');

  const pageFiles = getPageFiles();
  const appFiles = getAppFiles();

  if (pageFiles.length === 0) {
    colorLog('No page files found.', 'yellow');
    return;
  }

  let migratedCount = 0;
  let pendingCount = 0;

  colorLog('\nMigration Status:', 'cyan');
  colorLog('================', 'cyan');

  pageFiles.forEach(pagePath => {
    const relativePath = path.relative(PAGES_DIR, pagePath);
    const migrated = isPageMigrated(pagePath, appFiles);

    if (migrated) {
      colorLog(`✅ ${relativePath}`, 'green');
      migratedCount++;
    } else {
      colorLog(`❌ ${relativePath}`, 'red');
      pendingCount++;
    }
  });

  colorLog('\nSummary:', 'cyan');
  colorLog('========', 'cyan');
  colorLog(`Total pages: ${pageFiles.length}`, 'white');
  colorLog(`Migrated: ${migratedCount}`, 'green');
  colorLog(`Pending: ${pendingCount}`, 'red');

  const progressPercentage = Math.round((migratedCount / pageFiles.length) * 100);
  colorLog(`Migration progress: ${progressPercentage}%`, 'yellow');

  // Print next steps
  if (pendingCount > 0) {
    colorLog('\nNext Steps:', 'cyan');
    colorLog('==========', 'cyan');
    colorLog('1. Identify the highest priority pages to migrate', 'white');
    colorLog('2. Create corresponding files in the app directory', 'white');
    colorLog('3. Update imports and client/server component boundaries', 'white');
    colorLog('4. Test the migrated pages', 'white');
    colorLog('5. Run this script again to track progress', 'white');
  } else {
    colorLog('\nCongratulations! All pages have been migrated to the App Router.', 'green');
  }
}

/**
 * Main function
 */
function main() {
  colorLog('Next.js Pages to App Router Migration Tool', 'magenta');
  colorLog('=========================================', 'magenta');

  // Check if the pages directory exists
  if (!directoryExists(PAGES_DIR)) {
    colorLog('Pages directory not found. Make sure you are running this script from the project root.', 'red');
    process.exit(1);
  }

  // Check if the app directory exists
  if (!directoryExists(APP_DIR)) {
    colorLog('App directory not found. Creating it...', 'yellow');
    fs.mkdirSync(APP_DIR, { recursive: true });
    colorLog('App directory created.', 'green');
  }

  // Generate the migration report
  generateMigrationReport();
}

// Run the script
main();
