#!/usr/bin/env node

/**
 * Automated accessibility testing script for CI
 * This script runs axe-core accessibility tests on specified URLs
 * and generates a report of accessibility issues.
 *
 * Usage:
 * node scripts/accessibility/run-axe-tests.js [--urls=url1,url2] [--threshold=number] [--report=path]
 *
 * Options:
 * --urls: Comma-separated list of URLs to test (default: http://localhost:3000)
 * --threshold: Maximum number of violations allowed before failing (default: 0)
 * --report: Path to save the report (default: accessibility-report.json)
 */

const { AxePuppeteer } = require('@axe-core/puppeteer');
const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

// Parse command line arguments
const args = process.argv.slice(2).reduce((acc, arg) => {
  const [key, value] = arg.split('=');
  if (key && value) {
    acc[key.replace('--', '')] = value;
  }
  return acc;
}, {});

// Default values
const urls = args.urls ? args.urls.split(',') : ['http://localhost:3000'];
const threshold = parseInt(args.threshold || '0', 10);
const reportPath = args.report || 'accessibility-report.json';

// Ensure the report directory exists
const reportDir = path.dirname(reportPath);
if (!fs.existsSync(reportDir)) {
  fs.mkdirSync(reportDir, { recursive: true });
}

// ANSI color codes for console output
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
 * Run axe accessibility tests on a URL
 * @param {string} url - The URL to test
 * @param {puppeteer.Browser} browser - The Puppeteer browser instance
 * @returns {Promise<object>} - The axe results
 */
async function runAxeTests(url, browser) {
  console.log(`${colors.blue}Testing URL: ${url}${colors.reset}`);

  const page = await browser.newPage();

  try {
    // Set viewport size
    await page.setViewport({ width: 1280, height: 800 });

    // Navigate to the URL
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });

    // Wait for any client-side rendering to complete
    await page.waitForTimeout(2000);

    // Run axe tests
    const results = await new AxePuppeteer(page)
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    return {
      url,
      timestamp: new Date().toISOString(),
      violations: results.violations,
      passes: results.passes,
      incomplete: results.incomplete,
      inapplicable: results.inapplicable,
    };
  } catch (error) {
    console.error(`${colors.red}Error testing ${url}: ${error.message}${colors.reset}`);
    return {
      url,
      timestamp: new Date().toISOString(),
      error: error.message,
      violations: [],
      passes: [],
      incomplete: [],
      inapplicable: [],
    };
  } finally {
    await page.close();
  }
}

/**
 * Print a summary of the accessibility test results
 * @param {object} results - The axe results
 */
function printSummary(results) {
  console.log('\n=== Accessibility Test Summary ===\n');

  let totalViolations = 0;
  let totalPasses = 0;

  results.forEach((result) => {
    const violations = result.violations.length;
    const passes = result.passes.length;
    totalViolations += violations;
    totalPasses += passes;

    console.log(`${colors.blue}URL: ${result.url}${colors.reset}`);

    if (violations === 0) {
      console.log(`${colors.green}✓ No accessibility violations found${colors.reset}`);
    } else {
      console.log(`${colors.red}✗ ${violations} accessibility violations found${colors.reset}`);

      // Group violations by impact
      const byImpact = result.violations.reduce((acc, violation) => {
        acc[violation.impact] = acc[violation.impact] || [];
        acc[violation.impact].push(violation);
        return acc;
      }, {});

      // Print violations by impact (critical first)
      ['critical', 'serious', 'moderate', 'minor'].forEach((impact) => {
        if (byImpact[impact] && byImpact[impact].length > 0) {
          const impactColor = impact === 'critical' || impact === 'serious' ? colors.red : colors.yellow;
          console.log(`${impactColor}${impact.toUpperCase()}: ${byImpact[impact].length} issues${colors.reset}`);

          byImpact[impact].forEach((violation) => {
            console.log(`  - ${violation.help}: ${violation.nodes.length} occurrences`);
          });
        }
      });
    }

    console.log(`${colors.green}✓ ${passes} accessibility checks passed${colors.reset}`);
    console.log('');
  });

  console.log('=== Overall Results ===');
  console.log(`${colors.blue}Total URLs tested: ${results.length}${colors.reset}`);
  console.log(`${totalViolations === 0 ? colors.green : colors.red}Total violations: ${totalViolations}${colors.reset}`);
  console.log(`${colors.green}Total passes: ${totalPasses}${colors.reset}`);
  console.log(`${colors.blue}Report saved to: ${reportPath}${colors.reset}`);

  if (totalViolations > threshold) {
    console.log(`${colors.red}❌ Failed: ${totalViolations} violations exceed threshold of ${threshold}${colors.reset}`);
    return false;
  } else {
    console.log(`${colors.green}✅ Passed: ${totalViolations} violations within threshold of ${threshold}${colors.reset}`);
    return true;
  }
}

/**
 * Main function to run the accessibility tests
 */
async function main() {
  console.log(`${colors.cyan}Starting accessibility tests...${colors.reset}`);
  console.log(`${colors.cyan}Testing ${urls.length} URLs with threshold of ${threshold}${colors.reset}`);

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  try {
    // Run tests for all URLs
    const results = [];
    for (const url of urls) {
      const result = await runAxeTests(url, browser);
      results.push(result);
    }

    // Save the report
    fs.writeFileSync(reportPath, JSON.stringify(results, null, 2));

    // Print summary
    const passed = printSummary(results);

    // Exit with appropriate code
    process.exit(passed ? 0 : 1);
  } catch (error) {
    console.error(`${colors.red}Error running accessibility tests: ${error.message}${colors.reset}`);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

// Run the main function
main();
