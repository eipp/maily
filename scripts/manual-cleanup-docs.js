#!/usr/bin/env node

/**
 * Automated Documentation Cleanup Script
 *
 * This script compares the list of files that should remain (from the consolidation progress document)
 * with the actual files in the docs directory, and moves all other files to an archive directory.
 * with the actual files in the docs directory, and moves all other files to an archive directory.
 *
 * Usage: node scripts/manual-cleanup-docs.js
 */

const fs = require('fs');
const path = require('path');
const util = require('util');
const readdir = util.promisify(fs.readdir);
const readFile = util.promisify(fs.readFile);
const mkdir = util.promisify(fs.mkdir);
const copyFile = util.promisify(fs.copyFile);
const unlink = util.promisify(fs.unlink);
const stat = util.promisify(fs.stat);

// Configuration
const DOCS_DIR = path.join(__dirname, '..', 'docs');
const ARCHIVE_DIR = path.join(DOCS_DIR, 'archive');
const CONSOLIDATION_PROGRESS_FILE = path.join(DOCS_DIR, 'documentation-consolidation-progress.md');

// Files that should remain after consolidation
const FILES_TO_KEEP = [
  'index.md',
  'documentation-consolidation-progress.md',
  'core-guide.md',
  'glossary-and-faq.md',
  'architecture-handbook.md',
  'user-features.md',
  'developer-features.md',
  'implementation-history.md',
  'ai-handbook.md',
  'ai-service-reference.md',
  'infrastructure-handbook.md',
  'operations-runbook.md',
  'security-compliance-handbook.md',
  'frontend-packages.md',
  'backend-packages.md',
  'frontend-apps.md',
  'backend-apps.md',
  'technical-reference.md',
  'design-standards.md',
  'developer-guide.md',
  'testing-guide.md',
  'operational-handbook.md',
  'infrastructure-reference.md',
  'api-reference.md',
  'trust-infrastructure-handbook.md',
  'enhancement-plan.md',
  'integration-guide.md',
  'app-components.md',
  'modernization-roadmap.md',
  'enhancement-tools-reference.md'
];

// Directories to ignore during cleanup
const IGNORE_DIRS = ['archive', 'api', 'postman', 'legal', 'tmp'];

// Report arrays
const archivedFiles = [];
const keptFiles = [];
const errorFiles = [];

/**
 * Archive a file by moving it to the archive directory
 */
async function archiveFile(filePath) {
  try {
    const fullPath = path.join(DOCS_DIR, filePath);
    const archivePath = path.join(ARCHIVE_DIR, filePath);
    const archiveDir = path.dirname(archivePath);

    // Create directory structure in archive if it doesn't exist
    await mkdir(archiveDir, { recursive: true });

    // Move the file to the archive
    await copyFile(fullPath, archivePath);
    await unlink(fullPath);

    console.log(`✅ Archived: ${filePath}`);
    archivedFiles.push(filePath);
    return true;
  } catch (err) {
    if (err.code === 'ENOENT') {
      console.warn(`⚠️ File not found: ${filePath}`);
    } else {
      console.error(`❌ Error archiving ${filePath}:`, err.message);
      errorFiles.push({ path: filePath, error: err.message });
    }
    return false;
  }
}

/**
 * Generate a report of the cleanup process
 */
function generateReport() {
  const timestamp = new Date().toISOString().replace(/:/g, '-').split('.')[0];
  const reportPath = path.join(DOCS_DIR, `auto-cleanup-report-${timestamp}.md`);

  let report = `# Documentation Automated Cleanup Report\n\n`;
  report += `Generated: ${new Date().toLocaleString()}\n\n`;

  report += `## Summary\n\n`;
  report += `- Files kept: ${keptFiles.length}\n`;
  report += `- Files archived: ${archivedFiles.length}\n`;
  report += `- Errors: ${errorFiles.length}\n\n`;

  if (keptFiles.length > 0) {
    report += `## Files Kept\n\n`;
    keptFiles.forEach(file => {
      report += `- \`${file}\`\n`;
    });
    report += '\n';
  }

  if (archivedFiles.length > 0) {
    report += `## Archived Files\n\n`;
    archivedFiles.forEach(file => {
      report += `- \`${file}\`\n`;
    });
    report += '\n';
  }

  if (errorFiles.length > 0) {
    report += `## Error Files\n\n`;
    report += `These files encountered errors during archiving:\n\n`;
    errorFiles.forEach(file => {
      report += `- \`${file.path}\`: ${file.error}\n`;
    });
    report += '\n';
  }

  fs.writeFileSync(reportPath, report);
  console.log(`\nReport generated at: ${reportPath}`);
}

/**
 * Main function
 */
async function main() {
  console.log('Starting automated documentation cleanup...');

  // Create archive directory if it doesn't exist
  try {
    await mkdir(ARCHIVE_DIR, { recursive: true });
    console.log(`Created archive directory: ${ARCHIVE_DIR}`);
  } catch (err) {
    console.error('Error creating archive directory:', err);
    process.exit(1);
  }

  // Get all files in the docs directory
  const allFiles = [];

  async function scanDir(dir) {
    const relativeDirPath = path.relative(DOCS_DIR, dir);
    const entries = await readdir(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      const relativePath = path.join(relativeDirPath, entry.name);

      if (entry.isDirectory()) {
        if (!IGNORE_DIRS.includes(entry.name)) {
          await scanDir(fullPath);
        }
      } else {
        allFiles.push(relativePath);
      }
    }
  }

  await scanDir(DOCS_DIR);

  console.log(`Found ${allFiles.length} files in the docs directory`);

  // Process each file
  for (const file of allFiles) {
    if (FILES_TO_KEEP.includes(file)) {
      console.log(`✅ Keeping: ${file}`);
      keptFiles.push(file);
    } else {
      await archiveFile(file);
    }
  }

  // Generate report
  generateReport();

  console.log(`\nCleanup complete. Archived ${archivedFiles.length} files, kept ${keptFiles.length} files.`);
}

// Run the main function
main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
