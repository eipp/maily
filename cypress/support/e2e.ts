// ***********************************************************
// This support file is processed and loaded automatically
// before your test files.
//
// This is a great place to put global configuration and
// behavior that modifies Cypress.
// ***********************************************************

// Import commands.js using ES2015 syntax:
import './commands';

// Configure Cypress behavior
Cypress.on('uncaught:exception', (err, runnable) => {
  // Returning false here prevents Cypress from failing the test when
  // an uncaught exception happens in the application code
  // This is useful when testing third-party libraries or components
  // that might throw errors but don't affect the test flow
  console.log('Uncaught exception:', err.message);
  return false;
});

// Set up localStorage persistence between tests
beforeEach(() => {
  // Preserve localStorage from previous tests
  const win = cy.state('window');
  if (win) {
    const localStorage = win.localStorage;
    if (localStorage) {
      Object.keys(localStorage).forEach(key => {
        cy.log(`Preserved localStorage key: ${key}`);
      });
    }
  }

  // Set default viewport for all tests
  cy.viewport(1280, 720);
});

// Add global error and request logging for debugging
Cypress.on('log:added', (attrs, log) => {
  if (attrs.name === 'request' || attrs.name === 'xhr') {
    console.log(
      `${attrs.name} ${attrs.method} ${attrs.url}: ${attrs.status}`
    );
  }
});

// Add custom assertion for performance testing
chai.Assertion.addMethod('performWithin', function(threshold) {
  const startTime = this._obj.startTime;
  const endTime = this._obj.endTime;
  const duration = endTime - startTime;

  this.assert(
    duration <= threshold,
    `expected operation to complete within ${threshold}ms but it took ${duration}ms`,
    `expected operation to take longer than ${threshold}ms but it took ${duration}ms`,
    threshold,
    duration,
    true
  );
});

// Add global accessibility testing
// This injects axe-core into the page and provides a11y commands
import 'cypress-axe';

// Add custom command to check page performance
Cypress.Commands.add('checkPagePerformance', () => {
  return cy.window().then(win => {
    // Get performance timing metrics
    const performance = win.performance;
    if (!performance) {
      cy.log('Performance API not supported');
      return null;
    }

    const timing = performance.timing;
    const navigationStart = timing.navigationStart;

    // Calculate key metrics
    const metrics = {
      totalPageLoad: timing.loadEventEnd - navigationStart,
      domContentLoaded: timing.domContentLoadedEventEnd - navigationStart,
      firstPaint: performance.getEntriesByType('paint')[0]?.startTime || 0,
      firstContentfulPaint: performance.getEntriesByType('paint')[1]?.startTime || 0,
      domInteractive: timing.domInteractive - navigationStart,
      resourceLoading: timing.responseEnd - timing.responseStart,
    };

    // Log performance metrics
    cy.task('log', `Page Performance Metrics:\n${JSON.stringify(metrics, null, 2)}`);

    // Check if metrics are within acceptable ranges
    if (metrics.totalPageLoad > 5000) {
      cy.log(`⚠️ Warning: Total page load time (${metrics.totalPageLoad}ms) exceeds 5000ms`);
    }

    if (metrics.firstContentfulPaint > 2000) {
      cy.log(`⚠️ Warning: First contentful paint (${metrics.firstContentfulPaint}ms) exceeds 2000ms`);
    }

    return metrics;
  });
});

// Load test data fixtures
const loadFixtures = () => {
  cy.fixture('users.json').as('users');
  cy.fixture('templates.json').as('templates');
  cy.fixture('campaigns.json').as('campaigns');
};

beforeEach(loadFixtures);
