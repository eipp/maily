# Campaign API Adapter Implementation

This document outlines the implementation of the adapter service that bridges the fixed and router implementations of the Campaign API.

## Overview

The adapter implementation follows a layered approach to provide compatibility between the fixed and router API versions:

1. **Authentication Bridge**: Supports both API key and Bearer token authentication methods
2. **Endpoint Standardization**: Implements router-style endpoints (`/campaigns/`) on the fixed implementation
3. **Data Model Conversion**: Converts between fixed and router data formats seamlessly
4. **Response Standardization**: Provides consistent response formatting across all endpoints

## Components

### 1. API Adapter Service (`api_adapter_service.py`)

Core adapter implementation that provides:
- `AuthAdapter`: Authentication compatibility layer
- `ModelAdapter`: Data model conversion utilities
- `ResponseAdapter`: Response format standardization
- `EndpointAdapter`: Endpoint routing between implementations

### 2. Shared Models (`models/shared_models.py`)

Unified data models that are used by both implementations:
- `CampaignStatus`: Standardized status enum (DRAFT, SCHEDULED, SENDING, etc.)
- `CampaignResponse`: Standardized campaign response model
- Standardized conversion functions between formats

### 3. Adapter Bridge (`adapter_bridge.py`)

Standalone server that provides:
- Combined API that works with both formats
- Compatibility endpoints for both implementations
- Authentication with both methods (API key and Bearer token)

### 3. API Standardization (`api_standardization.py`)

Adds missing endpoints to the fixed implementation:
- Campaign update functionality
- Campaign deletion
- Campaign analytics
- Campaign sending with batch processing

### 4. Main Adapter (`main_adapter.py`)

Main entry point for the unified adapter service:
- Combines all components into a unified API
- Handles compatibility between implementations
- Provides standardized API interface

### 5. Standardized Response Utilities (`utils/response.py`)

Response formatting utilities that ensure consistent API responses:
- `standard_response`: Creates standardized success responses
- `error_response`: Creates standardized error responses
- `paginated_response`: Creates standardized paginated responses

### 6. Background Task Service (`services/task_service.py`)

Robust task processing with:
- Task tracking with status updates
- Retry mechanism for failed tasks
- Task querying and management

### 7. Enhanced Health Monitoring (`services/health_service.py`)

Comprehensive health checks with:
- Detailed component status reporting
- Support for degraded operation modes
- Alerting based on health status

## Deployment Modes

The adapter can be deployed in three modes:

1. **Unified Mode**: Combines both implementations with full compatibility
   ```
   python3 apps/api/scripts/deploy_adapter.py --mode unified
   ```

2. **Bridge Mode**: Runs the adapter bridge as a standalone service
   ```
   python3 apps/api/scripts/deploy_adapter.py --mode bridge
   ```

3. **Standardized Mode**: Runs the fixed implementation with standardized endpoints
   ```
   python3 apps/api/scripts/deploy_adapter.py --mode standardized
   ```

## Usage Examples

### Authentication

Both authentication methods are supported:

```python
# API Key (Fixed style)
response = requests.post(
    "https://api.example.com/api/v1/campaigns",
    headers={"X-API-Key": "your-api-key"},
    json={
        "task": "Create campaign",
        "model_name": "gpt-4",
        "audience": {"segments": ["customers"]}
    }
)

# Bearer Token (Router style)
response = requests.post(
    "https://api.example.com/api/v1/campaigns",
    headers={"Authorization": "Bearer your-token"},
    json={
        "name": "New Campaign",
        "subject": "Welcome",
        "content": "<p>Hello</p>"
    }
)
```

### Endpoints

Both endpoint patterns are supported:

```python
# Fixed style endpoint
response = requests.post(
    "https://api.example.com/create_campaign",
    headers={"X-API-Key": "your-api-key"},
    json={...}
)

# Router style endpoint
response = requests.post(
    "https://api.example.com/api/v1/campaigns",
    headers={"Authorization": "Bearer your-token"},
    json={...}
)
```

## Testing

The adapter implementation includes comprehensive tests:

```bash
# Run adapter implementation tests
python -m pytest apps/api/tests/test_adapter_implementation.py

# Run full test suite with both implementations
python3 apps/api/run_tests.py --implementation both --coverage --html
```

## Implementation Progress

Phase 1 of the implementation plan has been completed:
- [x] Run the test suite to identify current pass/fail status
- [x] Make adapter service executable
- [x] Run implementation example to verify adapter functionality
- [x] Deploy adapter service in compatibility mode
  - [x] Apply authentication bridge to both implementations
  - [x] Implement endpoint routing between implementations
  - [x] Set up model conversion for request/response data

Phase 2 of the implementation plan has been completed:
- [x] Implement standardized endpoint structure
  - [x] Use router patterns `/campaigns/` as the standard
  - [x] Add compatibility endpoints in fixed implementation
  - [x] Apply consistent authentication across all endpoints
- [x] Add missing endpoints to fixed implementation

Phase 3 of the implementation plan has been completed:
- [x] Implement standardized response formats
- [x] Standardize data models with unified schema
- [x] Implement robust background task processing and health monitoring
5. Create client migration guide

## Monitoring Implementation Progress

The test runner provides detailed metrics on implementation progress:

```bash
# Track progress against both implementations
python3 apps/api/run_tests.py --implementation both --coverage --html
