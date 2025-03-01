#!/usr/bin/env node

/**
 * Architectural Decision Records (ADR) Management Tool
 *
 * This script provides a command-line interface for managing Architectural Decision Records.
 * ADRs are lightweight documents that capture important architectural decisions, along with
 * their context and consequences.
 *
 * Features:
 * - Create new ADRs from templates
 * - List existing ADRs
 * - Update ADR status (proposed, accepted, rejected, deprecated, superseded)
 * - Generate index and navigation for MkDocs
 * - Link related ADRs
 *
 * Usage:
 * - Create new ADR: node scripts/adr.js new "Title of Decision"
 * - List ADRs: node scripts/adr.js list
 * - Update ADR status: node scripts/adr.js status 0001-example-decision.md accepted
 * - Generate index: node scripts/adr.js index
 */

const fs = require('fs');
const path = require('path');
const util = require('util');
const yaml = require('js-yaml');
const readline = require('readline');

// Convert callbacks to promises
const readFile = util.promisify(fs.readFile);
const writeFile = util.promisify(fs.writeFile);
const readdir = util.promisify(fs.readdir);
const mkdir = util.promisify(fs.mkdir);
const stat = util.promisify(fs.stat);

// Configuration
const REPO_ROOT = path.resolve(__dirname, '..');
const ADR_DIR = path.join(REPO_ROOT, 'docs', 'architecture', 'decisions');
const TEMPLATE_PATH = path.join(__dirname, 'adr-template.md');
const MKDOCS_PATH = path.join(REPO_ROOT, 'mkdocs.yml');
const ADR_INDEX_PATH = path.join(REPO_ROOT, 'docs', 'architecture', 'index.md');

// ADR statuses
const ADR_STATUSES = ['proposed', 'accepted', 'rejected', 'deprecated', 'superseded'];

// Create readline interface for user input
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

/**
 * Ask a question and get user input
 */
function question(query) {
  return new Promise(resolve => rl.question(query, resolve));
}

/**
 * Pad a number with leading zeros
 */
function padNumber(num, size) {
  return String(num).padStart(size, '0');
}

/**
 * Convert a title to a filename-friendly format
 */
function titleToFilename(title) {
  return title
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-');
}

/**
 * Create a new ADR
 */
async function createAdr(title) {
  try {
    // Create ADR directory if it doesn't exist
    await mkdir(ADR_DIR, { recursive: true });

    // Get existing ADRs to determine next number
    const existingAdrs = await readdir(ADR_DIR);
    const adrFiles = existingAdrs.filter(file => file.match(/^\d{4}-.*\.md$/));

    // Determine the next ADR number
    let nextNumber = 1;
    if (adrFiles.length > 0) {
      // Extract numbers from filenames and find the highest
      const numbers = adrFiles
        .map(file => parseInt(file.substring(0, 4), 10))
        .filter(num => !isNaN(num));

      if (numbers.length > 0) {
        nextNumber = Math.max(...numbers) + 1;
      }
    }

    // Format the ADR number with leading zeros
    const adrNumber = padNumber(nextNumber, 4);

    // Format the filename
    const filename = `${adrNumber}-${titleToFilename(title)}.md`;
    const filePath = path.join(ADR_DIR, filename);

    // Check if template exists, create it if not
    if (!fs.existsSync(TEMPLATE_PATH)) {
      console.log('ADR template not found, creating default template...');
      await createDefaultTemplate();
    }

    // Read template and replace placeholders
    let template = await readFile(TEMPLATE_PATH, 'utf8');
    template = template
      .replace(/\{NUMBER\}/g, adrNumber)
      .replace(/\{TITLE\}/g, title)
      .replace(/\{DATE\}/g, new Date().toISOString().split('T')[0]);

    // Write the new ADR
    await writeFile(filePath, template);

    console.log(`ADR created successfully: ${filePath}`);
    console.log('Edit the file to document your architectural decision.');

    // Update the ADR index
    await generateAdrIndex();

    // Update MkDocs configuration
    await updateMkDocsConfig();

    return filePath;
  } catch (error) {
    console.error(`Error creating ADR: ${error.message}`);
    throw error;
  }
}

/**
 * Create a default ADR template
 */
