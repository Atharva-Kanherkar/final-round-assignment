"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2025-10-02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial tables."""
    # Create sessions table (using String for status to avoid enum issues)
    op.create_table(
        'sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('candidate_name', sa.String(255), nullable=False),
        sa.Column('job_title', sa.String(255), nullable=False),
        sa.Column('company', sa.String(255), nullable=False),
        sa.Column('candidate_profile', sa.JSON(), nullable=False),
        sa.Column('job_requirements', sa.JSON(), nullable=False),
        sa.Column('topics', sa.JSON(), nullable=False),
        sa.Column('current_topic', sa.String(100), nullable=False),
        sa.Column('current_topic_index', sa.Integer(), default=0),
        sa.Column('status', sa.String(20), nullable=False),  # Using String instead of Enum
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('questions_asked', sa.Integer(), default=0),
        sa.Column('average_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Add check constraint for valid status values
    op.create_check_constraint(
        'valid_status',
        'sessions',
        "status IN ('active', 'paused', 'completed')"
    )

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('topic', sa.String(100), nullable=False),
        sa.Column('msg_metadata', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
    )

    # Create evaluations table
    op.create_table(
        'evaluations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', UUID(as_uuid=True), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('response', sa.Text(), nullable=False),
        sa.Column('topic', sa.String(100), nullable=False),
        sa.Column('technical_accuracy', sa.Float(), nullable=False),
        sa.Column('depth', sa.Float(), nullable=False),
        sa.Column('clarity', sa.Float(), nullable=False),
        sa.Column('relevance', sa.Float(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('strengths', sa.JSON(), nullable=True),
        sa.Column('gaps', sa.JSON(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
    )

    # Create final_reports table
    op.create_table(
        'final_reports',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('candidate_name', sa.String(255), nullable=False),
        sa.Column('job_title', sa.String(255), nullable=False),
        sa.Column('duration_minutes', sa.Float(), nullable=False),
        sa.Column('total_questions', sa.Integer(), nullable=False),
        sa.Column('topics_covered', sa.JSON(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('topic_summaries', sa.JSON(), nullable=False),
        sa.Column('overall_strengths', sa.JSON(), nullable=True),
        sa.Column('areas_for_improvement', sa.JSON(), nullable=True),
        sa.Column('recommendation', sa.String(50), nullable=False),
        sa.Column('additional_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
    )

    # Create indexes
    op.create_index('idx_sessions_status', 'sessions', ['status'])
    op.create_index('idx_sessions_created', 'sessions', ['created_at'])
    op.create_index('idx_messages_session', 'messages', ['session_id'])
    op.create_index('idx_evaluations_session', 'evaluations', ['session_id'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index('idx_evaluations_session')
    op.drop_index('idx_messages_session')
    op.drop_index('idx_sessions_created')
    op.drop_index('idx_sessions_status')

    op.drop_table('final_reports')
    op.drop_table('evaluations')
    op.drop_table('messages')
    op.drop_table('sessions')
