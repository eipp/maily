// ***********************************************
// This example commands.ts shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************

/// <reference types="cypress" />
/// <reference types="cypress-axe" />

// Declare global Cypress namespace to add custom commands
declare global {
  namespace Cypress {
    interface Chainable<Subject> {
      /**
       * Custom command to login with email and password
       * @example cy.login('user@example.com', 'password123')
       */
      login(email: string, password: string): Chainable<Element>;

      /**
       * Custom command to create a new email campaign
       * @example cy.createCampaign('Test Campaign', 'Welcome Email')
       */
      createCampaign(name: string, templateName: string): Chainable<Element>;

      /**
       * Custom command to check accessibility with axe
       * @example cy.checkAccessibility()
       */
      checkAccessibility(options?: any): Chainable<Element>;

      /**
       * Custom command to check page performance
       * @example cy.checkPagePerformance()
       */
      checkPagePerformance(): Chainable<any>;

      /**
       * Custom command to drag and drop elements in the canvas
       */
      dragAndDrop(
        draggableSelector: string,
        droppableSelector: string,
        offsetX?: number,
        offsetY?: number
      ): Chainable<Element>;
    }
  }
}

// Login command
Cypress.Commands.add('login', (email: string, password: string) => {
  cy.visit('/login');
  cy.get('[data-testid="email-input"]').type(email);
  cy.get('[data-testid="password-input"]').type(password);
  cy.get('[data-testid="login-button"]').click();

  // Wait for login to complete and redirect
  cy.url().should('not.include', '/login');

  // Verify user is logged in
  cy.get('[data-testid="user-menu"]').should('be.visible');
});

// Create campaign command
Cypress.Commands.add('createCampaign', (name: string, templateName: string) => {
  // Navigate to campaigns page
  cy.visit('/campaigns');

  // Click create campaign button
  cy.get('[data-testid="create-campaign-button"]').click();

  // Enter campaign name
  cy.get('[data-testid="campaign-name-input"]').type(name);

  // Select template
  cy.get('[data-testid="template-selector"]').click();
  cy.contains(templateName).click();

  // Save campaign
  cy.get('[data-testid="save-campaign-button"]').click();

  // Wait for save to complete
  cy.contains('Campaign created successfully').should('be.visible');

  // Return to campaigns page
  cy.visit('/campaigns');

  // Verify campaign was created
  cy.contains(name).should('be.visible');
});

// Check accessibility command
Cypress.Commands.add('checkAccessibility', (options = {}) => {
  cy.injectAxe();
  cy.checkA11y(
    undefined, // context
    {
      runOnly: {
        type: 'tag',
        values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'],
      },
      ...options,
    },
    null, // callback
    true // should log to console
  );
});

// Drag and drop command for canvas elements
Cypress.Commands.add(
  'dragAndDrop',
  (draggableSelector: string, droppableSelector: string, offsetX = 0, offsetY = 0) => {
    // Get coordinates
    cy.get(draggableSelector).then($draggable => {
      const draggableRect = $draggable[0].getBoundingClientRect();
      const draggableX = draggableRect.left + draggableRect.width / 2;
      const draggableY = draggableRect.top + draggableRect.height / 2;

      cy.get(droppableSelector).then($droppable => {
        const droppableRect = $droppable[0].getBoundingClientRect();
        const droppableX = droppableRect.left + droppableRect.width / 2 + offsetX;
        const droppableY = droppableRect.top + droppableRect.height / 2 + offsetY;

        // Perform drag and drop
        cy.get(draggableSelector)
          .trigger('mousedown', { button: 0, clientX: draggableX, clientY: draggableY, force: true })
          .trigger('mousemove', { button: 0, clientX: droppableX, clientY: droppableY, force: true })
          .trigger('mouseup', { force: true });
      });
    });
  }
);
