-- Initialize Maily development database
-- This script runs when the database container starts in development mode

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS maily;

-- Create users table
CREATE TABLE IF NOT EXISTS maily.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create email_templates table
CREATE TABLE IF NOT EXISTS maily.email_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES maily.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create contacts table
CREATE TABLE IF NOT EXISTS maily.contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES maily.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_subscribed BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, email)
);

-- Create campaigns table
CREATE TABLE IF NOT EXISTS maily.campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES maily.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    template_id UUID NOT NULL REFERENCES maily.email_templates(id),
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    scheduled_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create campaign_contacts table (junction table)
CREATE TABLE IF NOT EXISTS maily.campaign_contacts (
    campaign_id UUID NOT NULL REFERENCES maily.campaigns(id) ON DELETE CASCADE,
    contact_id UUID NOT NULL REFERENCES maily.contacts(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    sent_at TIMESTAMP WITH TIME ZONE,
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (campaign_id, contact_id)
);

-- Create email_logs table
CREATE TABLE IF NOT EXISTS maily.email_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES maily.users(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES maily.campaigns(id) ON DELETE SET NULL,
    contact_id UUID REFERENCES maily.contacts(id) ON DELETE SET NULL,
    email VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert sample data for development
INSERT INTO maily.users (email, password_hash, first_name, last_name, is_verified)
VALUES
    ('admin@example.com', crypt('password123', gen_salt('bf')), 'Admin', 'User', TRUE),
    ('user@example.com', crypt('password123', gen_salt('bf')), 'Regular', 'User', TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON maily.users(email);
CREATE INDEX IF NOT EXISTS idx_contacts_email ON maily.contacts(email);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON maily.campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaign_contacts_status ON maily.campaign_contacts(status);
CREATE INDEX IF NOT EXISTS idx_email_logs_status ON maily.email_logs(status);

-- Grant privileges
GRANT ALL PRIVILEGES ON SCHEMA maily TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA maily TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA maily TO postgres;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION maily.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON maily.users
FOR EACH ROW EXECUTE FUNCTION maily.update_updated_at_column();

CREATE TRIGGER update_email_templates_updated_at
BEFORE UPDATE ON maily.email_templates
FOR EACH ROW EXECUTE FUNCTION maily.update_updated_at_column();

CREATE TRIGGER update_contacts_updated_at
BEFORE UPDATE ON maily.contacts
FOR EACH ROW EXECUTE FUNCTION maily.update_updated_at_column();

CREATE TRIGGER update_campaigns_updated_at
BEFORE UPDATE ON maily.campaigns
FOR EACH ROW EXECUTE FUNCTION maily.update_updated_at_column();
