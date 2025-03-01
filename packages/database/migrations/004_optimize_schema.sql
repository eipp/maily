-- Migration: 004_optimize_schema.sql
-- Purpose: Optimize database schema with proper indexing and relationships
-- Optimizes performance for common queries and ensures data integrity

-- Add indexes for commonly queried fields
CREATE INDEX IF NOT EXISTS idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_created_at ON campaigns(created_at);
CREATE INDEX IF NOT EXISTS idx_email_templates_user_id ON email_templates(user_id);
CREATE INDEX IF NOT EXISTS idx_email_templates_is_public ON email_templates(is_public);
CREATE INDEX IF NOT EXISTS idx_user_configs_model_name ON user_configs(model_name);
CREATE INDEX IF NOT EXISTS idx_consent_records_user_id ON consent_records(user_id);
CREATE INDEX IF NOT EXISTS idx_plugin_settings_plugin_id ON plugin_settings(plugin_id);

-- Add composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_campaigns_user_id_status ON campaigns(user_id, status);
CREATE INDEX IF NOT EXISTS idx_campaigns_user_id_created_at ON campaigns(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_email_templates_user_id_is_public ON email_templates(user_id, is_public);

-- Add partial indexes for frequently filtered subsets
CREATE INDEX IF NOT EXISTS idx_campaigns_active ON campaigns(user_id) WHERE status != 'deleted';
CREATE INDEX IF NOT EXISTS idx_email_templates_public ON email_templates(id) WHERE is_public = true;
CREATE INDEX IF NOT EXISTS idx_consent_records_active ON consent_records(user_id) WHERE is_active = true;

-- Add GIN indexes for JSON/JSONB columns for efficient querying
CREATE INDEX IF NOT EXISTS idx_campaigns_metadata_gin ON campaigns USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_campaigns_analytics_data_gin ON campaigns USING GIN (analytics_data);
CREATE INDEX IF NOT EXISTS idx_email_templates_tags_gin ON email_templates USING GIN (tags);

-- Create contacts table with proper indexing
CREATE TABLE IF NOT EXISTS contacts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    metadata JSONB,
    tags JSONB,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, email)
);

CREATE INDEX IF NOT EXISTS idx_contacts_user_id ON contacts(user_id);
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
CREATE INDEX IF NOT EXISTS idx_contacts_status ON contacts(status);
CREATE INDEX IF NOT EXISTS idx_contacts_metadata_gin ON contacts USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_contacts_tags_gin ON contacts USING GIN (tags);

-- Create campaign_contacts junction table for many-to-many relationship
CREATE TABLE IF NOT EXISTS campaign_contacts (
    campaign_id INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending',
    sent_at TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (campaign_id, contact_id)
);

CREATE INDEX IF NOT EXISTS idx_campaign_contacts_campaign_id ON campaign_contacts(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_contacts_contact_id ON campaign_contacts(contact_id);
CREATE INDEX IF NOT EXISTS idx_campaign_contacts_status ON campaign_contacts(status);

-- Create canvas_states table for collaborative editing
CREATE TABLE IF NOT EXISTS canvas_states (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    campaign_id INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
    state JSONB NOT NULL,
    thumbnail TEXT,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_canvas_states_user_id ON canvas_states(user_id);
CREATE INDEX IF NOT EXISTS idx_canvas_states_campaign_id ON canvas_states(campaign_id);

-- Create canvas_collaborations table for tracking collaborators
CREATE TABLE IF NOT EXISTS canvas_collaborations (
    id SERIAL PRIMARY KEY,
    canvas_id INTEGER REFERENCES canvas_states(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'editor',
    last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(canvas_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_canvas_collaborations_canvas_id ON canvas_collaborations(canvas_id);
CREATE INDEX IF NOT EXISTS idx_canvas_collaborations_user_id ON canvas_collaborations(user_id);

-- Add connection pooling configuration table
CREATE TABLE IF NOT EXISTS db_connection_pool_config (
    id SERIAL PRIMARY KEY,
    pool_name VARCHAR(50) NOT NULL UNIQUE,
    min_size INTEGER NOT NULL DEFAULT 5,
    max_size INTEGER NOT NULL DEFAULT 20,
    max_idle_time INTEGER NOT NULL DEFAULT 300, -- seconds
    max_lifetime INTEGER NOT NULL DEFAULT 3600, -- seconds
    idle_timeout INTEGER NOT NULL DEFAULT 60, -- seconds
    checkout_timeout INTEGER NOT NULL DEFAULT 30, -- seconds
    max_retrys INTEGER NOT NULL DEFAULT 3,
    retry_delay INTEGER NOT NULL DEFAULT 500, -- milliseconds
    is_active BOOLEAN DEFAULT true,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default connection pool configuration
INSERT INTO db_connection_pool_config
(pool_name, min_size, max_size, max_idle_time, max_lifetime, idle_timeout, checkout_timeout, max_retrys, retry_delay)
VALUES
('default', 5, 20, 300, 3600, 60, 30, 3, 500),
('analytics', 3, 10, 600, 7200, 120, 60, 3, 500),
('read_replica', 5, 30, 300, 3600, 60, 30, 3, 500)
ON CONFLICT (pool_name) DO NOTHING;
