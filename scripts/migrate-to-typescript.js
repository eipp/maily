#!/usr/bin/env node
/**
 * Automation script for migrating JavaScript files to TypeScript
 * Uses ts-migrate for automated conversion and tracks migration progress
 */
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const glob = require('glob');

// Configuration
const TARGET_DIRS = [
  'apps/web/components/legacy',
  'apps/web/utils',
  'apps/web/pages',
  'packages/utils/src',
  'packages/ui/src'
];
const EXCLUDE_PATTERNS = [
  '**/*.d.ts',
  '**/*.test.*',
  '**/node_modules/**',
  '**/dist/**',
  '**/build/**',
];
const PROGRESS_FILE = path.resolve(__dirname, '../ts-migration-progress.json');

// Initialize migration tracking
let migrationProgress = {
  completed: [],
  failed: [],
  pending: [],
  lastRun: null,
  stats: {
    totalFiles: 0,
    convertedFiles: 0,
    remainingFiles: 0
  }
};

// Load existing progress if available
if (fs.existsSync(PROGRESS_FILE)) {
  try {
    migrationProgress = JSON.parse(fs.readFileSync(PROGRESS_FILE, 'utf8'));
    console.log('Loaded existing migration progress.');
  } catch (e) {
    console.warn('Could not parse existing progress file, starting fresh.');
  }
}

// Find all JavaScript files
const findJsFiles = (targetDirs) => {
  let allFiles = [];

  targetDirs.forEach(dir => {
    const fullDir = path.resolve(process.cwd(), dir);
    if (!fs.existsSync(fullDir)) {
      console.warn(`Directory not found: ${fullDir}`);
      return;
    }

    const files = glob.sync(`${dir}/**/*.{js,jsx}`, {
      ignore: EXCLUDE_PATTERNS,
      cwd: process.cwd()
    });

    allFiles = [...allFiles, ...files];
  });

  return allFiles;
};

// Filter out already processed files
const getFilesToProcess = (allFiles) => {
  const completedSet = new Set(migrationProgress.completed);
  const failedSet = new Set(migrationProgress.failed);

  return allFiles.filter(file => !completedSet.has(file) && !failedSet.has(file));
};

// Check if ts-migrate is installed
const ensureDependencies = () => {
  try {
    execSync('npx ts-migrate --version', { stdio: 'ignore' });
  } catch (e) {
    console.log('Installing ts-migrate...');
    execSync('npm install --save-dev ts-migrate', { stdio: 'inherit' });
  }
};

// Migrate a single file
const migrateFile = (filePath) => {
  const directory = path.dirname(filePath);
  const filename = path.basename(filePath);

  try {
    console.log(`Migrating ${filePath}...`);

    // Create .ts file with same name
    const tsFilePath = filePath.replace(/\.(js|jsx)$/, '.ts$1');

    // Run ts-migrate on the file
    execSync(`npx ts-migrate migrate ${filePath}`, {
      stdio: 'inherit',
      cwd: process.cwd()
    });

    // Add to completed list
    migrationProgress.completed.push(filePath);
    console.log(`✅ Successfully migrated ${filePath}`);
    return true;
  } catch (error) {
    console.error(`❌ Failed to migrate ${filePath}:`, error.message);
    migrationProgress.failed.push(filePath);
    return false;
  }
};

// Update the migration stats
const updateStats = (allFiles) => {
  migrationProgress.stats.totalFiles = allFiles.length;
  migrationProgress.stats.convertedFiles = migrationProgress.completed.length;
  migrationProgress.stats.remainingFiles = allFiles.length - migrationProgress.completed.length;
  migrationProgress.lastRun = new Date().toISOString();
};

// Save progress to file
const saveProgress = () => {
  fs.writeFileSync(PROGRESS_FILE, JSON.stringify(migrationProgress, null, 2));
  console.log(`Migration progress saved to ${PROGRESS_FILE}`);
};

// Main execution
const run = async () => {
  console.log('Maily TypeScript Migration Tool');
  console.log('------------------------------');

  ensureDependencies();

  const allJsFiles = findJsFiles(TARGET_DIRS);
  console.log(`Found ${allJsFiles.length} JavaScript files total.`);

  const filesToProcess = getFilesToProcess(allJsFiles);
  console.log(`${filesToProcess.length} files remaining to be processed.`);

  if (filesToProcess.length === 0) {
    console.log('All files have been processed. Migration complete! 🎉');
    return;
  }

  migrationProgress.pending = filesToProcess;

  let successCount = 0;
  let failCount = 0;

  // Process files in batches to avoid overwhelming the system
  const BATCH_SIZE = 5;
  for (let i = 0; i < filesToProcess.length; i += BATCH_SIZE) {
    const batch = filesToProcess.slice(i, i + BATCH_SIZE);

    console.log(`\nProcessing batch ${Math.floor(i/BATCH_SIZE) + 1} of ${Math.ceil(filesToProcess.length/BATCH_SIZE)}...`);

    for (const file of batch) {
      const success = migrateFile(file);
      if (success) {
        successCount++;
      } else {
        failCount++;
      }

      // Update progress after each file in case of interruption
      updateStats(allJsFiles);
      saveProgress();
    }
  }

  console.log('\nMigration Summary:');
  console.log(`✅ Successfully migrated: ${successCount} files`);
  console.log(`❌ Failed to migrate: ${failCount} files`);
  console.log(`⏸ Remaining files: ${migrationProgress.stats.remainingFiles}`);

  if (migrationProgress.failed.length > 0) {
    console.log('\nFailed files (may require manual migration):');
    migrationProgress.failed.forEach(file => console.log(`- ${file}`));
  }
};

// Execute
run().catch(error => {
  console.error('Migration failed:', error);
  process.exit(1);
});
