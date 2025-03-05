# AI Mesh Network Integration Testing

This document provides guidance on testing the AI Mesh Network integration with Cognitive Canvas in the Maily platform.

## Overview

The AI Mesh Network is a distributed system of AI agents that collaborate to provide real-time analysis, suggestions, and verification for content created in the Cognitive Canvas. The testing strategy covers both functional (E2E) testing and performance testing.

## End-to-End Testing

The E2E tests verify that:
1. Canvas operations correctly integrate with the AI Mesh Network
2. Real-time collaboration works through the WebSocket connections
3. AI-assisted operations function correctly
4. Trust verification processes work end-to-end

### Running E2E Tests

To run the AI Mesh Network integration E2E tests:

```bash
# Run all E2E tests
npm run test:e2e

# Run only AI Mesh integration tests
npm run test:e2e -- --spec "tests/e2e/ai-mesh-integration.cy.ts"

# Run in interactive mode
npm run cypress:open
```

### Test Structure

The `ai-mesh-integration.cy.ts` file contains tests for:

- Canvas editing with AI Mesh Network integration
- Real-time collaboration via WebSockets
- AI-assisted canvas operations
- Trust verification processes

Each test mocks the relevant API endpoints and WebSocket connections to ensure tests are reliable and don't require external services to be running.

## Performance Testing

Performance tests measure:
1. AI Mesh Network response times under load
2. WebSocket message throughput
3. System behavior under high concurrency
4. Resource utilization

### Running Performance Tests

To run the AI Mesh Network performance tests using k6:

```bash
# Install k6 if not already installed
# MacOS: brew install k6
# Linux: follow instructions at https://k6.io/docs/getting-started/installation/

# Run the test against staging environment
k6 run -e API_URL=https://staging-api.maily.app tests/performance/ai_mesh_canvas_performance.js

# Run a specific scenario
k6 run -e API_URL=https://staging-api.maily.app --tag scenario=websocket_test tests/performance/ai_mesh_canvas_performance.js
```

### Performance Test Scenarios

The performance tests include three scenarios:

1. **Load Test**: Moderate user load gradually increasing to 20 concurrent users
   ```bash
   k6 run -e API_URL=https://staging-api.maily.app --tag scenario=load_test tests/performance/ai_mesh_canvas_performance.js
   ```

2. **Stress Test**: Higher concurrency with up to 50 concurrent users creating multiple tasks
   ```bash
   k6 run -e API_URL=https://staging-api.maily.app --tag scenario=stress_test tests/performance/ai_mesh_canvas_performance.js
   ```

3. **WebSocket Test**: Tests WebSocket connection performance with 10 concurrent users
   ```bash
   k6 run -e API_URL=https://staging-api.maily.app --tag scenario=websocket_test tests/performance/ai_mesh_canvas_performance.js
   ```

### Performance Thresholds

The tests enforce the following performance thresholds:

- HTTP request duration: 95% of requests under 500ms, 99% under 1000ms
- Canvas load time: 95% of loads under 800ms
- AI agent response time: 90% of responses under 2000ms
- Full operation time: 90% of operations under 5000ms
- WebSocket messages: At least 100 messages processed during the test
- Task creation success rate: Above 95%
- Network creation success rate: Above 98%

## Test Implementation Details

### Mocking WebSocket Connections

The E2E tests use Cypress's stub capability to mock WebSocket connections:

```javascript
cy.window().then((win) => {
  cy.stub(win, 'WebSocket').returns({
    send: cy.stub(),
    close: cy.stub(),
    addEventListener: (event, callback) => {
      // Simulate WebSocket behaviors
    }
  });
});
```

### Simulating AI Agent Responses

Tests simulate AI agent responses by triggering mock WebSocket messages:

```javascript
cy.window().then((win) => {
  const messageEvent = {
    data: JSON.stringify({
      type: 'task_update',
      task_id: 'test-task-id',
      status: 'completed',
      data: { /* Mock response data */ }
    })
  };
  
  win.messageCallback(messageEvent);
});
```

## Troubleshooting

### E2E Test Failures

Common issues with E2E tests:

- **Intercepted requests not matching**: Check the API endpoint paths in the test match the application
- **WebSocket mocks not working**: Ensure the application is using the standard WebSocket API
- **UI elements not found**: Verify aria-labels and other selectors match the application

### Performance Test Failures

Common issues with performance tests:

- **Connection failures**: Check network connectivity to the test environment
- **Authentication failures**: Verify the test-login endpoint is available
- **Threshold violations**: Review recent changes that might have affected performance
- **WebSocket errors**: Check the WebSocket URLs are correctly formatted

## Adding New Tests

When adding new tests:

1. Follow the existing patterns for mocking WebSockets and API responses
2. Add specific assertions to verify AI mesh behaviors
3. Keep performance tests focused on realistic user scenarios
4. Update this documentation with any new test scenarios