# HTTP & Redis Migration Plan

This document outlines the plan for migrating from deprecated HTTP libraries (requests/aiohttp) and non-standardized Redis implementations to our standardized clients.

## Progress Summary

### HTTP Client Migration Progress
- **Completed**: 
  - `apps/ai-service/utils/tracing.py` - Updated OpenTelemetry instrumentation
  - `tests/performance/ai_mesh_load_test.py` - Converted to use standardized client
  - `apps/api/utils/tracing.py` - Fixed asyncio import order and ensured consistent instrumentation
  - `tests/performance/ai_mesh_chaos_test.py` - Migrated from aiohttp to standardized client
  - `apps/api/tests/integration/test_service_mesh_integration.py` - Replaced requests with standardized client
  - `tests/unit/test_http_client.py` - Added regression test suite for standardized HTTP client
  
- **Completed**:
  - All known HTTP client implementations have been migrated

### Redis Client Migration Progress
- **Completed**:
  - `apps/api/utils/cache_manager.py` - Already using standardized client
  - `apps/ai-service/implementations/memory/vector_embeddings.py` - Converted to use standardized client
  - `apps/api/routers/health.py` - Already using standardized client
  - `apps/ai-service/implementations/memory/memory_indexing.py` - Fixed to use correct Redis client import
  - `apps/ai-service/implementations/memory/session_management.py` - Updated to use standardized client directly
  - `apps/ai-service/metrics/ai_mesh_collector.py` - Already using standardized client
  - `apps/ai-service/routers/websocket_router.py` - Verified using standardized Redis client for PubSub
  - `apps/api/routers/websocket_router.py` - Verified using standardized Redis client for PubSub
  - `apps/api/services/canvas_service.py` - Verified using standardized Redis client
  - `apps/api/routers/campaigns.py` - Fixed to use standardized Redis client
  - `tests/unit/test_redis_client.py` - Added regression test suite for standardized Redis client
  
- **Completed**:
  - All Redis implementations have been migrated to the standardized client

## HTTP Client Migration (requests/aiohttp → httpx)

### Implementation Plan - COMPLETED

1. **Phase 1: Core Services** (COMPLETED)
   - ✅ Migrate AI service HTTP clients
   - ✅ Update API service tracing module
   - ✅ Update integration tests
   - ✅ Validate functionality

2. **Phase 2: Testing & Utilities** (COMPLETED)
   - ✅ Migrated AI Mesh load testing script
   - ✅ Migrated AI Mesh chaos testing script
   - ✅ Migrate remaining testing scripts
   - ✅ Migrate utility modules
   - ✅ Validate test functionality

3. **Phase 3: Dependency Removal** (COMPLETED)
   - ✅ Update requirements files to remove requests/aiohttp
   - ✅ Run tests to ensure no regressions
   - ✅ Update Docker builds

## Redis Client Migration

### All Files Successfully Migrated

All Redis implementations have been successfully migrated to the standardized client.

### Implementation Plan

1. **Phase 1: Core Services** (COMPLETED)
   - ✅ Migrate API service Redis clients for Canvas, Websockets
   - ✅ Update/verify AI service memory system Redis usage
   - ✅ Validate functionality for all migrated components
   - ✅ Complete campaign management Redis migration

2. **Phase 2: Utilities & Scripts** (COMPLETED)
   - ✅ Cache manager already using standardized client
   - ✅ Memory systems migrated
   - ✅ Migrate remaining utility modules (websocket, canvas)
   - ✅ Migrate scripts
   - ✅ Validate functionality

3. **Phase 3: Dependency Removal** (COMPLETED)
   - ✅ Update requirements to use only redis>=4.5.5
   - ✅ Remove aioredis references
   - ✅ Update Docker builds

## Migration Strategy

### For Each File:

1. **Backup**: Create a backup of the file
2. **Import Update**: Replace imports with standardized client imports
3. **Implementation Update**: Replace client implementations with standardized versions
4. **Local Testing**: Test the file's functionality locally
5. **Integration Testing**: Test within the broader system
6. **Commit**: Commit changes with descriptive message

### Testing Strategy:

1. **Unit Tests**: Ensure all unit tests pass with new implementations
2. **Integration Tests**: Confirm services interact correctly
3. **End-to-End Tests**: Validate complete workflows
4. **Performance Tests**: Confirm no performance degradation

## Resources

- See [Migration Examples](./MIGRATION-EXAMPLES.md) for code examples
- Standardized HTTP client: `packages/error-handling/python/http_client.py` (imported as `packages.error_handling.python.http_client`)
- Standardized Redis client: `packages/database/src/redis/redis_client.py`

### Import Path Notes

There's an inconsistency between the directory name and import path for the error handling package:
- Directory: `packages/error-handling/` (with hyphen)
- Import: `packages.error_handling` (with underscore)

When importing the HTTP client, use:
```python
from packages.error_handling.python.http_client import HttpClient, get, post
```

Make sure your Python path includes the parent directory so these imports will work.

## Implementation Status

- **HTTP Client Migration**: COMPLETED ✅
- **Redis Client Migration**: COMPLETED ✅
- **Overall Progress**: 100% COMPLETED ✅

## Risk Mitigation

1. **Incremental Approach**: Successfully migrated service by service
2. **Comprehensive Testing**: Tests created and verified for both client types
3. **Rollback Capability**: Backups maintained for all changed files
4. **Documentation**: Migration examples and plans were comprehensive

## Completed Final Steps

1. ✅ **Campaign Management**: Successfully migrated campaign management Redis implementation
2. ✅ **End-to-End Tests**: Verified full system functionality with standardized clients
3. ✅ **Documentation**: Updated developer docs to reflect standardized client usage
4. ✅ **Final Verification**: Performed final verification to ensure all services use standardized clients

## Next Steps

1. **Monitor for Issues**: Watch for any errors related to the migration
2. **Performance Metrics**: Continue monitoring performance metrics to ensure no degradation
3. **Developer Education**: Ensure all team members are familiar with standardized clients
4. **Code Review Process**: Update code review guidelines to enforce standardized client usage