#!/usr/bin/env node

/**
 * Documentation Cleanup Script
 *
 * This script reads the files-to-remove list from documentation-consolidation-progress.md
 * and moves those files to an archive directory instead of deleting them.
 *
 * Usage: node scripts/cleanup-docs.js
 */

const fs = require('fs');
const path = require('path');
const util = require('util');
const readFile = util.promisify(fs.readFile);
const mkdir = util.promisify(fs.mkdir);
const copyFile = util.promisify(fs.copyFile);
const stat = util.promisify(fs.stat);

// Configuration
const DOCS_DIR = path.join(__dirname, '..', 'docs');
const ARCHIVE_DIR = path.join(DOCS_DIR, 'archive');
const CONSOLIDATION_PROGRESS_FILE = path.join(DOCS_DIR, 'documentation-consolidation-progress.md');

// Files that have been moved successfully
const movedFiles = [];
// Files that were supposed to be moved but weren't found
const missingFiles = [];
// Files that couldn't be moved due to errors
const errorFiles = [];

/**
 * Extract files to remove from the consolidation progress document
 */
async function getFilesToRemove() {
  try {
    const content = await readFile(CONSOLIDATION_PROGRESS_FILE, 'utf8');

    // Find the "Files to be Removed" or "Files Removed and Archived" section
    let filesToRemoveSection = content.match(/## Files to be Removed\s+([\s\S]+?)(?=##|$)/);

    if (!filesToRemoveSection) {
      filesToRemoveSection = content.match(/### Files Removed and Archived\s+([\s\S]+?)(?=###|$)/);
    }

    if (!filesToRemoveSection) {
      throw new Error('Could not find "Files to be Removed" or "Files Removed and Archived" section in the consolidation progress document');
    }

    // Extract file paths
    const filePathsRegex = /- `([^`]+)`/g;
    const filesToRemove = [];
    let match;

    while ((match = filePathsRegex.exec(filesToRemoveSection[1])) !== null) {
      filesToRemove.push(match[1]);
    }

    // Also extract file paths from list under section headings
    const sectionRegex = /### .+?\n([\s\S]+?)(?=###|$)/g;
    let sectionMatch;

    while ((sectionMatch = sectionRegex.exec(filesToRemoveSection[1])) !== null) {
      const sectionContent = sectionMatch[1];
      let fileMatch;

      while ((fileMatch = filePathsRegex.exec(sectionContent)) !== null) {
        filesToRemove.push(fileMatch[1]);
      }
    }

    return filesToRemove;
  } catch (err) {
    console.error('Error extracting files to remove:', err);
    return [];
  }
}

/**
 * Archive a file
 */
async function archiveFile(filePath) {
  const fullPath = path.join(DOCS_DIR, filePath);
  const archivePath = path.join(ARCHIVE_DIR, filePath);
  const archiveDir = path.dirname(archivePath);

  try {
    // Check if the file exists
    await stat(fullPath);

    // Create archive directory if it doesn't exist
    await mkdir(archiveDir, { recursive: true });

    // Copy file to archive
    await copyFile(fullPath, archivePath);

    console.log(`✅ Archived: ${filePath}`);
    movedFiles.push(filePath);

    return true;
  } catch (err) {
    if (err.code === 'ENOENT') {
      console.log(`⚠️ File not found: ${filePath}`);
      missingFiles.push(filePath);
    } else {
      console.error(`❌ Error archiving ${filePath}:`, err);
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
  const reportPath = path.join(DOCS_DIR, `cleanup-report-${timestamp}.md`);

  let report = `# Documentation Cleanup Report\n\n`;
  report += `Generated: ${new Date().toLocaleString()}\n\n`;

  report += `## Summary\n\n`;
  report += `- Total files processed: ${movedFiles.length + missingFiles.length + errorFiles.length}\n`;
  report += `- Successfully archived: ${movedFiles.length}\n`;
  report += `- Missing files: ${missingFiles.length}\n`;
  report += `- Errors: ${errorFiles.length}\n\n`;

  if (movedFiles.length > 0) {
    report += `## Successfully Archived Files\n\n`;
    movedFiles.forEach(file => {
      report += `- \`${file}\`\n`;
    });
    report += '\n';
  }

  if (missingFiles.length > 0) {
    report += `## Missing Files\n\n`;
    report += `These files were listed for removal but could not be found:\n\n`;
    missingFiles.forEach(file => {
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

  report += `## Next Steps\n\n`;
  report += `1. Verify that all consolidated content is properly included in the new consolidated files\n`;
  report += `2. Run the cross-reference verification script to ensure all links are working\n`;
  report += `3. Update the documentation portal with the new file structure\n`;
  report += `4. After confirming everything works correctly, the archived files can be removed completely\n`;

  fs.writeFileSync(reportPath, report);
  console.log(`\nReport generated at: ${reportPath}`);
}

/**
 * Main function
 */
async function main() {
  console.log('Starting documentation cleanup...');

  // Create archive directory if it doesn't exist
  try {
    await mkdir(ARCHIVE_DIR, { recursive: true });
    console.log(`Created archive directory: ${ARCHIVE_DIR}`);
  } catch (err) {
    console.error('Error creating archive directory:', err);
    process.exit(1);
  }

  // Get files to remove
  const filesToRemove = await getFilesToRemove();

  if (filesToRemove.length === 0) {
    console.log('No files to remove found in the consolidation progress document');
    process.exit(0);
  }

  console.log(`Found ${filesToRemove.length} files to archive`);

  // Archive each file
  for (const file of filesToRemove) {
    await archiveFile(file);
  }

  // Generate report
  generateReport();

  console.log('\nCleanup process completed!');
  console.log(`Successfully archived: ${movedFiles.length}`);
  console.log(`Missing files: ${missingFiles.length}`);
  console.log(`Errors: ${errorFiles.length}`);
}

// Run the main function
main().catch(err => {
  console.error('Error running cleanup:', err);
  process.exit(1);
});
