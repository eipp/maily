"""create email templates table

Revision ID: 0a9b7cd3e102
Revises:
Create Date: 2023-05-25 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0a9b7cd3e102'
down_revision = None  # Update this with the previous migration revision ID
branch_labels = None
depends_on = None


def upgrade():
    # Create email_templates table
    op.create_table(
        'email_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('content', sa.JSON(), nullable=False),
        sa.Column('thumbnail', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('is_public', sa.Boolean(), default=False),
        sa.Column('is_featured', sa.Boolean(), default=False),
        sa.Column('version', sa.Integer(), default=1),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index on user_id for faster lookup
    op.create_index(op.f('ix_email_templates_user_id'), 'email_templates', ['user_id'], unique=False)

    # Add template_id foreign key to campaigns table
    op.add_column('campaigns', sa.Column('template_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_campaigns_template_id',
        'campaigns', 'email_templates',
        ['template_id'], ['id']
    )


def downgrade():
    # Drop foreign key in campaigns table
    op.drop_constraint('fk_campaigns_template_id', 'campaigns', type_='foreignkey')
    op.drop_column('campaigns', 'template_id')

    # Drop index and email_templates table
    op.drop_index(op.f('ix_email_templates_user_id'), table_name='email_templates')
    op.drop_table('email_templates')
