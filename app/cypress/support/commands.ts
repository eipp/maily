import '@testing-library/cypress/add-commands';

// Custom command for login
Cypress.Commands.add('login', (email: string, password: string) => {
  // First check if we have a valid session
  cy.window().its('localStorage').invoke('getItem', 'auth_token').then((token) => {
    if (!token) {
      // No valid session, perform login
      cy.visit('/auth/login');
      cy.get('[data-cy=email]').type(email);
      cy.get('[data-cy=password]').type(password);
      cy.get('[data-cy=login-submit]').click();
      
      // Wait for successful login
      cy.url().should('include', '/dashboard');
    }
  });
});

// Custom command to create campaign
Cypress.Commands.add('createCampaign', (name: string, subject: string) => {
  cy.visit('/campaigns/new');
  cy.get('[data-testid="campaign-name"]').type(name);
  cy.get('[data-testid="campaign-subject"]').type(subject);
  cy.get('[data-testid="save-campaign"]').click();
});

declare global {
  namespace Cypress {
    interface Chainable {
      login(email: string, password: string): Chainable<void>;
      createCampaign(name: string, subject: string): Chainable<void>;
    }
  }
} 