async function createDefaultTemplate() {
  const templateContent = `# {NUMBER}. {TITLE}

Date: {DATE}

## Status

Proposed

## Context

What is the issue that we're seeing that is motivating this decision or change?

## Decision

What is the change that we're proposing and/or doing?

## Consequences

What becomes easier or more difficult to do because of this change?

## Related ADRs

- [ADR-XXXX](xxxx-example.md)
`;

  const templateDir = path.dirname(TEMPLATE_PATH);
  await mkdir(templateDir, { recursive: true });
  await writeFile(TEMPLATE_PATH, templateContent);

  console.log(`Default ADR template created at: ${TEMPLATE_PATH}`);
}

/**
 * List all existing ADRs
 */
async function listAdrs() {
  try {
    // Create ADR directory if it doesn't exist
    await mkdir(ADR_DIR, { recursive: true });

    // Get existing ADRs
    const files = await readdir(ADR_DIR);
    const adrFiles = files.filter(file => file.match(/^\d{4}-.*\.md$/));

    if (adrFiles.length === 0) {
      console.log('No ADRs found.');
      return [];
    }

    console.log('\nExisting Architectural Decision Records:');
    console.log('=======================================\n');

    const adrs = [];

    // Process each ADR
    for (const file of adrFiles) {
      const filePath = path.join(ADR_DIR, file);
      const content = await readFile(filePath, 'utf8');

      // Extract title and status
      const titleMatch = content.match(/# \d+\. (.*)/);
      const statusMatch = content.match(/## Status\s*\n\s*(.*)/);

      const title = titleMatch ? titleMatch[1].trim() : 'Unknown Title';
      const status = statusMatch ? statusMatch[1].trim() : 'Unknown Status';

      adrs.push({
        number: file.substring(0, 4),
        title,
        status,
        file
      });

      console.log(`${file.substring(0, 4)}: ${title} (${status})`);
    }

    return adrs;
  } catch (error) {
    console.error(`Error listing ADRs: ${error.message}`);
    return [];
  }
}

/**
 * Update the status of an ADR
 */
async function updateAdrStatus(filename, newStatus) {
  try {
    if (!ADR_STATUSES.includes(newStatus.toLowerCase())) {
      console.error(`Invalid status: ${newStatus}`);
      console.error(`Valid statuses are: ${ADR_STATUSES.join(', ')}`);
      return false;
    }

    const filePath = path.join(ADR_DIR, filename);

    if (!fs.existsSync(filePath)) {
      console.error(`ADR file not found: ${filePath}`);
      return false;
    }

    // Read the ADR content
    let content = await readFile(filePath, 'utf8');

    // Replace the status
    content = content.replace(
      /(## Status\s*\n\s*)(.*)/,
      `$1${newStatus.charAt(0).toUpperCase() + newStatus.slice(1)}`
    );

    // Write the updated content
    await writeFile(filePath, content);

    console.log(`Status updated to "${newStatus}" for ${filename}`);
    return true;
  } catch (error) {
    console.error(`Error updating ADR status: ${error.message}`);
    return false;
  }
}

/**
 * Generate an index of all ADRs
 */
async function generateAdrIndex() {
  try {
    // Create architecture directory if it doesn't exist
    await mkdir(path.dirname(ADR_INDEX_PATH), { recursive: true });

    // Get list of ADRs
    const adrs = await listAdrs();

    // Generate index content
    let indexContent = `# Architectural Decision Records\n\n`;
    indexContent += `This directory contains Architectural Decision Records (ADRs) for the Maily project.\n\n`;
    indexContent += `ADRs are used to document architectural decisions: the context, what was decided, and the consequences.\n\n`;

    indexContent += `## Decision Log\n\n`;
    indexContent += `| Number | Title | Status | Date |\n`;
    indexContent += `|--------|-------|--------|------|\n`;

    // Process each ADR for the table
    for (const adr of adrs) {
      const filePath = path.join(ADR_DIR, adr.file);
      const content = await readFile(filePath, 'utf8');

      // Extract date
      const dateMatch = content.match(/Date: (.*)/);
      const date = dateMatch ? dateMatch[1].trim() : 'Unknown';

      indexContent += `| [${adr.number}](decisions/${adr.file}) | ${adr.title} | ${adr.status} | ${date} |\n`;
    }

    // Add information about statuses
    indexContent += `\n## ADR Statuses\n\n`;
    indexContent += `- **Proposed**: The ADR is being considered but hasn't been approved yet.\n`;
    indexContent += `- **Accepted**: The ADR has been accepted and represents the current architecture decision.\n`;
    indexContent += `- **Rejected**: The ADR was not accepted.\n`;
    indexContent += `- **Deprecated**: The ADR was once accepted but is no longer relevant.\n`;
    indexContent += `- **Superseded**: The ADR has been replaced by a newer ADR.\n`;

    // Add information about creating new ADRs
    indexContent += `\n## Creating a New ADR\n\n`;
    indexContent += `To create a new ADR, run:\n\n`;
    indexContent += `\`\`\`bash\n`;
    indexContent += `node scripts/adr.js new "Title of Decision"\n`;
    indexContent += `\`\`\`\n`;

    // Write the index file
    await writeFile(ADR_INDEX_PATH, indexContent);

    console.log(`ADR index generated at: ${ADR_INDEX_PATH}`);
    return true;
  } catch (error) {
    console.error(`Error generating ADR index: ${error.message}`);
    return false;
  }
}

/**
 * Update MkDocs configuration to include ADRs
 */
async function updateMkDocsConfig() {
  try {
    // Read the existing mkdocs.yml
    const mkdocsContent = await readFile(MKDOCS_PATH, 'utf8');
    const mkdocs = yaml.load(mkdocsContent);

    // Find the Platform Documentation section
    const platformDocIndex = mkdocs.nav.findIndex(item =>
      typeof item === 'object' && Object.keys(item)[0] === 'Platform Documentation'
    );

    if (platformDocIndex === -1) {
      console.error('Could not find "Platform Documentation" section in mkdocs.yml');
      return false;
    }

    // Get the Platform Documentation section
    const platformDoc = mkdocs.nav[platformDocIndex]['Platform Documentation'];

    // Check if Architecture section already exists
    let archIndex = -1;
    let archItem = null;

    for (let i = 0; i < platformDoc.length; i++) {
      const item = platformDoc[i];
      if (typeof item === 'object' && Object.keys(item)[0] === 'Architecture') {
        archIndex = i;
        archItem = item;
        break;
      }
    }

    // Create Architecture section if it doesn't exist
    if (archIndex === -1) {
      archItem = {
        'Architecture': 'architecture/index.md'
      };
      platformDoc.push(archItem);
    } else {
      // Check if it's a simple string or an object with subsections
      if (typeof archItem['Architecture'] === 'string') {
        archItem['Architecture'] = {
          'Overview': archItem['Architecture'],
          'Decisions': 'architecture/index.md'
        };
      } else if (typeof archItem['Architecture'] === 'object') {
        archItem['Architecture']['Decisions'] = 'architecture/index.md';
      }
    }

    // Write updated config
    await writeFile(
      MKDOCS_PATH,
      yaml.dump(mkdocs, { lineWidth: 100, noRefs: true })
    );

    console.log(`Updated MkDocs configuration at ${MKDOCS_PATH}`);
    return true;
  } catch (error) {
    console.error(`Error updating MkDocs config: ${error.message}`);
    return false;
  }
}

/**
 * Main function
 */
async function main() {
  try {
    const command = process.argv[2];

    if (!command) {
      console.log('Usage:');
      console.log('  node scripts/adr.js new "Title of Decision"');
      console.log('  node scripts/adr.js list');
      console.log('  node scripts/adr.js status 0001-example-decision.md accepted');
      console.log('  node scripts/adr.js index');
      rl.close();
      return;
    }

    switch (command.toLowerCase()) {
      case 'new':
        // Create new ADR
        const title = process.argv[3];
        if (!title) {
          console.error('Title is required for new ADR');
          console.log('Usage: node scripts/adr.js new "Title of Decision"');
          break;
        }
        await createAdr(title);
        break;

      case 'list':
        // List ADRs
        await listAdrs();
        break;

      case 'status':
        // Update ADR status
        const filename = process.argv[3];
        const newStatus = process.argv[4];

        if (!filename || !newStatus) {
          console.error('Filename and status are required');
          console.log('Usage: node scripts/adr.js status 0001-example-decision.md accepted');
          break;
        }

        await updateAdrStatus(filename, newStatus);
        break;

      case 'index':
        // Generate ADR index
        await generateAdrIndex();
        break;

      default:
        console.error(`Unknown command: ${command}`);
        console.log('Usage:');
        console.log('  node scripts/adr.js new "Title of Decision"');
        console.log('  node scripts/adr.js list');
        console.log('  node scripts/adr.js status 0001-example-decision.md accepted');
        console.log('  node scripts/adr.js index');
    }
  } catch (error) {
    console.error(`Error: ${error.message}`);
  } finally {
    rl.close();
  }
}

// Run the main function
main();
