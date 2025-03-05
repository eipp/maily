describe('Cognitive Canvas', () => {
  beforeEach(() => {
    cy.intercept('GET', '/api/v1/canvas/**', { 
      statusCode: 200, 
      body: { data: { shapes: [], layers: [] } } 
    }).as('getCanvasData');
    
    cy.intercept('POST', '/api/v1/canvas/**', {
      statusCode: 200,
      body: { data: { id: 'test-canvas-id' } }
    }).as('saveCanvas');
    
    cy.intercept('POST', '/api/v1/mailydocs/documents/*/verify', {
      statusCode: 200,
      body: {
        data: {
          verification_info: {
            certificate_id: 'cert-123456',
            document_hash: 'abc123def456',
            timestamp: new Date().toISOString(),
            verification_url: 'https://verify.maily.app/cert-123456',
            qr_code: 'https://example.com/qr-code-placeholder.png',
            blockchain_transaction: {
              transaction_id: '0xabcdef1234567890',
              block_number: '12345678',
              network: 'Polygon'
            }
          }
        }
      }
    }).as('verifyDocument');
    
    cy.visit('/canvas-demo');
  });

  it('should load the canvas editor correctly', () => {
    cy.get('[aria-label="Interactive canvas editor"]').should('be.visible');
    cy.get('[aria-label="Canvas tools"]').should('be.visible');
    cy.get('[aria-label="Canvas workspace"]').should('be.visible');
  });

  it('should add shapes to the canvas', () => {
    // Add a rectangle
    cy.get('button[aria-label="Add rectangle"]').click();
    cy.get('rect').should('have.length.at.least', 1);
    
    // Add a circle
    cy.get('button[aria-label="Add circle"]').click();
    cy.get('circle').should('have.length.at.least', 1);
    
    // Add text
    cy.get('button[aria-label="Add text"]').click();
    cy.get('text').should('have.length.at.least', 1);
  });

  it('should select and delete shapes', () => {
    // Add a shape
    cy.get('button[aria-label="Add rectangle"]').click();
    
    // Select the shape (click on the rectangle)
    cy.get('rect').first().click();
    
    // Delete the shape
    cy.get('button[aria-label="Delete selected shape"]').click();
    
    // Verify shape count decreased
    cy.get('rect').should('have.length', 0);
  });

  it('should manage layers correctly', () => {
    // Open layers panel
    cy.get('button[aria-label="Toggle layers panel"]').click();
    
    // Add a new layer
    cy.contains('button', 'Add Layer').click();
    
    // Verify layer was added
    cy.get('[data-testid="layer-item"]').should('have.length.at.least', 2);
    
    // Toggle layer visibility
    cy.get('[data-testid="toggle-visibility"]').first().click();
    cy.get('[data-testid="toggle-visibility"]').first().click();
  });

  it('should handle zoom controls', () => {
    // Initial zoom should be 100%
    cy.contains('100%').should('exist');
    
    // Zoom in
    cy.get('button[aria-label="Zoom in"]').click();
    cy.contains('120%').should('exist');
    
    // Zoom out
    cy.get('button[aria-label="Zoom out"]').click();
    cy.contains('100%').should('exist');
    
    // Reset zoom
    cy.get('button[aria-label="Reset zoom"]').click();
    cy.contains('100%').should('exist');
  });

  it('should show MailyDocs editor with proper tabs', () => {
    cy.visit('/mailydocs');
    
    // Verify tabs exist
    cy.contains('Design').should('be.visible');
    cy.contains('Content').should('be.visible');
    cy.contains('Preview').should('be.visible');
    
    // Verify document type selection
    cy.get('label').contains('Document Type').should('be.visible');
    
    // Check document title input
    cy.get('input[placeholder="Enter document title"]').should('be.visible');
    
    // Check personalization toggle
    cy.get('label').contains('Enable Personalization').should('be.visible');
    
    // Check blockchain verification toggle
    cy.get('label').contains('Blockchain Verification').should('be.visible');
  });

  it('should create and verify a document with blockchain', () => {
    cy.visit('/mailydocs');
    
    // Enter document title
    cy.get('input[placeholder="Enter document title"]').type('Test Verified Document');
    
    // Select document type
    cy.get('label').contains('Document Type').parent().find('button').click();
    cy.contains('Smart PDF').click();
    
    // Enable blockchain verification
    cy.get('label').contains('Blockchain Verification').prev().check();
    
    // Add section content
    cy.get('textarea[placeholder="Enter text content"]').type('This is a test document with blockchain verification');
    
    // Save document
    cy.contains('button', 'Save Document').click();
    
    // Should show verification tab
    cy.contains('Verification').should('be.visible');
    
    // Verification tab should contain certificate data
    cy.contains('Verification').click();
    cy.contains('Blockchain Certificate').should('be.visible');
    cy.contains('Certificate ID:').should('be.visible');
    cy.contains('Transaction ID:').should('be.visible');
  });

  it('should handle performance metrics panel', () => {
    // Toggle performance metrics panel
    cy.get('button[aria-label="Toggle performance metrics"]').click();
    
    // Verify performance panel appears
    cy.contains('Performance Metrics').should('be.visible');
    cy.contains('Shape Count:').should('be.visible');
    cy.contains('Layer Count:').should('be.visible');
    
    // Add shapes to see metrics update
    cy.get('button[aria-label="Add rectangle"]').click();
    cy.get('button[aria-label="Add circle"]').click();
    
    // Close performance panel
    cy.get('button[aria-label="Toggle performance metrics"]').click();
    cy.contains('Performance Metrics').should('not.be.visible');
  });

  it('should handle undo and redo actions', () => {
    // Add a shape
    cy.get('button[aria-label="Add rectangle"]').click();
    cy.get('rect').should('have.length.at.least', 1);
    
    // Delete the shape
    cy.get('rect').first().click();
    cy.get('button[aria-label="Delete selected shape"]').click();
    cy.get('rect').should('have.length', 0);
    
    // Undo deletion
    cy.get('button[aria-label="Undo"]').click();
    cy.get('rect').should('have.length.at.least', 1);
    
    // Redo deletion
    cy.get('button[aria-label="Redo"]').click();
    cy.get('rect').should('have.length', 0);
  });
});