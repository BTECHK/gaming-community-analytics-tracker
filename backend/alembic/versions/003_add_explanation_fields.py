"""Add explanation fields to aggregations table

Revision ID: 003
Revises: 002
Create Date: 2026-01-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add sentiment_explanation JSONB column
    op.add_column(
        "aggregations",
        sa.Column("sentiment_explanation", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    # Add confidence_breakdown JSONB column
    op.add_column(
        "aggregations",
        sa.Column("confidence_breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("aggregations", "confidence_breakdown")
    op.drop_column("aggregations", "sentiment_explanation")
