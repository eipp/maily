describe('AI Agent', () => {
  beforeEach(() => {
    // Login before each test
    cy.visit('/login')
    cy.get('input[name="email"]').type(Cypress.env('TEST_USER_EMAIL'))
    cy.get('input[name="password"]').type(Cypress.env('TEST_USER_PASSWORD'))
    cy.get('button[type="submit"]').click()
    cy.url().should('include', '/dashboard')
  })

  it('should generate email content using AI', () => {
    cy.visit('/campaigns/new')

    // Open AI content generator
    cy.get('[data-testid="ai-content-generator"]').click()

    // Fill prompt details
    cy.get('textarea[name="content-brief"]')
      .type('Write a welcome email for new software users')

    cy.get('select[name="tone"]').select('Professional')
    cy.get('input[name="target-audience"]').type('Software developers')

    // Generate content
    cy.get('button').contains('Generate Content').click()

    // Wait for generation and verify
    cy.get('[data-testid="ai-generated-content"]', { timeout: 10000 })
      .should('be.visible')
      .and('not.be.empty')

    // Apply generated content
    cy.get('button').contains('Use This Content').click()

    // Verify content was applied to editor
    cy.get('[data-testid="email-editor"]')
      .should('contain.text', 'Welcome')
  })

  it('should analyze campaign performance with AI', () => {
    // Navigate to completed campaign
    cy.visit('/campaigns')
    cy.contains('Completed Campaign').click()

    // Open AI analysis
    cy.get('[data-testid="ai-analysis"]').click()

    // Wait for analysis to complete
    cy.get('[data-testid="ai-insights"]', { timeout: 15000 })
      .should('be.visible')

    // Verify analysis components
    cy.get('[data-testid="performance-score"]').should('exist')
    cy.get('[data-testid="improvement-suggestions"]').should('exist')
    cy.get('[data-testid="audience-insights"]').should('exist')
  })

  it('should optimize subject lines with AI', () => {
    cy.visit('/campaigns/new')

    // Enter initial subject line
    cy.get('input[name="subject-line"]')
      .type('Welcome to our platform')

    // Request AI optimization
    cy.get('[data-testid="optimize-subject"]').click()

    // Wait for suggestions
    cy.get('[data-testid="subject-suggestions"]', { timeout: 10000 })
      .should('be.visible')

    // Verify multiple suggestions
    cy.get('[data-testid="subject-option"]')
      .should('have.length.at.least', 3)

    // Select a suggestion
    cy.get('[data-testid="subject-option"]')
      .first()
      .click()

    // Verify selection was applied
    cy.get('input[name="subject-line"]')
      .should('not.have.value', 'Welcome to our platform')
  })

  it('should handle AI service errors gracefully', () => {
    cy.visit('/campaigns/new')

    // Simulate API error by using invalid prompt
    cy.get('[data-testid="ai-content-generator"]').click()
    cy.get('textarea[name="content-brief"]')
      .type('{"invalid": "prompt"}')

    cy.get('button').contains('Generate Content').click()

    // Verify error handling
    cy.contains('Error generating content').should('be.visible')
    cy.get('[data-testid="error-details"]')
      .should('contain.text', 'Please try again')

    // Verify recovery option
    cy.get('button').contains('Try Again')
      .should('be.visible')
      .click()

    // Verify form reset
    cy.get('textarea[name="content-brief"]')
      .should('be.empty')
  })
})
