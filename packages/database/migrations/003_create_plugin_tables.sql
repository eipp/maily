-- Migration: Create Plugin System Tables
-- This migration adds tables required for the plugin management system

-- Create plugins table
CREATE TABLE IF NOT EXISTS plugins (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    author VARCHAR(255),
    website VARCHAR(255),
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create plugin_settings table
CREATE TABLE IF NOT EXISTS plugin_settings (
    id SERIAL PRIMARY KEY,
    plugin_id INTEGER NOT NULL REFERENCES plugins(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    settings JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_plugins_name ON plugins(name);
CREATE INDEX IF NOT EXISTS idx_plugins_is_enabled ON plugins(is_enabled);
CREATE INDEX IF NOT EXISTS idx_plugin_settings_plugin_id ON plugin_settings(plugin_id);
CREATE INDEX IF NOT EXISTS idx_plugin_settings_user_id ON plugin_settings(user_id);

-- Create unique constraint for plugin settings per user
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_plugin_user_setting
ON plugin_settings(plugin_id, user_id)
WHERE user_id IS NOT NULL;

-- Create unique constraint for global plugin settings (where user_id is NULL)
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_plugin_global_setting
ON plugin_settings(plugin_id)
WHERE user_id IS NULL;

-- Add audit trigger for tracking updates to plugins
CREATE OR REPLACE FUNCTION update_plugin_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_plugin_timestamp ON plugins;
CREATE TRIGGER update_plugin_timestamp
BEFORE UPDATE ON plugins
FOR EACH ROW
EXECUTE FUNCTION update_plugin_timestamp();

-- Add audit trigger for tracking updates to plugin settings
DROP TRIGGER IF EXISTS update_plugin_settings_timestamp ON plugin_settings;
CREATE TRIGGER update_plugin_settings_timestamp
BEFORE UPDATE ON plugin_settings
FOR EACH ROW
EXECUTE FUNCTION update_plugin_timestamp();
