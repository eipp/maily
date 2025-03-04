#!/usr/bin/env node

/**
 * Documentation Automation Script
 *
 * This script orchestrates the documentation automation process by running multiple
 * documentation generation tools and validating the result.
 *
 * Features:
 * - Runs API documentation generation from OpenAPI spec
 * - Runs inline code documentation generation from source code comments
 * - Validates documentation links and references
 * - Updates MkDocs navigation and configuration
 * - Creates documentation summary report
 * - Can be run in CI/CD pipeline or locally
 *
 * Usage: node scripts/docs-automation.js [--validate-only] [--report-file=path/to/report.json]
 */

const fs = require('fs');
const path = require('path');
const util = require('util');
const { execSync, spawn } = require('child_process');
const yaml = require('js-yaml');

// Convert callbacks to promises
const readFile = util.promisify(fs.readFile);
const writeFile = util.promisify(fs.writeFile);
const mkdir = util.promisify(fs.mkdir);
const stat = util.promisify(fs.stat);

// Configuration
const REPO_ROOT = path.resolve(__dirname, '..');
const DOCS_DIR = path.join(REPO_ROOT, 'docs');
const MKDOCS_PATH = path.join(REPO_ROOT, 'mkdocs.yml');
const REPORT_PATH = path.join(REPO_ROOT, 'docs-validation-report.json');

// Parse command line arguments
const args = process.argv.slice(2).reduce((acc, arg) => {
  if (arg === '--validate-only') {
    acc.validateOnly = true;
  } else if (arg.startsWith('--report-file=')) {
    acc.reportFile = arg.split('=')[1];
  }
  return acc;
}, { validateOnly: false, reportFile: REPORT_PATH });

// Define colors for console output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

/**
 * Execute a command and return a promise
 */
function execCommand(command, options = {}) {
  const { silent = false, ...otherOptions } = options;

  return new Promise((resolve, reject) => {
    console.log(`${colors.cyan}> ${command}${colors.reset}`);

    const childProcess = spawn('bash', ['-c', command], {
      stdio: silent ? 'ignore' : 'inherit',
      ...otherOptions
    });

    childProcess.on('close', code => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`Command failed with exit code ${code}`));
      }
    });

    childProcess.on('error', error => {
      reject(error);
    });
  });
}

/**
 * Log a message with timestamp
 */
function log(message, type = 'info') {
  const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
  let color;

  switch (type) {
    case 'success':
      color = colors.green;
      break;
    case 'error':
      color = colors.red;
      break;
    case 'warning':
      color = colors.yellow;
      break;
    case 'section':
      color = colors.magenta + colors.bright;
      message = `\n${message}\n${'-'.repeat(message.length)}`;
      break;
    default:
      color = colors.reset;
  }

  console.log(`${colors.dim}[${timestamp}]${colors.reset} ${color}${message}${colors.reset}`);
}

/**
 * Ensure required directories exist
 */
async function ensureDirectories() {
  log('Ensuring required directories exist', 'section');

  try {
    await mkdir(DOCS_DIR, { recursive: true });
    await mkdir(path.join(DOCS_DIR, 'api'), { recursive: true });
    await mkdir(path.join(DOCS_DIR, 'code'), { recursive: true });
    await mkdir(path.join(DOCS_DIR, 'architecture'), { recursive: true });
    await mkdir(path.join(DOCS_DIR, 'architecture', 'decisions'), { recursive: true });

    log('Required directories created or verified', 'success');
  } catch (error) {
    log(`Error creating directories: ${error.message}`, 'error');
    throw error;
  }
}

/**
 * Generate API documentation from OpenAPI spec
 */
async function generateApiDocs() {
  log('Generating API documentation from OpenAPI spec', 'section');

  try {
    await execCommand('node scripts/generate-api-docs.js');
    log('API documentation generated successfully', 'success');
  } catch (error) {
    log(`Error generating API documentation: ${error.message}`, 'error');
    throw error;
  }
}

/**
 * Generate inline code documentation from source code comments
 */
async function generateInlineDocs() {
  log('Generating inline code documentation', 'section');

  try {
    await execCommand('node scripts/generate-inline-docs.js');
    log('Inline code documentation generated successfully', 'success');
  } catch (error) {
    log(`Error generating inline code documentation: ${error.message}`, 'error');
    throw error;
  }
}

/**
 * Generate ADR index
 */
async function generateAdrIndex() {
  log('Generating Architectural Decision Records index', 'section');

  try {
    await execCommand('node scripts/adr.js index');
    log('ADR index generated successfully', 'success');
  } catch (error) {
    log(`Error generating ADR index: ${error.message}`, 'error');
    throw error;
  }
}

/**
 * Create onboarding documentation
 */
