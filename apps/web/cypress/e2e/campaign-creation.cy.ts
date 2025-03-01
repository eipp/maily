describe('Campaign Creation Flow', () => {
  beforeEach(() => {
    // Assuming we have a login helper
    cy.login('test@example.com', 'password');
    cy.visit('/dashboard/campaigns/new');
  });

  it('creates a new campaign successfully', () => {
    // Fill out campaign details
    cy.get('[data-cy=campaign-name]').type('Welcome Campaign');
    cy.get('[data-cy=campaign-subject]').type('Welcome to Maily!');
    cy.get('[data-cy=campaign-content]').type('Hello {name}, welcome to our platform!');

    // Test AI content generation
    cy.get('[data-cy=generate-content]').click();
    cy.get('[data-cy=ai-suggestions]').should('be.visible');
    cy.get('[data-cy=use-suggestion]').first().click();

    // Test personalization preview
    cy.get('[data-cy=preview-personalization]').click();
    cy.get('[data-cy=preview-content]').should('contain', 'Hello John');

    // Submit the campaign
    cy.get('[data-cy=submit-campaign]').click();

    // Verify success
    cy.get('[data-cy=success-message]').should('be.visible');
    cy.url().should('include', '/dashboard/campaigns');
  });

  it('validates required fields', () => {
    // Try to submit empty form
    cy.get('[data-cy=submit-campaign]').click();

    // Check validation messages
    cy.get('[data-cy=name-error]').should('be.visible');
    cy.get('[data-cy=subject-error]').should('be.visible');
    cy.get('[data-cy=content-error]').should('be.visible');
  });

  it('handles API errors gracefully', () => {
    // Intercept API call and force an error
    cy.intercept('POST', '/api/campaigns', {
      statusCode: 500,
      body: { error: 'Internal Server Error' },
    }).as('createCampaign');

    // Fill out form
    cy.get('[data-cy=campaign-name]').type('Test Campaign');
    cy.get('[data-cy=campaign-subject]').type('Test Subject');
    cy.get('[data-cy=campaign-content]').type('Test Content');

    // Submit
    cy.get('[data-cy=submit-campaign]').click();

    // Verify error handling
    cy.get('[data-cy=error-message]')
      .should('be.visible')
      .and('contain', 'Failed to create campaign');
  });

  it('saves campaign as draft', () => {
    // Fill partial details
    cy.get('[data-cy=campaign-name]').type('Draft Campaign');
    cy.get('[data-cy=campaign-subject]').type('Draft Subject');

    // Save as draft
    cy.get('[data-cy=save-draft]').click();

    // Verify draft saved
    cy.get('[data-cy=success-message]').should('be.visible').and('contain', 'Draft saved');

    // Verify in drafts list
    cy.visit('/dashboard/campaigns/drafts');
    cy.get('[data-cy=draft-list]').should('contain', 'Draft Campaign');
  });
});
