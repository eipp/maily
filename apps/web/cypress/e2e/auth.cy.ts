describe('Authentication Flow', () => {
  beforeEach(() => {
    cy.visit('/login')
  })

  it('should show validation errors for empty form submission', () => {
    cy.get('button[type="submit"]').click()
    cy.contains('Email is required').should('be.visible')
    cy.contains('Password is required').should('be.visible')
  })

  it('should show error for invalid credentials', () => {
    cy.get('input[name="email"]').type('invalid@example.com')
    cy.get('input[name="password"]').type('wrongpassword')
    cy.get('button[type="submit"]').click()
    cy.contains('Invalid email or password').should('be.visible')
  })

  it('should redirect to dashboard after successful login', () => {
    cy.get('input[name="email"]').type(Cypress.env('TEST_USER_EMAIL'))
    cy.get('input[name="password"]').type(Cypress.env('TEST_USER_PASSWORD'))
    cy.get('button[type="submit"]').click()
    cy.url().should('include', '/dashboard')
    cy.contains('Welcome back').should('be.visible')
  })

  it('should allow password reset request', () => {
    cy.contains('Forgot password?').click()
    cy.url().should('include', '/reset-password')
    cy.get('input[name="email"]').type('test@example.com')
    cy.get('button[type="submit"]').click()
    cy.contains('Password reset instructions sent').should('be.visible')
  })

  it('should maintain session after page reload', () => {
    // Login first
    cy.get('input[name="email"]').type(Cypress.env('TEST_USER_EMAIL'))
    cy.get('input[name="password"]').type(Cypress.env('TEST_USER_PASSWORD'))
    cy.get('button[type="submit"]').click()

    // Verify login success
    cy.url().should('include', '/dashboard')

    // Reload page
    cy.reload()

    // Should still be logged in
    cy.url().should('include', '/dashboard')
    cy.contains('Welcome back').should('be.visible')
  })
})
