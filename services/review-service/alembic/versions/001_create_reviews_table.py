"""Create reviews table."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_create_reviews_table"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Apply schema changes."""
    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("restaurant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id", "author_user_id", name="uq_reviews_order_author"),
    )
    op.create_index(op.f("ix_reviews_author_user_id"), "reviews", ["author_user_id"], unique=False)
    op.create_index(op.f("ix_reviews_created_at"), "reviews", ["created_at"], unique=False)
    op.create_index(op.f("ix_reviews_order_id"), "reviews", ["order_id"], unique=False)
    op.create_index(op.f("ix_reviews_rating"), "reviews", ["rating"], unique=False)
    op.create_index(op.f("ix_reviews_restaurant_id"), "reviews", ["restaurant_id"], unique=False)


def downgrade() -> None:
    """Rollback schema changes."""
    op.drop_index(op.f("ix_reviews_restaurant_id"), table_name="reviews")
    op.drop_index(op.f("ix_reviews_rating"), table_name="reviews")
    op.drop_index(op.f("ix_reviews_order_id"), table_name="reviews")
    op.drop_index(op.f("ix_reviews_created_at"), table_name="reviews")
    op.drop_index(op.f("ix_reviews_author_user_id"), table_name="reviews")
    op.drop_table("reviews")
