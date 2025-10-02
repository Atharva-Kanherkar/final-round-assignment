"""Increase job_title column length to handle longer titles

Revision ID: 002
Revises: 001
Create Date: 2025-10-02

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    """Increase VARCHAR limits for title fields."""
    # Increase job_title in sessions table
    op.alter_column('sessions', 'job_title',
                    existing_type=sa.String(255),
                    type_=sa.String(500),
                    existing_nullable=False)

    # Increase job_title in final_reports table
    op.alter_column('final_reports', 'job_title',
                    existing_type=sa.String(255),
                    type_=sa.String(500),
                    existing_nullable=False)


def downgrade():
    """Revert VARCHAR limits."""
    op.alter_column('sessions', 'job_title',
                    existing_type=sa.String(500),
                    type_=sa.String(255),
                    existing_nullable=False)

    op.alter_column('final_reports', 'job_title',
                    existing_type=sa.String(500),
                    type_=sa.String(255),
                    existing_nullable=False)
