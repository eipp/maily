-- Rollback for baseline migration
-- Warning: This will drop all tables and data!
-- Only use in development or when you have backups

-- Drop indexes
DROP INDEX IF EXISTS idx_user_plugins_plugin_id;
DROP INDEX IF EXISTS idx_user_plugins_user_id;
DROP INDEX IF EXISTS idx_user_consents_purpose_id;
DROP INDEX IF EXISTS idx_user_consents_user_id;
DROP INDEX IF EXISTS idx_templates_user_id;
DROP INDEX IF EXISTS idx_api_keys_user_id;
DROP INDEX IF EXISTS idx_sessions_user_id;
DROP INDEX IF EXISTS idx_accounts_user_id;

-- Drop plugin tables
DROP TABLE IF EXISTS user_plugins CASCADE;
DROP TABLE IF EXISTS plugins CASCADE;

-- Drop consent tables
DROP TABLE IF EXISTS user_consents CASCADE;
DROP TABLE IF EXISTS consent_purposes CASCADE;

-- Drop template tables
DROP TABLE IF EXISTS templates CASCADE;

-- Drop API keys tables
DROP TABLE IF EXISTS api_key_scopes CASCADE;
DROP TABLE IF EXISTS api_keys CASCADE;

-- Drop auth tables
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Drop migration history table
DELETE FROM migration_history WHERE migration_name = '20250303183957_baseline'; 