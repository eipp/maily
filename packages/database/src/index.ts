/**
 * Maily Database Package
 *
 * This package uses SQLAlchemy for database operations.
 * For TypeScript/JavaScript services, use the database API endpoints.
 *
 * Python services should import directly from the Python modules:
 * - from packages.database.src.models import User, Campaign, etc.
 * - from packages.database.src.client import get_db, get_db_dependency
 */

export const databaseInfo = {
  type: 'sqlalchemy',
  modelsPath: 'packages/database/src/models.py',
  clientPath: 'packages/database/src/client.py',
};

// Database client and models
export * from './client';
export * from './models';
export * from './schemas';
export * from './migrations';
