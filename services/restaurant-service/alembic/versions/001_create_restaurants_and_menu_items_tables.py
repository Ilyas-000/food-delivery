"""create restaurants and menu_items tables

Revision ID: 001_initial
Revises:
Create Date: 2026-02-01 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create cuisine_enum type
    cuisine_enum = postgresql.ENUM(
        "ITALIAN",
        "CHINESE",
        "JAPANESE",
        "MEXICAN",
        "INDIAN",
        "FRENCH",
        "THAI",
        "AMERICAN",
        "KOREAN",
        "VIETNAMESE",
        "MEDITERRANEAN",
        "MIDDLE_EASTERN",
        "GREEK",
        "SPANISH",
        "TURKISH",
        "RUSSIAN",
        "BRAZILIAN",
        "FUSION",
        "VEGETARIAN",
        "VEGAN",
        "SEAFOOD",
        "STEAKHOUSE",
        "FAST_FOOD",
        "CAFE",
        "BAKERY",
        "DESSERTS",
        "OTHER",
        name="cuisine_enum",
        create_type=False,
    )
    cuisine_enum.create(op.get_bind(), checkfirst=True)

    # Create menu_category_enum type
    category_enum = postgresql.ENUM(
        "APPETIZER",
        "SALAD",
        "SOUP",
        "MAIN_COURSE",
        "SIDE_DISH",
        "DESSERT",
        "BEVERAGE",
        "ALCOHOL",
        "BREAKFAST",
        "LUNCH",
        "DINNER",
        "SNACK",
        "SPECIAL",
        name="menu_category_enum",
        create_type=False,
    )
    category_enum.create(op.get_bind(), checkfirst=True)

    # Create menu_availability_enum type
    availability_enum = postgresql.ENUM(
        "AVAILABLE",
        "OUT_OF_STOCK",
        "DISCONTINUED",
        name="menu_availability_enum",
        create_type=False,
    )
    availability_enum.create(op.get_bind(), checkfirst=True)

    # Create restaurants table
    op.create_table(
        "restaurants",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Restaurant unique identifier",
        ),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Restaurant owner ID (user service)",
        ),
        sa.Column("name", sa.String(length=100), nullable=False, comment="Restaurant name"),
        sa.Column("description", sa.Text(), nullable=False, comment="Restaurant description"),
        sa.Column("street", sa.String(length=200), nullable=False, comment="Street address"),
        sa.Column("city", sa.String(length=100), nullable=False, comment="City"),
        sa.Column("postal_code", sa.String(length=20), nullable=False, comment="Postal code"),
        sa.Column(
            "latitude",
            sa.Numeric(precision=10, scale=7),
            nullable=True,
            comment="GPS latitude (-90 to 90)",
        ),
        sa.Column(
            "longitude",
            sa.Numeric(precision=10, scale=7),
            nullable=True,
            comment="GPS longitude (-180 to 180)",
        ),
        sa.Column("cuisine", cuisine_enum, nullable=False, comment="Cuisine type"),
        sa.Column(
            "rating",
            sa.Numeric(precision=3, scale=2),
            nullable=False,
            comment="Average rating (0.0 to 5.0)",
        ),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, comment="Is restaurant active (soft delete)"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Creation timestamp (UTC)",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Last update timestamp (UTC)",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_restaurants_owner_id"), "restaurants", ["owner_id"], unique=False)
    op.create_index(op.f("ix_restaurants_cuisine"), "restaurants", ["cuisine"], unique=False)
    op.create_index(op.f("ix_restaurants_city"), "restaurants", ["city"], unique=False)
    op.create_index(op.f("ix_restaurants_rating"), "restaurants", ["rating"], unique=False)
    op.create_index(op.f("ix_restaurants_created_at"), "restaurants", ["created_at"], unique=False)

    # Create menu_items table
    op.create_table(
        "menu_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Menu item unique identifier",
        ),
        sa.Column(
            "restaurant_id", postgresql.UUID(as_uuid=True), nullable=False, comment="Restaurant ID"
        ),
        sa.Column("name", sa.String(length=200), nullable=False, comment="Menu item name"),
        sa.Column("description", sa.Text(), nullable=False, comment="Menu item description"),
        sa.Column(
            "price_amount",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
            comment="Price amount",
        ),
        sa.Column(
            "price_currency",
            sa.String(length=3),
            nullable=False,
            comment="Currency code (ISO 4217)",
        ),
        sa.Column("category", category_enum, nullable=False, comment="Menu item category"),
        sa.Column(
            "image_url", sa.String(length=500), nullable=True, comment="Image URL (optional)"
        ),
        sa.Column(
            "availability", availability_enum, nullable=False, comment="Item availability status"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Creation timestamp (UTC)",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Last update timestamp (UTC)",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_menu_items_restaurant_id"), "menu_items", ["restaurant_id"], unique=False
    )
    op.create_index(op.f("ix_menu_items_category"), "menu_items", ["category"], unique=False)
    op.create_index(
        op.f("ix_menu_items_availability"), "menu_items", ["availability"], unique=False
    )
    op.create_index(op.f("ix_menu_items_created_at"), "menu_items", ["created_at"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop menu_items table
    op.drop_index(op.f("ix_menu_items_created_at"), table_name="menu_items")
    op.drop_index(op.f("ix_menu_items_availability"), table_name="menu_items")
    op.drop_index(op.f("ix_menu_items_category"), table_name="menu_items")
    op.drop_index(op.f("ix_menu_items_restaurant_id"), table_name="menu_items")
    op.drop_table("menu_items")

    # Drop restaurants table
    op.drop_index(op.f("ix_restaurants_created_at"), table_name="restaurants")
    op.drop_index(op.f("ix_restaurants_rating"), table_name="restaurants")
    op.drop_index(op.f("ix_restaurants_city"), table_name="restaurants")
    op.drop_index(op.f("ix_restaurants_cuisine"), table_name="restaurants")
    op.drop_index(op.f("ix_restaurants_owner_id"), table_name="restaurants")
    op.drop_table("restaurants")

    # Drop enum types
    sa.Enum(name="menu_availability_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="menu_category_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="cuisine_enum").drop(op.get_bind(), checkfirst=True)
