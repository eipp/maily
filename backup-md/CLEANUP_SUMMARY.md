# Maily Codebase Cleanup Summary

## Duplicate Implementations Removed

### 1. Redis Client Consolidation
- **Standardized Implementation**: Using shared Redis client from `packages/database/src/redis/redis_client.py`
- **Deprecated Legacy Files**:
  - `apps/api/cache/redis.py` - Added deprecation notice, now imports from shared implementation
  - `apps/api/cache/redis_service.py` - Updated to use standard implementation
- **Benefits**: Circuit breaker pattern, connection pooling, standardized error handling across services

### 2. Testing Framework Standardization
- **Standardized Implementation**: Selected Vitest as primary testing framework for JavaScript/TypeScript
- **Deprecated Legacy Files**:
  - `apps/web/jest.config.js` - Added deprecation notice, keeping for backward compatibility
- **Benefits**: Faster test execution, TypeScript-native support, simpler configuration

### 3. Next.js Configuration Cleanup
- **Standardized Implementation**: Using single `next.config.js` in web app directory
- **Archived Legacy Files**:
  - `apps/web/config-backup/next.config.js`
  - `apps/web/config-backup/next.config.mjs`
  - `apps/web/config-backup/next.config.analyzer.js`
- **Benefits**: Simplified configuration management, clear configuration source, reduced confusion

### 4. Kubernetes Backup Files Cleanup
- **Action**: Created `scripts/cleanup-k8s-backups.sh` to handle .bak files
- **Functionality**:
  - Moves existing .bak files to backup-archives directory
  - Generates git command to stop tracking non-existent backup files
- **Affected Files**: 10 .bak files in kubernetes/deployments/

## Dependency Bloat Elimination

### 1. Built-in Module Requirements
- **Removed**: asyncio from requirements-ai-ml.txt (built-in Python module)

### 2. OpenTelemetry Packages
- **Standardized**: Created central requirements file at `packages/config/monitoring/telemetry-requirements.txt`
- **Version Alignment**: Set consistent versions for all OpenTelemetry packages

### 3. GraphQL Implementations
- **Tool Created**: `scripts/standardize-graphql.js`
- **Standardization**:
  - Selected Apollo Client as standard GraphQL implementation
  - Script to update package.json files across the codebase
  - Removal of legacy libraries (apollo-boost, graphql-request, etc.)

### 4. HTTP Client Libraries
- **Tool Created**: `scripts/standardize-http-clients.py`
- **Standardization**:
  - Selected httpx as standard HTTP client
  - Script to update import statements across Python codebase
  - Consolidation from multiple clients (requests, aiohttp, urllib3)

## Implementation Progress

1. ✅ **Scripts Generated and Run**:
   - Fixed and ran `scripts/standardize-graphql.js` (found no GraphQL dependencies to update)
   - Fixed and ran `python scripts/standardize-http-clients.py apps/` (updated 9 files, 10 replacements)

2. ✅ **Requirements Files Updated**:
   - Created standardized OpenTelemetry requirements at `packages/config/monitoring/telemetry-requirements.txt`
   - Updated main `requirements.txt` to use standardized telemetry requirements
   - Marked legacy HTTP clients as deprecated in requirements.txt
   - Standardized on httpx as the primary HTTP client

3. ✅ **Kubernetes Backup Cleanup**:
   - Ran `scripts/cleanup-k8s-backups.sh` to handle .bak files
   - Created backup-archives directory
   - Checked that .bak files are no longer being tracked by git

## Remaining Tasks

1. **Create Developer Documentation**:
   - Add standard libraries to developer documentation
   - Note deprecated modules in coding guidelines
   - Update CLAUDE.md with standardized patterns

2. **Git Management**:
   - Commit changes (after review)
   - Create a PR with the standardization work