async function generateOnboardingDocs() {
  log('Generating onboarding documentation', 'section');

  const onboardingPath = path.join(DOCS_DIR, 'onboarding.md');

  try {
    const exists = await stat(onboardingPath).catch(() => false);

    if (!exists) {
      log('Creating new onboarding documentation file');

      const onboardingContent = `# Maily Developer Onboarding

## Introduction

Welcome to the Maily development team! This guide will help you get started with the project, understand the codebase, and set up your development environment.

## Getting Started

### Prerequisites

- Node.js (v18+)
- npm (v8+)
- Python 3.10+
- Docker and Docker Compose
- Git

### Setup Steps

1. Clone the repository:
   \`\`\`bash
   git clone https://github.com/maily/maily.git
   cd maily
   \`\`\`

2. Install dependencies:
   \`\`\`bash
   npm install
   pip install -r requirements.txt
   \`\`\`

3. Set up environment variables:
   \`\`\`bash
   cp .env.example .env
   # Edit .env with your configuration
   \`\`\`

4. Start development servers:
   \`\`\`bash
   npm run dev
   \`\`\`

## Project Structure

- \`apps/\`: Application code
  - \`api/\`: Backend API services
  - \`web/\`: Frontend web applications
  - \`email-service/\`: Email rendering and delivery
  - \`workers/\`: Background processing workers
- \`packages/\`: Shared libraries
- \`docs/\`: Documentation
- \`scripts/\`: Automation scripts
- \`tests/\`: Test suites

## Key Architecture Concepts

- Hexagonal architecture with domain-driven design
- Microservices communication patterns
- AI-powered content generation
- Multi-provider email delivery

## Workflow

1. Pick up an issue from the project board
2. Create a feature branch: \`feature/your-feature-name\`
3. Implement your changes with appropriate tests
4. Submit a pull request
5. Respond to review feedback

## Documentation

- [Architecture Handbook](architecture-handbook.md)
- [API Reference](api-reference.md)
- [Development Guide](developer-guide.md)
- [Testing Guide](testing-guide.md)

## Getting Help

- Reach out in the #dev Slack channel
- Check existing Architecture Decision Records for context
- Review inline documentation and code comments
- Contact your onboarding buddy

## First Tasks

Here are some recommended first tasks to help you get familiar with the codebase:

1. Run the test suite and make sure everything passes
2. Fix a small bug or add a minor feature
3. Review the architecture documentation
4. Pair with another developer on a task
`;

      await writeFile(onboardingPath, onboardingContent);
      log('Created new onboarding documentation file', 'success');
    } else {
      log('Onboarding documentation already exists', 'success');
    }
  } catch (error) {
    log(`Error generating onboarding documentation: ${error.message}`, 'error');
    throw error;
  }
}

/**
 * Update MkDocs configuration to include onboarding documentation
 */
async function updateMkDocsConfig() {
  log('Updating MkDocs configuration', 'section');

  try {
    // Read the existing mkdocs.yml
    const mkdocsContent = await readFile(MKDOCS_PATH, 'utf8');
    const mkdocs = yaml.load(mkdocsContent);

    // Find the Getting Started section
    const gettingStartedIndex = mkdocs.nav.findIndex(item =>
      typeof item === 'object' && Object.keys(item)[0] === 'Getting Started'
    );

    if (gettingStartedIndex === -1) {
      log('Could not find "Getting Started" section in mkdocs.yml', 'warning');
      return;
    }

    // Add onboarding to the Getting Started section if it doesn't exist
    const gettingStarted = mkdocs.nav[gettingStartedIndex]['Getting Started'];
    const hasOnboarding = gettingStarted.some(item => {
      if (typeof item === 'object') {
        return Object.keys(item)[0] === 'Developer Onboarding';
      }
      return false;
    });

    if (!hasOnboarding) {
      gettingStarted.push({
        'Developer Onboarding': 'onboarding.md'
      });

      // Write updated config
      await writeFile(
        MKDOCS_PATH,
        yaml.dump(mkdocs, { lineWidth: 100, noRefs: true })
      );

      log('Added onboarding documentation to MkDocs configuration', 'success');
    } else {
      log('Onboarding documentation already in MkDocs configuration', 'success');
    }
  } catch (error) {
    log(`Error updating MkDocs config: ${error.message}`, 'error');
    throw error;
  }
}

/**
 * Validate documentation links and references
 */
async function validateDocumentation() {
  log('Validating documentation links and references', 'section');

  try {
    // Use MkDocs built-in validator (--strict flag fails on any warnings/errors)
    log('Running MkDocs validation checks...');
    await execCommand('mkdocs build --strict --site-dir site-temp');

    // Clean up temporary site directory
    await execCommand('rm -rf site-temp');

    log('Documentation validation passed', 'success');
    return true;
  } catch (error) {
    log(`Documentation validation failed: ${error.message}`, 'error');
    return false;
  }
}

/**
 * Generate documentation validation report
 */
