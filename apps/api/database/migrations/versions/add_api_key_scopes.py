"""Add scopes field to the API key table.

Revision ID: a2b9c4d5e6f7
Revises: previous_revision_id
Create Date: 2025-02-28 14:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
import uuid


# revision identifiers, used by Alembic.
revision = 'a2b9c4d5e6f7'
down_revision = 'previous_revision_id'  # Replace with the actual previous revision ID
branch_labels = None
depends_on = None


def upgrade():
    # Add the scopes column to the api_keys table
    op.add_column('api_keys', sa.Column('scopes', JSONB, nullable=True))

    # Set default scopes for existing API keys (["*"] grants full access)
    op.execute("UPDATE api_keys SET scopes = '[]'::jsonb WHERE scopes IS NULL")

    # Make the column non-nullable after populating it
    op.alter_column('api_keys', 'scopes', nullable=False)

    # Update prefix for existing API keys from maily_ to mil_ for consistency
    # Create a function to update API keys while maintaining their hash
    op.execute("""
    CREATE OR REPLACE FUNCTION update_api_key_hash() RETURNS VOID AS $$
    DECLARE
        r RECORD;
    BEGIN
        FOR r IN SELECT id, hashed_key FROM api_keys WHERE hashed_key NOT LIKE 'mil_%' LOOP
            -- Here we are just marking them for future identification
            -- The actual key value can't be changed since we only store the hash
            UPDATE api_keys SET hashed_key = 'migrated_' || hashed_key WHERE id = r.id;
        END LOOP;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # Execute the function to update API key hashes
    op.execute("SELECT update_api_key_hash()")

    # Drop the function
    op.execute("DROP FUNCTION update_api_key_hash()")


def downgrade():
    # Remove the scopes column
    op.drop_column('api_keys', 'scopes')

    # We can't undo the hash prefix updates since we don't have the original values
