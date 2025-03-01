import '@testing-library/cypress/add-commands';

// Custom command for login
Cypress.Commands.add('login', (email: string, password: string) => {
  cy.visit('/login');
  cy.get('input[name="email"]').type(email);
  cy.get('input[name="password"]').type(password);
  cy.get('button[type="submit"]').click();
  cy.url().should('include', '/dashboard');
});

// Custom command to create campaign
Cypress.Commands.add('createCampaign', (name: string, subject: string) => {
  cy.visit('/campaigns/new');
  cy.get('input[name="campaign-name"]').type(name);
  cy.get('input[name="subject-line"]').type(subject);
  cy.get('[data-testid="template-selector"]').click();
  cy.contains('Welcome Email').click();
});

// Generate AI content command
Cypress.Commands.add('generateAIContent', (brief: string, tone: string) => {
  cy.get('[data-testid="ai-content-generator"]').click();
  cy.get('textarea[name="content-brief"]').type(brief);
  cy.get('select[name="tone"]').select(tone);
  cy.get('button').contains('Generate Content').click();
  cy.waitForAIResponse();
  return cy.get('[data-testid="ai-generated-content"]').invoke('text');
});

// Wait for AI response command
Cypress.Commands.add('waitForAIResponse', () => {
  cy.get('[data-testid="loading-indicator"]', { timeout: 15000 })
    .should('not.exist');
});

declare global {
  namespace Cypress {
    interface Chainable {
      login(email: string, password: string): Chainable<void>;
      createCampaign(name: string, subject: string): Chainable<void>;
      generateAIContent(brief: string, tone: string): Chainable<string>;
      waitForAIResponse(): Chainable<void>;
    }
  }
}
