"""Add feedback table for user votes and reports

Revision ID: 002
Revises: 001
Create Date: 2026-01-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create feedback table
    op.create_table(
        "feedback",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("topic_slug", sa.String(255), nullable=False),
        sa.Column("feedback_type", sa.String(50), nullable=False),
        sa.Column("reason", sa.String(100), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("session_id", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        comment="User feedback on topic summaries",
    )
    # Create indexes
    op.create_index("ix_feedback_topic_slug", "feedback", ["topic_slug"], unique=False)
    op.create_index("ix_feedback_session_id", "feedback", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_feedback_session_id", table_name="feedback")
    op.drop_index("ix_feedback_topic_slug", table_name="feedback")
    op.drop_table("feedback")
