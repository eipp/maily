-- Add indexes for frequently queried columns
CREATE INDEX IF NOT EXISTS idx_user_configs_email ON user_configs(email);
CREATE INDEX IF NOT EXISTS idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_created_at ON campaigns(created_at);

-- Add composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_campaigns_user_status ON campaigns(user_id, status);
CREATE INDEX IF NOT EXISTS idx_campaigns_status_date ON campaigns(status, created_at DESC);

-- Add indexes for full-text search
CREATE INDEX IF NOT EXISTS idx_campaigns_subject_trgm ON campaigns USING gin(subject gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_campaigns_body_trgm ON campaigns USING gin(body gin_trgm_ops);

-- Add partial index for active campaigns
CREATE INDEX IF NOT EXISTS idx_active_campaigns ON campaigns(user_id, created_at DESC)
WHERE status = 'active';

-- Add index for analytics queries
CREATE INDEX IF NOT EXISTS idx_campaigns_analytics ON campaigns USING gin(analytics_data);