async function generateValidationReport(validationSuccess) {
  log('Generating documentation validation report', 'section');

  try {
    const reportData = {
      timestamp: new Date().toISOString(),
      success: validationSuccess,
      validationErrors: [],
      stats: {
        totalFiles: 0,
        apiDocsFiles: 0,
        codeDocsFiles: 0,
        architectureDocsFiles: 0,
        adrs: 0
      }
    };

    // Count documentation files
    const apiFiles = await new Promise(resolve => {
      const result = execSync('find docs/api -type f -name "*.md" | wc -l', { encoding: 'utf8' });
      resolve(parseInt(result.trim(), 10));
    });

    const codeFiles = await new Promise(resolve => {
      const result = execSync('find docs/code -type f -name "*.md" | wc -l', { encoding: 'utf8' });
      resolve(parseInt(result.trim(), 10));
    });

    const architectureFiles = await new Promise(resolve => {
      const result = execSync('find docs/architecture -type f -name "*.md" | wc -l', { encoding: 'utf8' });
      resolve(parseInt(result.trim(), 10));
    });

    const adrFiles = await new Promise(resolve => {
      const result = execSync('find docs/architecture/decisions -type f -name "*.md" | wc -l', { encoding: 'utf8' });
      resolve(parseInt(result.trim(), 10));
    });

    const totalFiles = await new Promise(resolve => {
      const result = execSync('find docs -type f -name "*.md" | wc -l', { encoding: 'utf8' });
      resolve(parseInt(result.trim(), 10));
    });

    reportData.stats.totalFiles = totalFiles;
    reportData.stats.apiDocsFiles = apiFiles;
    reportData.stats.codeDocsFiles = codeFiles;
    reportData.stats.architectureDocsFiles = architectureFiles;
    reportData.stats.adrs = adrFiles;

    // If validation failed, try to extract error messages
    if (!validationSuccess) {
      try {
        const mkdocsOutput = execSync('mkdocs build --strict --site-dir site-temp 2>&1', { encoding: 'utf8' });

        // Extract error messages using regex
        const errorRegex = /ERROR\s*-\s*(.*?)$/gm;
        let match;
        while ((match = errorRegex.exec(mkdocsOutput)) !== null) {
          reportData.validationErrors.push(match[1].trim());
        }
      } catch (error) {
        if (error.stdout) {
          const errorRegex = /ERROR\s*-\s*(.*?)$/gm;
          let match;
          while ((match = errorRegex.exec(error.stdout)) !== null) {
            reportData.validationErrors.push(match[1].trim());
          }
        }
      } finally {
        // Clean up temporary site directory
        execSync('rm -rf site-temp');
      }
    }

    // Write report to file
    await writeFile(
      args.reportFile,
      JSON.stringify(reportData, null, 2)
    );

    log(`Validation report written to ${args.reportFile}`, 'success');

    // Generate human-readable report
    const reportSummary = `# Documentation Validation Report

Generated: ${new Date().toLocaleString()}

## Validation Status

${validationSuccess ? '✅ Passed' : '❌ Failed'}

## Statistics

- Total documentation files: ${totalFiles}
- API documentation files: ${apiFiles}
- Code documentation files: ${codeFiles}
- Architecture documentation files: ${architectureFiles}
- Architectural Decision Records: ${adrFiles}

${reportData.validationErrors.length > 0 ? `
## Validation Errors

${reportData.validationErrors.map(error => `- ${error}`).join('\n')}
` : ''}

## Next Steps

${validationSuccess
  ? '- Review the documentation to ensure completeness\n- Share the documentation with the team for feedback'
  : '- Fix the validation errors listed above\n- Run the validation again'}
`;

    await writeFile(
      path.join(DOCS_DIR, 'validation-report.md'),
      reportSummary
    );

    log('Human-readable report generated', 'success');
    return reportData;
  } catch (error) {
    log(`Error generating validation report: ${error.message}`, 'error');
    throw error;
  }
}

/**
 * Main function
 */
async function main() {
  const startTime = new Date();
  log('Starting documentation automation process', 'section');

  try {
    // Ensure required directories exist
    await ensureDirectories();

    // Skip generation steps if validate-only flag is set
    if (!args.validateOnly) {
      // Generate documentation
      await generateApiDocs();
      await generateInlineDocs();
      await generateAdrIndex();
      await generateOnboardingDocs();
      await updateMkDocsConfig();
    }

    // Validate documentation
    const validationSuccess = await validateDocumentation();

    // Generate validation report
    await generateValidationReport(validationSuccess);

    const endTime = new Date();
    const duration = (endTime - startTime) / 1000;

    log(`Documentation automation ${validationSuccess ? 'completed successfully' : 'failed'} in ${duration.toFixed(2)} seconds`, validationSuccess ? 'success' : 'error');

    if (!validationSuccess) {
      process.exit(1);
    }
  } catch (error) {
    log(`Error: ${error.message}`, 'error');
    process.exit(1);
  }
}

// Run the main function
main();
