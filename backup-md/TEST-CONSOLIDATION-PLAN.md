# Test Consolidation Plan

This document outlines the strategy for consolidating and standardizing all test implementations across the Maily platform.

## Current Status

The repository currently contains test implementations in multiple locations with significant duplication:

1. **Duplicated Unit Tests**:
   - Tests in `/tests/unit/` and service-specific locations like `/apps/api/tests/unit/`
   - Identical test files including `test_ai_service.py`, `test_ai_agents.py`, and `test_dependencies.py`
   - Duplicated test fixtures in multiple `conftest.py` files

2. **Scattered Integration Tests**:
   - Tests in `/tests/integration/` and service-specific directories
   - Inconsistent approaches to mocking external services
   - Duplicated test cases for workflows and health checks

3. **Mixed E2E Test Frameworks**:
   - Both Cypress (`.cy.ts`) and Playwright (`.spec.ts`) tests
   - Python E2E tests alongside TypeScript/JavaScript tests
   - Duplicated flows (auth, campaign creation, etc.)

4. **Limited Shared Testing Utilities**:
   - Duplicated mock implementations for Redis, DB, and API services
   - Inconsistent test data generation

5. **Inconsistent Naming Conventions**:
   - Mixed file naming patterns (`test_*.py`, `*_test.py`, `.test.ts`, `.spec.ts`)
   - Inconsistent organization (by feature vs. by component)

## Consolidation Goals

1. **Eliminate Test Duplication**:
   - Consolidate identical tests into a single implementation
   - Share test fixtures and utilities across test suites

2. **Standardize Test Organization**:
   - Establish clear locations for each type of test
   - Consistent directory structure across the repository

3. **Unified Test Frameworks**:
   - Select primary frameworks for each test type
   - Standardize on configuration and patterns

4. **Shared Test Utilities**:
   - Create shared mocks, fixtures, and data generators
   - Standard patterns for common testing scenarios

5. **Consistent Naming and Organization**:
   - Establish and document naming conventions
   - Clarify organization principles for tests

## Implementation Plan

### 1. Create Shared Testing Package

**Task**: Implement a shared testing package with common utilities.

- [ ] Create `/packages/testing/` package structure
- [ ] Move common mocks (Redis, DB, API) to appropriate modules
- [ ] Implement shared fixtures for common scenarios
- [ ] Create test data generators
- [ ] Document usage patterns and best practices

### 2. Standardize Unit Tests

**Task**: Consolidate unit tests to a single pattern.

- [ ] Decide on unit test location pattern (repository-level vs. service-specific)
- [ ] Identify and merge duplicate test files
- [ ] Standardize import patterns and mock usage
- [ ] Update CI configuration to reflect new structure

### 3. Consolidate Integration Tests

**Task**: Standardize integration test structure.

- [ ] Define clear separation between service-specific and cross-service tests
- [ ] Implement shared test data and fixtures
- [ ] Standardize on test bridge patterns
- [ ] Remove duplicated test cases

### 4. Standardize E2E Tests

**Task**: Select and standardize E2E testing approach.

- [ ] Choose primary E2E framework (Playwright vs. Cypress)
- [ ] Implement page object pattern for UI tests
- [ ] Create shared test user and authentication management
- [ ] Document E2E test creation process

### 5. Establish Naming and Organization Conventions

**Task**: Document and implement consistent naming and organization.

- [ ] Define file naming conventions for all test types
- [ ] Establish directory structure standards
- [ ] Create test categorization system (markers, tags)
- [ ] Update READMEs with conventions

## Migration Strategy

1. **Phase 1**: Create shared testing package and update critical tests
2. **Phase 2**: Migrate unit tests to standard pattern
3. **Phase 3**: Consolidate integration tests
4. **Phase 4**: Standardize E2E tests
5. **Phase 5**: Implement consistent naming and organization

## Testing the Tests

1. **Coverage Verification**: Ensure test consolidation maintains code coverage
2. **CI Integration**: Update CI pipelines to validate tests
3. **Documentation**: Include examples and guidelines for each test type

## Implementation Schedule

- Week 1: Create shared testing package
- Week 2: Standardize unit tests
- Week 3: Consolidate integration tests
- Week 4: Standardize E2E tests
- Week 5: Establish naming and organization conventions

## Acceptance Criteria

1. No duplicate test implementations across the repository
2. All tests following standardized patterns and conventions
3. Comprehensive shared testing utilities package
4. Clear documentation for creating and maintaining tests
5. All tests passing in CI pipeline

## Long-Term Maintenance

1. **Test Templates**: Create templates for new tests
2. **Review Process**: Include test structure in code review checklist
3. **Test Quality Metrics**: Monitor test quality and coverage