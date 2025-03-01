-- Migration: Create Consent Management Tables
-- This migration adds tables required for GDPR-compliant consent management

-- Create users table if it doesn't exist yet
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create consent_records table
CREATE TABLE IF NOT EXISTS consent_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    marketing_emails BOOLEAN DEFAULT FALSE,
    data_analytics BOOLEAN DEFAULT FALSE,
    third_party_sharing BOOLEAN DEFAULT FALSE,
    personalization BOOLEAN DEFAULT FALSE,
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_consent_user_id ON consent_records(user_id);
CREATE INDEX IF NOT EXISTS idx_consent_is_active ON consent_records(is_active);
CREATE INDEX IF NOT EXISTS idx_consent_created_at ON consent_records(created_at);

-- Create composite index for common query pattern
CREATE INDEX IF NOT EXISTS idx_consent_user_active ON consent_records(user_id, is_active);

-- Add audit trigger for tracking updates to consent records
CREATE OR REPLACE FUNCTION update_consent_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_consent_timestamp ON consent_records;
CREATE TRIGGER update_consent_timestamp
BEFORE UPDATE ON consent_records
FOR EACH ROW
EXECUTE FUNCTION update_consent_timestamp();
