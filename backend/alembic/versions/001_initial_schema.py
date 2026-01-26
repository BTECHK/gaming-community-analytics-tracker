"""Initial schema: posts, sentiment_results, aggregations

Revision ID: 001
Revises:
Create Date: 2026-01-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create platform enum type (before tables that use it)
    op.execute("CREATE TYPE platform_enum AS ENUM ('reddit', 'youtube', 'official-news', 'tier-site', 'google_trends', 'guide-site')")

    # Create sentiment_label enum type (before tables that use it)
    op.execute("CREATE TYPE sentiment_label_enum AS ENUM ('positive', 'neutral', 'negative')")

    # Create posts table
    op.create_table(
        "posts",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column(
            "platform",
            postgresql.ENUM(
                "reddit", "youtube", "official-news", "tier-site", "google_trends", "guide-site",
                name="platform_enum",
                create_type=False,  # Type already created above
            ),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("author", sa.String(255), nullable=True),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("upvotes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comments_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        comment="Raw ingested posts from various platforms",
    )
    # Create indexes for posts table
    op.create_index("ix_posts_platform", "posts", ["platform"], unique=False)
    op.create_index("ix_posts_external_id", "posts", ["external_id"], unique=False)
    op.create_index(
        "ix_posts_platform_external_id",
        "posts",
        ["platform", "external_id"],
        unique=True,
    )

    # Create sentiment_results table
    op.create_table(
        "sentiment_results",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("post_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column(
            "label",
            postgresql.ENUM(
                "positive", "neutral", "negative",
                name="sentiment_label_enum",
                create_type=False,  # Type already created above
            ),
            nullable=False,
        ),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("scores", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("topics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_toxic", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("toxicity_score", sa.Float(), nullable=True),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["post_id"],
            ["posts.id"],
            name="fk_sentiment_results_post_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        comment="NLP analysis results for posts",
    )
    # Create index for sentiment_results
    op.create_index("ix_sentiment_results_post_id", "sentiment_results", ["post_id"], unique=False)

    # Create aggregations table
    op.create_table(
        "aggregations",
        sa.Column("id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("topic_name", sa.String(255), nullable=False),
        sa.Column("topic_slug", sa.String(255), nullable=False),
        sa.Column("sentiment_positive", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("sentiment_neutral", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("sentiment_negative", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("representative_quotes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("post_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_mix", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("patch_version", sa.String(20), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("topic_slug", name="uq_aggregations_topic_slug"),
        comment="Aggregated topic summaries with sentiment breakdowns",
    )
    # Create index for aggregations
    op.create_index("ix_aggregations_topic_name", "aggregations", ["topic_name"], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_index("ix_aggregations_topic_name", table_name="aggregations")
    op.drop_table("aggregations")

    op.drop_index("ix_sentiment_results_post_id", table_name="sentiment_results")
    op.drop_table("sentiment_results")

    op.drop_index("ix_posts_platform_external_id", table_name="posts")
    op.drop_index("ix_posts_external_id", table_name="posts")
    op.drop_index("ix_posts_platform", table_name="posts")
    op.drop_table("posts")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS sentiment_label_enum")
    op.execute("DROP TYPE IF EXISTS platform_enum")
