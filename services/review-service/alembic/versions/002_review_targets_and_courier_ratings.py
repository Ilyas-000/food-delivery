"""Convert review schema to generic target model."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_review_targets_courier"
down_revision: str | None = "001_create_reviews_table"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade restaurant-only reviews to target-based reviews."""
    op.add_column(
        "reviews",
        sa.Column("target_type", sa.String(length=32), nullable=True, server_default="restaurant"),
    )
    op.add_column(
        "reviews",
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.execute("UPDATE reviews SET target_type = 'restaurant', target_id = restaurant_id")

    op.alter_column("reviews", "target_type", nullable=False, server_default=None)
    op.alter_column("reviews", "target_id", nullable=False)

    op.drop_constraint("uq_reviews_order_author", "reviews", type_="unique")
    op.create_unique_constraint(
        "uq_reviews_order_author_target_type",
        "reviews",
        ["order_id", "author_user_id", "target_type"],
    )

    op.create_index(op.f("ix_reviews_target_id"), "reviews", ["target_id"], unique=False)
    op.create_index(op.f("ix_reviews_target_type"), "reviews", ["target_type"], unique=False)
    op.drop_index(op.f("ix_reviews_restaurant_id"), table_name="reviews")
    op.drop_column("reviews", "restaurant_id")


def downgrade() -> None:
    """Restore restaurant-only review schema."""
    op.add_column(
        "reviews",
        sa.Column("restaurant_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.execute("UPDATE reviews SET restaurant_id = target_id WHERE target_type = 'restaurant'")

    op.alter_column("reviews", "restaurant_id", nullable=False)
    op.create_index(op.f("ix_reviews_restaurant_id"), "reviews", ["restaurant_id"], unique=False)

    op.drop_constraint("uq_reviews_order_author_target_type", "reviews", type_="unique")
    op.create_unique_constraint(
        "uq_reviews_order_author",
        "reviews",
        ["order_id", "author_user_id"],
    )

    op.drop_index(op.f("ix_reviews_target_type"), table_name="reviews")
    op.drop_index(op.f("ix_reviews_target_id"), table_name="reviews")
    op.drop_column("reviews", "target_id")
    op.drop_column("reviews", "target_type")
