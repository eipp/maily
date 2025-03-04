# Maily Configuration Directory

This directory contains all the standardized configuration files for the Maily platform.

## Structure

- `app/` - Application-specific configurations
  - `api/` - API service configuration
  - `web/` - Web application configuration
  - `ai-service/` - AI service configuration
- `services/` - Shared service configurations
  - `redis/` - Redis configuration
  - `database/` - Database configuration
- `frontend/` - Frontend tooling configurations (jest, eslint, babel, etc.)

## Usage

All configuration should be centralized in this directory and accessed through standardized imports.
For backward compatibility, some services may have forwarding modules that import from this central location.

## Standardization

As part of the repository organization improvements, the following changes have been made:

1. Configuration files have been moved from their app-specific locations to this centralized directory
2. Forwarding modules have been created for backward compatibility
3. New code should import configurations directly from this directory