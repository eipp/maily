# Maily Testing Framework

This directory contains the testing framework for the Maily application. The tests are organized into different categories based on their scope and purpose.

## Test Structure

- **Unit Tests** (`tests/unit/`): Tests for individual components and functions in isolation.
- **Integration Tests** (`tests/integration/`): Tests for interactions between components and external services.
- **End-to-End Tests** (`tests/e2e/`): Tests for complete user flows through the application.
- **Performance Tests** (`tests/performance/`): Tests for measuring and ensuring performance metrics.
- **AI Component Tests** (`tests/unit/test_ai_components.py`): Specialized tests for AI-related components.

## Running Tests

### Unit Tests

```bash
# Run all unit tests
pytest tests/unit/

# Run specific unit test file
pytest tests/unit/test_octotools_service.py

# Run JavaScript/TypeScript unit tests
npm run test:unit
```

### Integration Tests

```bash
# Run all integration tests
pytest tests/integration/

# Run specific integration test file
pytest tests/integration/test_ai_adapters.py
```

### End-to-End Tests

```bash
# Run all E2E tests
npx playwright test tests/e2e/

# Run specific E2E test file
npx playwright test tests/e2e/test_ai_campaign_flow.py

# Run with UI mode for debugging
npx playwright test --ui
```

### Performance Tests

```bash
# Run all performance tests
npx playwright test tests/performance/

# Run specific performance test
npx playwright test tests/performance/test_canvas_performance.js
```

### AI Component Tests

```bash
# Run all AI component tests
npm run test:ai-components
```

## Test Coverage

To generate test coverage reports:

```bash
# Python coverage
pytest --cov=. --cov-report=html tests/

# JavaScript/TypeScript coverage
npm run test:coverage
```

Coverage reports will be generated in the `htmlcov/` directory for Python and `coverage/` directory for JavaScript/TypeScript.

## Continuous Integration

Tests are automatically run in the CI pipeline on every push to the `main` and `develop` branches, as well as on pull requests to these branches. The CI pipeline is configured in `.github/workflows/test.yml`.

## Writing Tests

### Unit Tests

Unit tests should focus on testing a single function or component in isolation. External dependencies should be mocked.

Example:

```python
def test_register_tool():
    # Arrange
    service = OctoToolsService()
    service._client = MagicMock()
    service._client.post.return_value = AsyncMock(
        status_code=200,
        json=AsyncMock(return_value={"id": "tool-123"})
    )

    # Act
    result = await service.register_tool("test-tool", {"key": "value"})

    # Assert
    assert result == {"id": "tool-123"}
    service._client.post.assert_called_once_with(
        "/tools",
        json={"name": "test-tool", "config": {"key": "value"}}
    )
```

### Integration Tests

Integration tests should focus on testing the interaction between components and external services.

Example:

```python
def test_generate_text():
    # Arrange
    adapter = OpenAIAdapter(api_key="test-key")
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Generated text"))]
    mock_response.model = "gpt-4"
    mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=20)

    with patch("openai.ChatCompletion.create", return_value=mock_response):
        # Act
        result = await adapter.generate_text("Test prompt")

        # Assert
        assert result.content == "Generated text"
        assert result.model == "gpt-4"
        assert result.usage.prompt_tokens == 10
        assert result.usage.completion_tokens == 20
```

### End-to-End Tests

End-to-end tests should focus on testing complete user flows through the application.

Example:

```python
def test_ai_campaign_creation_flow(page):
    # Login
    login_user(page)

    # Navigate to campaigns page
    page.click("text=Campaigns")
    page.wait_for_selector("text=Create Campaign")

    # Create new campaign
    page.click("text=Create Campaign")
    page.fill("input[name='campaign-name']", "Test Campaign")
    page.click("text=Next")

    # Verify campaign was created
    page.wait_for_selector("text=Test Campaign")
    assert page.is_visible("text=Test Campaign")
```

### Performance Tests

Performance tests should focus on measuring and ensuring performance metrics.

Example:

```javascript
test('Canvas initial render performance', async ({ page }) => {
  const renderTime = await page.evaluate(() => {
    performance.mark('canvas-render-start');
    // Force a re-render
    document.querySelector('.canvas-container').style.display = 'none';
    document.querySelector('.canvas-container').offsetHeight;
    document.querySelector('.canvas-container').style.display = 'block';

    return new Promise(resolve => {
      requestAnimationFrame(() => {
        performance.mark('canvas-render-end');
        performance.measure('canvas-render', 'canvas-render-start', 'canvas-render-end');
        const measurements = performance.getEntriesByName('canvas-render');
        resolve(measurements[0].duration);
      });
    });
  });

  expect(renderTime).toBeLessThan(RENDER_TIME_THRESHOLD);
});
```

## Best Practices

1. **Isolation**: Tests should be isolated from each other and should not depend on the state of other tests.
2. **Deterministic**: Tests should be deterministic and should not depend on external factors.
3. **Fast**: Tests should be fast to run to encourage frequent testing.
4. **Comprehensive**: Tests should cover all critical paths and edge cases.
5. **Maintainable**: Tests should be easy to maintain and update as the codebase evolves.
6. **Clear**: Tests should clearly indicate what they are testing and what the expected outcome is.
7. **Mocking**: External dependencies should be mocked to ensure tests are isolated and deterministic.
8. **Fixtures**: Use fixtures to set up common test data and environments.
9. **Cleanup**: Tests should clean up after themselves to avoid affecting other tests.
10. **CI Integration**: Tests should be integrated into the CI pipeline to ensure they are run on every change.

## Test Environment

The test environment is configured to be as close as possible to the production environment, but with test-specific configurations:

- Test database with test data
- Mock external services where appropriate
- Environment variables for test-specific configurations

## Troubleshooting

If tests are failing, check the following:

1. Are all dependencies installed?
2. Are environment variables set correctly?
3. Is the test database configured correctly?
4. Are external services mocked correctly?
5. Are there any network issues affecting integration tests?
6. Are there any timing issues affecting end-to-end tests?

For more help, contact the development team.
