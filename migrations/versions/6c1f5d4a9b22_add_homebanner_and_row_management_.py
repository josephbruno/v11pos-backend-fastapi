"""Add homebanner and row management modules

Revision ID: 6c1f5d4a9b22
Revises: cb0f4438b485
Create Date: 2026-04-13 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6c1f5d4a9b22"
down_revision: Union[str, None] = "cb0f4438b485"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


row_type_enum = sa.Enum(
    "CATEGORY",
    "PRODUCT",
    "COMBO_PRODUCT",
    "SINGLE_BANNER",
    "ADS_BANNER",
    "ADS_VIDEO",
    name="rowtype",
)


def upgrade() -> None:
    row_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "home_banners",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("restaurant_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("subtitle", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("mobile_image", sa.String(length=500), nullable=True),
        sa.Column("desktop_image", sa.String(length=500), nullable=True),
        sa.Column("redirect_url", sa.String(length=500), nullable=True),
        sa.Column("button_text", sa.String(length=100), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("featured", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("start_at", sa.DateTime(), nullable=True),
        sa.Column("end_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_home_banners_active"), "home_banners", ["active"], unique=False)
    op.create_index(op.f("ix_home_banners_restaurant_id"), "home_banners", ["restaurant_id"], unique=False)
    op.create_index(op.f("ix_home_banners_sort_order"), "home_banners", ["sort_order"], unique=False)
    op.create_index(op.f("ix_home_banners_title"), "home_banners", ["title"], unique=False)

    op.create_table(
        "row_managements",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("restaurant_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column("subtitle", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("row_type", row_type_enum, nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("show_title", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("layout_style", sa.String(length=30), nullable=True),
        sa.Column("items_per_view", sa.Integer(), nullable=True),
        sa.Column("auto_scroll", sa.Boolean(), nullable=False),
        sa.Column("category_ids", sa.JSON(), nullable=True),
        sa.Column("product_ids", sa.JSON(), nullable=True),
        sa.Column("combo_product_ids", sa.JSON(), nullable=True),
        sa.Column("image", sa.String(length=500), nullable=True),
        sa.Column("mobile_image", sa.String(length=500), nullable=True),
        sa.Column("desktop_image", sa.String(length=500), nullable=True),
        sa.Column("video_url", sa.String(length=500), nullable=True),
        sa.Column("thumbnail_image", sa.String(length=500), nullable=True),
        sa.Column("redirect_url", sa.String(length=500), nullable=True),
        sa.Column("button_text", sa.String(length=100), nullable=True),
        sa.Column("background_color", sa.String(length=7), nullable=True),
        sa.Column("text_color", sa.String(length=7), nullable=True),
        sa.Column("start_at", sa.DateTime(), nullable=True),
        sa.Column("end_at", sa.DateTime(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_row_managements_active"), "row_managements", ["active"], unique=False)
    op.create_index(op.f("ix_row_managements_name"), "row_managements", ["name"], unique=False)
    op.create_index(op.f("ix_row_managements_restaurant_id"), "row_managements", ["restaurant_id"], unique=False)
    op.create_index(op.f("ix_row_managements_row_type"), "row_managements", ["row_type"], unique=False)
    op.create_index(op.f("ix_row_managements_sort_order"), "row_managements", ["sort_order"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_row_managements_sort_order"), table_name="row_managements")
    op.drop_index(op.f("ix_row_managements_row_type"), table_name="row_managements")
    op.drop_index(op.f("ix_row_managements_restaurant_id"), table_name="row_managements")
    op.drop_index(op.f("ix_row_managements_name"), table_name="row_managements")
    op.drop_index(op.f("ix_row_managements_active"), table_name="row_managements")
    op.drop_table("row_managements")

    op.drop_index(op.f("ix_home_banners_title"), table_name="home_banners")
    op.drop_index(op.f("ix_home_banners_sort_order"), table_name="home_banners")
    op.drop_index(op.f("ix_home_banners_restaurant_id"), table_name="home_banners")
    op.drop_index(op.f("ix_home_banners_active"), table_name="home_banners")
    op.drop_table("home_banners")

    row_type_enum.drop(op.get_bind(), checkfirst=True)
