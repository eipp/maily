#!/usr/bin/env node

/**
 * This script converts Jest test files to Vitest format
 * It updates imports, mocks, and other Jest-specific code
 */

const fs = require('fs');
const path = require('path');
const glob = require('glob');

// Find all Jest test files
const findTestFiles = () => {
  return glob.sync('apps/**/*.test.{js,jsx,ts,tsx}', {
    ignore: ['**/node_modules/**', '**/dist/**', '**/build/**']
  });
};

// Convert Jest file to Vitest format
const convertFile = (filePath) => {
  console.log(`Converting ${filePath}...`);
  
  let content = fs.readFileSync(filePath, 'utf8');
  
  // Replace Jest imports with Vitest imports
  const hasJestImport = content.includes('jest');
  if (hasJestImport) {
    if (!content.includes('import {')) {
      content = content.replace(
        /import (.*) from ['"]@testing-library\/react['"];/,
        'import $1 from \'@testing-library/react\';\nimport { describe, it, expect, beforeEach, afterEach, vi, beforeAll, afterAll } from \'vitest\';'
      );
    } else {
      content = content.replace(
        /import {(.*)} from ['"]@testing-library\/react['"];/,
        'import {$1} from \'@testing-library/react\';\nimport { describe, it, expect, beforeEach, afterEach, vi, beforeAll, afterAll } from \'vitest\';'
      );
    }
  }
  
  // Replace Jest specific methods with Vitest equivalents
  content = content.replace(/jest\.fn/g, 'vi.fn');
  content = content.replace(/jest\.mock/g, 'vi.mock');
  content = content.replace(/jest\.spyOn/g, 'vi.spyOn');
  content = content.replace(/jest\.useFakeTimers/g, 'vi.useFakeTimers');
  content = content.replace(/jest\.useRealTimers/g, 'vi.useRealTimers');
  content = content.replace(/jest\.resetAllMocks/g, 'vi.resetAllMocks');
  content = content.replace(/jest\.clearAllMocks/g, 'vi.clearAllMocks');
  content = content.replace(/jest\.restoreAllMocks/g, 'vi.restoreAllMocks');
  content = content.replace(/jest\.advanceTimersByTime/g, 'vi.advanceTimersByTime');
  content = content.replace(/jest\.runAllTimers/g, 'vi.runAllTimers');
  content = content.replace(/jest\.runOnlyPendingTimers/g, 'vi.runOnlyPendingTimers');
  
  // Write the updated file
  fs.writeFileSync(filePath, content, 'utf8');
  console.log(`Converted ${filePath}`);
};

// Main function
const main = () => {
  const files = findTestFiles();
  
  if (files.length === 0) {
    console.log('No test files found.');
    return;
  }
  
  console.log(`Found ${files.length} test files to convert.`);
  
  files.forEach(convertFile);
  
  console.log('Conversion complete!');
};

main();