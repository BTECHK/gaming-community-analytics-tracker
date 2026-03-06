"""Add news-source-a, news-source-b, reddit to platform_enum

Revision ID: 004
Revises: 003
Create Date: 2026-03-06

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE platform_enum ADD VALUE IF NOT EXISTS 'news-source-a'")
    op.execute("ALTER TYPE platform_enum ADD VALUE IF NOT EXISTS 'news-source-b'")
    op.execute("ALTER TYPE platform_enum ADD VALUE IF NOT EXISTS 'reddit'")


def downgrade() -> None:
    # PostgreSQL does not support removing values from enums directly.
    # To downgrade, you would need to recreate the type and migrate data.
    # This is intentionally left as a no-op since removing platforms
    # would require migrating or deleting existing data.
    pass
