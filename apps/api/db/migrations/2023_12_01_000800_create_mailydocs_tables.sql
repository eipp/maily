-- Migration: Create MailyDocs Tables
-- Description: Creates tables for document management, templates, and analytics

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(64) PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    file_path VARCHAR(512),
    file_url VARCHAR(512),
    preview_url VARCHAR(512),
    template_id VARCHAR(64),
    user_id VARCHAR(64),
    campaign_id VARCHAR(64),
    tracking_id VARCHAR(64),
    personalized BOOLEAN NOT NULL DEFAULT FALSE,
    interactive BOOLEAN NOT NULL DEFAULT FALSE,
    blockchain_verified BOOLEAN NOT NULL DEFAULT FALSE,
    verification_url VARCHAR(512),
    verification_info JSONB,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT fk_documents_users FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_documents_campaigns FOREIGN KEY(campaign_id) REFERENCES campaigns(id) ON DELETE SET NULL
);

-- Create index for queries
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(type);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_campaign_id ON documents(campaign_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);

-- Document templates table
CREATE TABLE IF NOT EXISTS document_templates (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    description TEXT,
    content JSONB NOT NULL DEFAULT '{}',
    thumbnail_url VARCHAR(512),
    created_by VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT fk_templates_users FOREIGN KEY(created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Create index for template queries
CREATE INDEX IF NOT EXISTS idx_templates_type ON document_templates(type);
CREATE INDEX IF NOT EXISTS idx_templates_name ON document_templates(name);

-- Document analytics table
CREATE TABLE IF NOT EXISTS document_analytics (
    document_id VARCHAR(64) PRIMARY KEY,
    views INTEGER NOT NULL DEFAULT 0,
    unique_views INTEGER NOT NULL DEFAULT 0,
    average_view_time FLOAT NOT NULL DEFAULT 0,
    completion_rate FLOAT NOT NULL DEFAULT 0,
    engagement_by_section JSONB,
    conversion_rate FLOAT,
    additional_metrics JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT fk_analytics_documents FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- Document sections table
CREATE TABLE IF NOT EXISTS document_sections (
    id VARCHAR(64) PRIMARY KEY,
    document_id VARCHAR(64) NOT NULL,
    title VARCHAR(255),
    type VARCHAR(50) NOT NULL,
    content TEXT,
    content_json JSONB,
    order_index INTEGER NOT NULL DEFAULT 0,
    interactive BOOLEAN NOT NULL DEFAULT FALSE,
    interaction_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT fk_sections_documents FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- Create index for section queries
CREATE INDEX IF NOT EXISTS idx_sections_document_id ON document_sections(document_id);
CREATE INDEX IF NOT EXISTS idx_sections_order ON document_sections(order_index);

-- Document verification records
CREATE TABLE IF NOT EXISTS document_verifications (
    id VARCHAR(64) PRIMARY KEY,
    document_id VARCHAR(64) NOT NULL,
    hash VARCHAR(128) NOT NULL,
    blockchain_tx VARCHAR(128),
    verification_method VARCHAR(50) NOT NULL,
    verified_at TIMESTAMP WITH TIME ZONE NOT NULL,
    verification_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT fk_verifications_documents FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- Create index for verification queries
CREATE INDEX IF NOT EXISTS idx_verifications_document_id ON document_verifications(document_id);

-- Document interaction events table
CREATE TABLE IF NOT EXISTS document_interactions (
    id VARCHAR(64) PRIMARY KEY,
    document_id VARCHAR(64) NOT NULL,
    section_id VARCHAR(64),
    viewer_id VARCHAR(64),
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT fk_interactions_documents FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
    CONSTRAINT fk_interactions_sections FOREIGN KEY(section_id) REFERENCES document_sections(id) ON DELETE SET NULL
);

-- Create index for interaction queries
CREATE INDEX IF NOT EXISTS idx_interactions_document_id ON document_interactions(document_id);
CREATE INDEX IF NOT EXISTS idx_interactions_viewer_id ON document_interactions(viewer_id);
CREATE INDEX IF NOT EXISTS idx_interactions_event_type ON document_interactions(event_type);
CREATE INDEX IF NOT EXISTS idx_interactions_occurred_at ON document_interactions(occurred_at);
