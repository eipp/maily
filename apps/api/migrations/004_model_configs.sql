-- Migration to create model_configs table
-- This stores configuration data for AI models

-- Create the model_configs table
CREATE TABLE IF NOT EXISTS model_configs (
    id VARCHAR(255) PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    model_name VARCHAR(255) NOT NULL,
    provider VARCHAR(255) NOT NULL,
    api_key TEXT NOT NULL,
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 1000,
    parameters JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER DEFAULT 0
);

-- Add indexes for common query patterns
CREATE INDEX idx_model_configs_model_name ON model_configs(model_name);
CREATE INDEX idx_model_configs_provider ON model_configs(provider);
CREATE INDEX idx_model_configs_user_id ON model_configs(user_id);
CREATE INDEX idx_model_configs_is_default ON model_configs(is_default);
CREATE INDEX idx_model_configs_is_active ON model_configs(is_active);
CREATE INDEX idx_model_configs_model_provider ON model_configs(model_name, provider);