describe('Email Campaign', () => {
  beforeEach(() => {
    // Login before each test
    cy.visit('/login')
    cy.get('input[name="email"]').type(Cypress.env('TEST_USER_EMAIL'))
    cy.get('input[name="password"]').type(Cypress.env('TEST_USER_PASSWORD'))
    cy.get('button[type="submit"]').click()
    cy.url().should('include', '/dashboard')
  })

  it('should create a new email campaign', () => {
    cy.visit('/campaigns/new')

    // Fill campaign details
    cy.get('input[name="campaign-name"]').type('Test Campaign')
    cy.get('input[name="subject-line"]').type('Important: Test Email')

    // Select template
    cy.get('[data-testid="template-selector"]').click()
    cy.contains('Welcome Email').click()

    // Customize content
    cy.get('[data-testid="email-editor"]').within(() => {
      cy.get('[data-testid="edit-heading"]').clear().type('Welcome to Our Service')
      cy.get('[data-testid="edit-body"]').clear().type('Thank you for joining us!')
    })

    // Select audience
    cy.get('[data-testid="audience-selector"]').click()
    cy.contains('All Subscribers').click()

    // Save campaign
    cy.get('button').contains('Save Campaign').click()

    // Verify campaign was created
    cy.contains('Campaign saved successfully').should('be.visible')
    cy.url().should('match', /\/campaigns\/[\w-]+$/)
  })

  it('should schedule and send a campaign', () => {
    // Navigate to existing campaign
    cy.visit('/campaigns')
    cy.contains('Test Campaign').click()

    // Schedule campaign
    cy.get('button').contains('Schedule').click()
    cy.get('input[name="schedule-date"]').type('2025-12-31T10:00')
    cy.get('button').contains('Confirm Schedule').click()

    // Verify scheduling
    cy.contains('Campaign scheduled').should('be.visible')
    cy.contains('Scheduled for:').should('be.visible')
  })

  it('should show campaign analytics', () => {
    // Navigate to campaign analytics
    cy.visit('/campaigns')
    cy.contains('Test Campaign').click()
    cy.get('[data-testid="view-analytics"]').click()

    // Verify analytics components
    cy.get('[data-testid="open-rate"]').should('exist')
    cy.get('[data-testid="click-rate"]').should('exist')
    cy.get('[data-testid="bounce-rate"]').should('exist')
    cy.get('[data-testid="unsubscribe-rate"]').should('exist')

    // Check analytics data loading
    cy.get('[data-testid="analytics-chart"]').should('be.visible')
    cy.get('[data-testid="recipients-list"]').should('be.visible')
  })

  it('should handle campaign errors and validation', () => {
    cy.visit('/campaigns/new')

    // Try to save without required fields
    cy.get('button').contains('Save Campaign').click()
    cy.contains('Campaign name is required').should('be.visible')
    cy.contains('Subject line is required').should('be.visible')

    // Try to schedule without audience
    cy.get('input[name="campaign-name"]').type('Test Campaign')
    cy.get('input[name="subject-line"]').type('Test Subject')
    cy.get('button').contains('Schedule').click()
    cy.contains('Please select an audience').should('be.visible')
  })
})
