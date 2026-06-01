"""Create delivery_assignments table."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_delivery_assignments"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Apply schema changes."""
    op.create_table(
        "delivery_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("restaurant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("courier_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("current_latitude", sa.Float(), nullable=True),
        sa.Column("current_longitude", sa.Float(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_delivery_assignments_order_id"),
        "delivery_assignments",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_delivery_assignments_restaurant_id"),
        "delivery_assignments",
        ["restaurant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_delivery_assignments_courier_id"),
        "delivery_assignments",
        ["courier_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_delivery_assignments_status"),
        "delivery_assignments",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_delivery_assignments_created_at"),
        "delivery_assignments",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Rollback schema changes."""
    op.drop_index(op.f("ix_delivery_assignments_created_at"), table_name="delivery_assignments")
    op.drop_index(op.f("ix_delivery_assignments_status"), table_name="delivery_assignments")
    op.drop_index(op.f("ix_delivery_assignments_courier_id"), table_name="delivery_assignments")
    op.drop_index(op.f("ix_delivery_assignments_restaurant_id"), table_name="delivery_assignments")
    op.drop_index(op.f("ix_delivery_assignments_order_id"), table_name="delivery_assignments")
    op.drop_table("delivery_assignments")
