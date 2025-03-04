#!/usr/bin/env node

/**
 * Documentation Link Verification Script
 *
 * This script scans all markdown files in the docs directory and verifies:
 * 1. All internal document links point to valid files
 * 2. All heading references (#headings) point to valid headings
 * 3. Flags any broken links or references
 *
 * Usage: node scripts/verify-doc-links.js
 */

const fs = require('fs');
const path = require('path');
const util = require('util');
const readdir = util.promisify(fs.readdir);
const readFile = util.promisify(fs.readFile);
const stat = util.promisify(fs.stat);

// Configurations
const DOCS_DIR = path.join(__dirname, '..', 'docs');
const VALID_EXTENSIONS = ['.md'];
const INTERNAL_LINK_REGEX = /\[.*?\]\(((?!http).*?\.md)(#.*?)?\)/g;
const HEADING_REGEX = /^#+\s+(.*)/gm;
const ANCHOR_REGEX = /#([a-z0-9-]+)/;

// Results tracking
const results = {
  filesScanned: 0,
  linksVerified: 0,
  brokenFileLinks: [],
  brokenHeadingLinks: [],
  summary: {}
};

/**
 * Converts heading text to GitHub-style anchor
 */
function headingToAnchor(heading) {
  return heading
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-');
}

/**
 * Get all markdown files in a directory (recursive)
 */
async function getMarkdownFiles(dir) {
  const files = [];
  const entries = await readdir(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      files.push(...await getMarkdownFiles(fullPath));
    } else if (
      entry.isFile() &&
      VALID_EXTENSIONS.includes(path.extname(entry.name).toLowerCase())
    ) {
      files.push(fullPath);
    }
  }

  return files;
}

/**
 * Extract all headings from a markdown file
 */
async function extractHeadings(filePath) {
  const content = await readFile(filePath, 'utf8');
  const headings = [];
  let match;

  while ((match = HEADING_REGEX.exec(content)) !== null) {
    const headingText = match[1].trim();
    headings.push({
      text: headingText,
      anchor: headingToAnchor(headingText)
    });
  }

  return headings;
}

/**
 * Verify links in a single markdown file
 */
async function verifyFileLinks(filePath, allFiles, headingsCache) {
  const content = await readFile(filePath, 'utf8');
  const brokenLinks = [];
  const fileDir = path.dirname(filePath);
  let match;

  // Reset regex state
  INTERNAL_LINK_REGEX.lastIndex = 0;

  while ((match = INTERNAL_LINK_REGEX.exec(content)) !== null) {
    results.linksVerified++;

    const [fullMatch, linkPath, anchorPart] = match;
    const targetPath = path.resolve(fileDir, linkPath);
    const relativeTargetPath = path.relative(DOCS_DIR, targetPath);

    // Check if the linked file exists
    try {
      await stat(targetPath);

      // If there's an anchor part, verify the heading exists
      if (anchorPart) {
        const anchorMatch = ANCHOR_REGEX.exec(anchorPart);
        if (anchorMatch) {
          const targetAnchor = anchorMatch[1];

          // Load headings for the target file if not cached
          if (!headingsCache[targetPath]) {
            headingsCache[targetPath] = await extractHeadings(targetPath);
          }

          // Check if anchor exists in headings
          const headingExists = headingsCache[targetPath].some(h => h.anchor === targetAnchor);

          if (!headingExists) {
            results.brokenHeadingLinks.push({
              file: path.relative(DOCS_DIR, filePath),
              link: fullMatch,
              target: `${relativeTargetPath}${anchorPart}`,
              reason: `Heading with anchor '${targetAnchor}' not found in target file`
            });
          }
        }
      }
    } catch (err) {
      results.brokenFileLinks.push({
        file: path.relative(DOCS_DIR, filePath),
        link: fullMatch,
        target: relativeTargetPath,
        reason: 'Target file does not exist'
      });
    }
  }

  return brokenLinks;
}

/**
 * Main function
 */
async function main() {
  console.log('Starting documentation link verification...');

  // Get all markdown files
  const files = await getMarkdownFiles(DOCS_DIR);
  results.filesScanned = files.length;

  console.log(`Found ${files.length} markdown files to scan`);

  // Cache for headings to avoid reading files multiple times
  const headingsCache = {};

  // Verify each file
  for (const file of files) {
    await verifyFileLinks(file, files, headingsCache);
  }

  // Generate summary
  results.summary = {
    totalFiles: results.filesScanned,
    totalLinks: results.linksVerified,
    brokenFileLinks: results.brokenFileLinks.length,
    brokenHeadingLinks: results.brokenHeadingLinks.length,
    totalIssues: results.brokenFileLinks.length + results.brokenHeadingLinks.length
  };

  // Display results
  console.log('\n--- VERIFICATION COMPLETE ---');
  console.log(`Files scanned: ${results.filesScanned}`);
  console.log(`Links verified: ${results.linksVerified}`);
  console.log(`Broken file links: ${results.brokenFileLinks.length}`);
  console.log(`Broken heading links: ${results.brokenHeadingLinks.length}`);

  if (results.brokenFileLinks.length > 0) {
    console.log('\n--- BROKEN FILE LINKS ---');
    results.brokenFileLinks.forEach(link => {
      console.log(`In ${link.file}:`);
      console.log(`  ${link.link} -> ${link.target}`);
      console.log(`  Reason: ${link.reason}`);
    });
  }

  if (results.brokenHeadingLinks.length > 0) {
    console.log('\n--- BROKEN HEADING LINKS ---');
    results.brokenHeadingLinks.forEach(link => {
      console.log(`In ${link.file}:`);
      console.log(`  ${link.link} -> ${link.target}`);
      console.log(`  Reason: ${link.reason}`);
    });
  }

  console.log('\n--- SUMMARY ---');
  console.log(JSON.stringify(results.summary, null, 2));

  // Exit with error code if issues found
  process.exit(results.summary.totalIssues > 0 ? 1 : 0);
}

// Run the main function
main().catch(err => {
  console.error('Error running verification:', err);
  process.exit(1);
});
