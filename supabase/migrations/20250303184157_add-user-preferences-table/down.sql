-- Rollback for migration: add-user-preferences-table
-- Created at: Mon Mar 3 18:41:57 EET 2025
-- Description: Add user preferences table

-- Drop index
DROP INDEX IF EXISTS idx_user_preferences_user_id;

-- Drop table
DROP TABLE IF EXISTS user_preferences CASCADE;

-- Remove from migration history table
DELETE FROM migration_history WHERE migration_name = '20250303184157_add-user-preferences-table';
