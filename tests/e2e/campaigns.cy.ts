describe('Campaign Management', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'password123');
  });

  it('should display campaign list', () => {
    cy.visit('/campaigns');
    cy.get('[data-testid="campaign-list"]').should('exist');
    cy.get('[data-testid="create-campaign-button"]').should('be.visible');
  });

  it('should create new campaign', () => {
    const campaignName = 'Test Campaign';
    const subject = 'Test Subject';

    cy.createCampaign(campaignName, subject);
    cy.get('[data-testid="success-message"]').should('be.visible');
    cy.url().should('include', '/campaigns');
    cy.get('[data-testid="campaign-list"]').should('contain', campaignName);
  });

  it('should edit existing campaign', () => {
    cy.visit('/campaigns');
    cy.get('[data-testid="campaign-item"]').first().click();
    cy.get('[data-testid="edit-campaign-button"]').click();
    cy.get('[data-testid="campaign-name"]').clear().type('Updated Campaign');
    cy.get('[data-testid="save-campaign"]').click();
    cy.get('[data-testid="success-message"]').should('be.visible');
    cy.get('[data-testid="campaign-list"]').should('contain', 'Updated Campaign');
  });

  it('should delete campaign', () => {
    cy.visit('/campaigns');
    cy.get('[data-testid="campaign-item"]')
      .first()
      .within(() => {
        cy.get('[data-testid="delete-campaign"]').click();
      });
    cy.get('[data-testid="confirm-delete"]').click();
    cy.get('[data-testid="success-message"]').should('be.visible');
  });

  it('should send test email', () => {
    cy.visit('/campaigns');
    cy.get('[data-testid="campaign-item"]').first().click();
    cy.get('[data-testid="send-test-email"]').click();
    cy.get('[data-testid="test-email-input"]').type('test@example.com');
    cy.get('[data-testid="send-test"]').click();
    cy.get('[data-testid="success-message"]').should('contain', 'Test email sent');
  });
});
