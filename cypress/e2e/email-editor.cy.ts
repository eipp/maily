describe('Email Editor', () => {
  beforeEach(() => {
    // Use our custom login command
    cy.login('test@example.com', 'password123');

    // Navigate to the email editor
    cy.visit('/editor/new');

    // Wait for the editor to load
    cy.get('[data-testid="email-editor-canvas"]', { timeout: 10000 }).should('be.visible');
  });

  it('should load the editor with default template', () => {
    // Verify editor components are visible
    cy.get('[data-testid="editor-toolbox"]').should('be.visible');
    cy.get('[data-testid="editor-properties-panel"]').should('be.visible');
    cy.get('[data-testid="save-button"]').should('be.visible');

    // Verify default template has essential elements
    cy.get('[data-testid="email-header"]').should('exist');
    cy.get('[data-testid="email-body"]').should('exist');
    cy.get('[data-testid="email-footer"]').should('exist');
  });

  it('should add text element to canvas', () => {
    // Find text element in toolbox
    cy.get('[data-testid="toolbox-text-element"]').should('be.visible');

    // Drag text element to canvas
    cy.dragAndDrop(
      '[data-testid="toolbox-text-element"]',
      '[data-testid="email-body"]'
    );

    // Verify text element was added
    cy.get('[data-testid="email-body"]')
      .find('[data-element-type="text"]')
      .should('exist');

    // Click on text element to edit
    cy.get('[data-element-type="text"]').click();

    // Verify text properties panel is shown
    cy.get('[data-testid="text-properties-panel"]').should('be.visible');

    // Edit text content
    cy.get('[data-testid="text-content-input"]')
      .clear()
      .type('Hello, this is a test email!');

    // Verify text content updated in canvas
    cy.get('[data-element-type="text"]')
      .should('contain.text', 'Hello, this is a test email!');
  });

  it('should change text element styling', () => {
    // Add text element
    cy.dragAndDrop(
      '[data-testid="toolbox-text-element"]',
      '[data-testid="email-body"]'
    );

    // Click on text element to edit
    cy.get('[data-element-type="text"]').click();

    // Change font size
    cy.get('[data-testid="font-size-select"]').click();
    cy.get('[data-value="18px"]').click();

    // Change text color
    cy.get('[data-testid="text-color-picker"]').click();
    cy.get('[data-color="#3366FF"]').click();

    // Change font weight
    cy.get('[data-testid="font-weight-bold"]').click();

    // Verify styling changes
    cy.get('[data-element-type="text"]').should('have.css', 'font-size', '18px');
    cy.get('[data-element-type="text"]').should('have.css', 'color', 'rgb(51, 102, 255)');
    cy.get('[data-element-type="text"]').should('have.css', 'font-weight', '700');
  });

  it('should add image element to canvas', () => {
    // Find image element in toolbox
    cy.get('[data-testid="toolbox-image-element"]').should('be.visible');

    // Drag image element to canvas
    cy.dragAndDrop(
      '[data-testid="toolbox-image-element"]',
      '[data-testid="email-body"]'
    );

    // Verify image element was added
    cy.get('[data-testid="email-body"]')
      .find('[data-element-type="image"]')
      .should('exist');

    // Click on image element to edit
    cy.get('[data-element-type="image"]').click();

    // Verify image properties panel is shown
    cy.get('[data-testid="image-properties-panel"]').should('be.visible');

    // Update image source
    cy.get('[data-testid="image-src-input"]')
      .clear()
      .type('https://example.com/test-image.jpg');

    // Add alt text
    cy.get('[data-testid="image-alt-input"]')
      .clear()
      .type('Test image alt text');

    // Verify image updated in canvas
    cy.get('[data-element-type="image"] img')
      .should('have.attr', 'src', 'https://example.com/test-image.jpg');
    cy.get('[data-element-type="image"] img')
      .should('have.attr', 'alt', 'Test image alt text');
  });

  it('should save email template', () => {
    // Add some content to the email
    cy.dragAndDrop(
      '[data-testid="toolbox-text-element"]',
      '[data-testid="email-body"]'
    );

    // Enter template name
    cy.get('[data-testid="template-name-input"]')
      .clear()
      .type('E2E Test Template');

    // Save the template
    cy.get('[data-testid="save-button"]').click();

    // Verify save success message
    cy.contains('Template saved successfully').should('be.visible');

    // Navigate to templates page
    cy.visit('/templates');

    // Verify template appears in list
    cy.contains('E2E Test Template').should('be.visible');
  });

  it('should check email accessibility', () => {
    // Add a heading and some content
    cy.dragAndDrop(
      '[data-testid="toolbox-heading-element"]',
      '[data-testid="email-body"]'
    );

    cy.dragAndDrop(
      '[data-testid="toolbox-text-element"]',
      '[data-testid="email-body"]'
    );

    // Check accessibility
    cy.checkAccessibility();
  });

  it('should check editor performance', () => {
    // Start performance measurement
    const startTime = performance.now();

    // Add multiple elements to test performance
    for (let i = 0; i < 5; i++) {
      cy.dragAndDrop(
        '[data-testid="toolbox-text-element"]',
        '[data-testid="email-body"]'
      );

      cy.dragAndDrop(
        '[data-testid="toolbox-image-element"]',
        '[data-testid="email-body"]'
      );
    }

    // End performance measurement
    cy.window().then(() => {
      const endTime = performance.now();
      expect({ startTime, endTime }).to.performWithin(5000);
    });

    // Check page performance metrics
    cy.checkPagePerformance();
  });
});
