describe('Marketing Website', () => {
  beforeEach(() => {
    // Start from homepage
    cy.visit('/')
  })

  it('should load homepage with all key elements', () => {
    // Check main sections
    cy.get('[data-testid="hero-section"]').should('be.visible')
    cy.get('[data-testid="features-section"]').should('be.visible')
    cy.get('[data-testid="pricing-section"]').should('be.visible')
    cy.get('[data-testid="testimonials-section"]').should('be.visible')

    // Check navigation
    cy.get('nav').within(() => {
      cy.contains('Features').should('be.visible')
      cy.contains('Pricing').should('be.visible')
      cy.contains('Login').should('be.visible')
      cy.contains('Sign Up').should('be.visible')
    })

    // Check footer
    cy.get('footer').within(() => {
      cy.contains('About Us').should('be.visible')
      cy.contains('Contact').should('be.visible')
      cy.contains('Privacy Policy').should('be.visible')
      cy.contains('Terms of Service').should('be.visible')
    })
  })

  it('should have working navigation links', () => {
    // Test main navigation
    cy.contains('Features').click()
    cy.url().should('include', '/features')

    cy.contains('Pricing').click()
    cy.url().should('include', '/pricing')

    cy.contains('About Us').click()
    cy.url().should('include', '/about')

    // Test CTA buttons
    cy.get('[data-testid="hero-section"]')
      .contains('Get Started')
      .click()
    cy.url().should('include', '/signup')
  })

  it('should have responsive design', () => {
    // Test mobile menu
    cy.viewport('iphone-x')
    cy.get('[data-testid="mobile-menu-button"]').should('be.visible').click()
    cy.get('[data-testid="mobile-menu"]').should('be.visible')

    // Test tablet layout
    cy.viewport('ipad-2')
    cy.get('[data-testid="features-section"]')
      .should('have.css', 'grid-template-columns', '1fr 1fr')

    // Test desktop layout
    cy.viewport(1920, 1080)
    cy.get('[data-testid="features-section"]')
      .should('have.css', 'grid-template-columns', '1fr 1fr 1fr')
  })

  it('should handle contact form submission', () => {
    cy.contains('Contact').click()

    // Fill out contact form
    cy.get('input[name="name"]').type('Test User')
    cy.get('input[name="email"]').type('test@example.com')
    cy.get('textarea[name="message"]').type('This is a test message')

    // Submit form
    cy.get('button[type="submit"]').click()

    // Check success message
    cy.contains('Thank you for your message').should('be.visible')
  })

  it('should load and play demo video', () => {
    cy.get('[data-testid="demo-video"]').should('be.visible')

    // Check video controls
    cy.get('[data-testid="demo-video"]').within(() => {
      cy.get('button[aria-label="Play"]').click()
      cy.get('video')
        .should('have.prop', 'paused', false)
        .and('have.prop', 'ended', false)
    })
  })

  it('should track marketing events', () => {
    // Intercept analytics calls
    cy.intercept('POST', '/api/analytics').as('analyticsCall')

    // Trigger trackable events
    cy.contains('Sign Up').click()
    cy.wait('@analyticsCall').its('request.body')
      .should('include', {
        event: 'signup_click',
        source: 'header'
      })

    cy.contains('Pricing').click()
    cy.wait('@analyticsCall').its('request.body')
      .should('include', {
        event: 'pricing_view'
      })
  })
})
