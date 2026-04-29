"""Add cart module tables

Revision ID: 7e2b1c9a4d21
Revises: 6c1f5d4a9b22
Create Date: 2026-04-29 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7e2b1c9a4d21"
down_revision: Union[str, None] = "6c1f5d4a9b22"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


cart_status_enum = sa.Enum("ACTIVE", "ORDERED", "ABANDONED", name="cartstatus", native_enum=False, length=20)
cart_item_type_enum = sa.Enum("PRODUCT", "COMBO_PRODUCT", name="cartitemtype", native_enum=False, length=20)


def upgrade() -> None:
    cart_status_enum.create(op.get_bind(), checkfirst=True)
    cart_item_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "carts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("restaurant_id", sa.String(length=36), nullable=False),
        sa.Column("customer_id", sa.String(length=36), nullable=False),
        sa.Column("status", cart_status_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_carts_created_at"), "carts", ["created_at"], unique=False)
    op.create_index(op.f("ix_carts_customer_id"), "carts", ["customer_id"], unique=False)
    op.create_index(op.f("ix_carts_is_active"), "carts", ["is_active"], unique=False)
    op.create_index(op.f("ix_carts_restaurant_id"), "carts", ["restaurant_id"], unique=False)
    op.create_index(op.f("ix_carts_status"), "carts", ["status"], unique=False)

    op.create_table(
        "cart_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("cart_id", sa.String(length=36), nullable=False),
        sa.Column("restaurant_id", sa.String(length=36), nullable=False),
        sa.Column("item_type", cart_item_type_enum, nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=True),
        sa.Column("combo_product_id", sa.String(length=36), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Integer(), nullable=False),
        sa.Column("modifiers_price", sa.Integer(), nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("modifier_signature", sa.String(length=1000), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cart_id"], ["carts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["combo_product_id"], ["combo_products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cart_items_cart_id"), "cart_items", ["cart_id"], unique=False)
    op.create_index(op.f("ix_cart_items_combo_product_id"), "cart_items", ["combo_product_id"], unique=False)
    op.create_index(op.f("ix_cart_items_created_at"), "cart_items", ["created_at"], unique=False)
    op.create_index(op.f("ix_cart_items_item_type"), "cart_items", ["item_type"], unique=False)
    op.create_index(op.f("ix_cart_items_modifier_signature"), "cart_items", ["modifier_signature"], unique=False)
    op.create_index(op.f("ix_cart_items_product_id"), "cart_items", ["product_id"], unique=False)
    op.create_index(op.f("ix_cart_items_restaurant_id"), "cart_items", ["restaurant_id"], unique=False)

    op.create_table(
        "cart_item_modifier_options",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("cart_item_id", sa.String(length=36), nullable=False),
        sa.Column("modifier_option_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cart_item_id"], ["cart_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["modifier_option_id"], ["modifier_options.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cart_item_modifier_options_cart_item_id"), "cart_item_modifier_options", ["cart_item_id"], unique=False)
    op.create_index(op.f("ix_cart_item_modifier_options_modifier_option_id"), "cart_item_modifier_options", ["modifier_option_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_cart_item_modifier_options_modifier_option_id"), table_name="cart_item_modifier_options")
    op.drop_index(op.f("ix_cart_item_modifier_options_cart_item_id"), table_name="cart_item_modifier_options")
    op.drop_table("cart_item_modifier_options")

    op.drop_index(op.f("ix_cart_items_restaurant_id"), table_name="cart_items")
    op.drop_index(op.f("ix_cart_items_product_id"), table_name="cart_items")
    op.drop_index(op.f("ix_cart_items_modifier_signature"), table_name="cart_items")
    op.drop_index(op.f("ix_cart_items_item_type"), table_name="cart_items")
    op.drop_index(op.f("ix_cart_items_created_at"), table_name="cart_items")
    op.drop_index(op.f("ix_cart_items_combo_product_id"), table_name="cart_items")
    op.drop_index(op.f("ix_cart_items_cart_id"), table_name="cart_items")
    op.drop_table("cart_items")

    op.drop_index(op.f("ix_carts_status"), table_name="carts")
    op.drop_index(op.f("ix_carts_restaurant_id"), table_name="carts")
    op.drop_index(op.f("ix_carts_is_active"), table_name="carts")
    op.drop_index(op.f("ix_carts_customer_id"), table_name="carts")
    op.drop_index(op.f("ix_carts_created_at"), table_name="carts")
    op.drop_table("carts")

    cart_item_type_enum.drop(op.get_bind(), checkfirst=True)
    cart_status_enum.drop(op.get_bind(), checkfirst=True)

