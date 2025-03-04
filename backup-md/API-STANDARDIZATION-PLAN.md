# API Standardization Plan

This document outlines the plan to complete the API standardization across the Maily platform.

## Current Status

The API currently exists in multiple forms:

1. **Fixed Implementation (`main_fixed.py`)** - Original implementation with a flat structure
2. **Standard Implementation (`main_standard.py`)** - Partially standardized implementation
3. **Adapter Implementation (`main_adapter.py`)** - Implementation using adapter pattern
4. **Secured Implementation (`main_secured.py`)** - Implementation with enhanced security
5. **Consolidated Implementation (`main.py`)** - Partially consolidated implementation with mode selection

The API standardization efforts have been started with:
- `api_standardization.py` - Adds standardized endpoints on top of fixed implementation
- `api_adapter_service.py` - Provides adapters for authentication, models, and responses

## Standardization Goals

1. **Unified API Structure**:
   - Consistent route naming (`/api/v1/resources`)
   - Consistent response format (standardized success/error responses)
   - Consistent parameter naming and casing

2. **Consistent Authentication**:
   - Support for both API keys and Bearer tokens
   - Unified authentication middleware
   - Standardized error responses for auth failures

3. **Standardized Response Format**:
   - Success responses: `{"data": {...}, "status": "success"}`
   - Error responses: `{"status": "error", "error": {"code": "ERROR_CODE", "message": "Error message", "details": {...}}}`
   - Consistent HTTP status codes

4. **OpenAPI Documentation**:
   - Comprehensive API documentation
   - Properly tagged endpoints by resource
   - Example requests and responses

## Implementation Plan

### 1. Consolidate Main Application Files

**Task**: Merge the different main implementations into a single configurable implementation.

- [x] Implement mode selection through environment variable (`APP_MODE`)
- [x] Create unified middleware stack
- [x] Standardize startup/shutdown procedures
- [x] Implement conditional imports based on mode

### 2. Complete the API Adapter Service

**Task**: Enhance the existing adapter service to cover all endpoints.

- [x] Improve AuthAdapter to handle multiple auth methods
- [x] Enhance ModelAdapter to convert between all formats
- [x] Complete ResponseAdapter for standardized responses
- [ ] Add support for all current endpoints
- [ ] Create comprehensive tests for adapters

### 3. Standardize Response Formats

**Task**: Implement consistent response formats across all endpoints.

- [ ] Create standardized response models using Pydantic
- [ ] Implement response middleware to ensure consistency
- [ ] Update all endpoints to use the standardized format
- [ ] Add support for pagination, filtering, and sorting

### 4. Consolidate Authentication

**Task**: Implement a unified authentication system.

- [ ] Create unified auth middleware that supports all methods
- [ ] Standardize scopes and permissions
- [ ] Implement role-based access control
- [ ] Create auth context with user information

### 5. Create Comprehensive OpenAPI Documentation

**Task**: Update and enhance API documentation.

- [ ] Define consistent tags for endpoint groups
- [ ] Add detailed descriptions for all endpoints
- [ ] Create example requests and responses
- [ ] Document security requirements

### 6. Update Client Libraries

**Task**: Update client libraries to work with the standardized API.

- [ ] Update JavaScript/TypeScript client
- [ ] Update Python client
- [ ] Create comprehensive tests for clients

## Migration Strategy

1. **Phase 1**: Implement the standardized API alongside existing endpoints
2. **Phase 2**: Gradually migrate clients to the standardized endpoints
3. **Phase 3**: Deprecate old endpoints with warnings
4. **Phase 4**: Remove old endpoints after migration period

## Testing Plan

1. **Unit Tests**: Test each adapter component independently
2. **Integration Tests**: Test end-to-end API flows
3. **Compatibility Tests**: Ensure backward compatibility with existing clients
4. **Performance Tests**: Verify adapter overhead is minimal
5. **Security Tests**: Verify auth mechanisms work correctly

## Implementation Schedule

- Week 1: Complete API Adapter Service
- Week 2: Standardize Response Formats
- Week 3: Consolidate Authentication
- Week 4: Create OpenAPI Documentation
- Week 5: Update Client Libraries and Run Tests
- Week 6: Begin Migration Process

## Acceptance Criteria

1. All endpoints follow standardized RESTful naming conventions
2. All responses follow the standardized format
3. Authentication works consistently across all endpoints
4. OpenAPI documentation is comprehensive and accurate
5. Client libraries work with standardized endpoints
6. All tests pass with high coverage