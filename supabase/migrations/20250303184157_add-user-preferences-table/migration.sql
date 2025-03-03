-- Migration: add-user-preferences-table
-- Created at: Mon Mar  3 18:41:57 EET 2025
-- Description: Add user preferences table

-- Create user_preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    preference_key TEXT NOT NULL,
    preference_value JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, preference_key)
);

-- Add index for better performance
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);

-- Update migration history table
INSERT INTO migration_history (migration_name, migration_description)
VALUES ('20250303184157_add-user-preferences-table', 'Add user preferences table')
ON CONFLICT (migration_name) DO NOTHING;
