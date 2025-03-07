# HTTP & Redis Migration Plan

This document outlines the plan for migrating from deprecated HTTP libraries (requests/aiohttp) and non-standardized Redis implementations to our standardized clients.

## Progress Summary

### HTTP Client Migration Progress
- **Completed**: 
  - `apps/ai-service/utils/tracing.py` - Updated OpenTelemetry instrumentation
  - `tests/performance/ai_mesh_load_test.py` - Converted to use standardized client
  
- **In Progress**:
  - `apps/api/utils/tracing.py`
  - Tests and remaining service integrations

### Redis Client Migration Progress
- **Completed**:
  - `apps/api/utils/cache_manager.py` - Already using standardized client
  - `apps/ai-service/implementations/memory/vector_embeddings.py` - Converted to use standardized client
  
- **In Progress**:
  - Memory indexing and compression implementations
  - AI mesh network session management

## HTTP Client Migration (requests/aiohttp → httpx)

### Remaining Files to Migrate

The following key files still need migration:
- `apps/api/tests/integration/test_service_mesh_integration.py`
- `apps/api/utils/tracing.py`
- `tests/performance/ai_mesh_chaos_test.py`
- `scripts/test-opentelemetry.py`
- `scripts/testing/load-testing/load_test.py`
- `apps/api/monitoring/tracing.py`

### Implementation Plan

1. **Phase 1: Core Services** (In Progress)
   - ✅ Migrate AI service HTTP clients
   - ⬜ Migrate API service HTTP clients
   - ⬜ Update integration tests
   - ⬜ Validate functionality

2. **Phase 2: Testing & Utilities** (Partially Completed)
   - ✅ Migrated AI Mesh load testing script
   - ⬜ Migrate remaining testing scripts
   - ⬜ Migrate utility modules
   - ⬜ Validate test functionality

3. **Phase 3: Dependency Removal** (Not Started)
   - ⬜ Update requirements files to remove requests/aiohttp
   - ⬜ Run tests to ensure no regressions
   - ⬜ Update Docker builds

## Redis Client Migration

### Remaining Files to Migrate

The following key files still need migration:
- `apps/api/routers/health.py`
- `apps/api/routers/campaigns.py`
- `apps/api/database/dependencies.py`
- `apps/api/endpoints/health.py`
- `apps/api/services/canvas_service.py`
- `apps/api/scripts/cleanup.py`
- `apps/ai-service/routers/websocket_router.py`
- `apps/ai-service/services/agent_coordinator.py`

### Implementation Plan

1. **Phase 1: Core Services** (In Progress)
   - ⬜ Migrate API service Redis clients
   - ✅ Partially migrated AI service Redis clients
   - ⬜ Validate functionality

2. **Phase 2: Utilities & Scripts** (Partially Completed)
   - ✅ Cache manager already using standardized client
   - ⬜ Migrate remaining utility modules
   - ⬜ Migrate scripts
   - ⬜ Validate functionality

3. **Phase 3: Dependency Removal** (Not Started)
   - ⬜ Update requirements to use only redis>=5.0.0
   - ⬜ Remove aioredis references
   - ⬜ Update Docker builds

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
- Standardized HTTP client: `packages/error_handling/python/http_client.py`
- Standardized Redis client: `packages/database/src/redis/redis_client.py`

## Updated Timeline

- **Week 1**: Complete HTTP Client Phase 1 & 2 (Current)
- **Week 2**: Complete Redis Client Phase 1 & 2
- **Week 3**: Phase 3 for both + Final Testing

## Risk Mitigation

1. **Incremental Approach**: Migrate service by service
2. **Comprehensive Testing**: Test at each step
3. **Rollback Plan**: Keep backups and prepare rollback procedures
4. **Documentation**: Document issues encountered and solutions

## Recommendations for Next Files

### HTTP Client Migration
1. `apps/api/utils/tracing.py` - Similar to the AI service tracing module
2. `tests/performance/ai_mesh_chaos_test.py` - Following the pattern of the load test file

### Redis Client Migration
1. `apps/ai-service/implementations/memory/memory_compression.py` - Following vector embeddings pattern
2. `apps/ai-service/implementations/memory/memory_indexing.py` - Following vector embeddings pattern