"""Add payment_gateways table

Revision ID: 9d4e2b7a6c10
Revises: f8c1d0e2a3b4
Create Date: 2026-05-29 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9d4e2b7a6c10"
down_revision: Union[str, None] = "f8c1d0e2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "payment_gateways",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("restaurant_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=True),
        sa.Column("environment", sa.String(length=20), nullable=False, server_default="sandbox"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="inactive"),
        sa.Column("api_key", sa.String(length=500), nullable=True),
        sa.Column("client_id", sa.String(length=255), nullable=True),
        sa.Column("secret_key", sa.String(length=500), nullable=True),
        sa.Column("merchant_id", sa.String(length=255), nullable=True),
        sa.Column("salt_key", sa.String(length=500), nullable=True),
        sa.Column("salt_index", sa.String(length=50), nullable=True),
        sa.Column("webhook_secret", sa.String(length=500), nullable=True),
        sa.Column("upi_id", sa.String(length=100), nullable=True),
        sa.Column("base_url", sa.String(length=500), nullable=True),
        sa.Column("webhook_url", sa.String(length=500), nullable=True),
        sa.Column("callback_url", sa.String(length=500), nullable=True),
        sa.Column("extra_config", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("updated_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("restaurant_id", "provider", name="uq_payment_gateways_restaurant_provider"),
    )
    op.create_index(op.f("ix_payment_gateways_environment"), "payment_gateways", ["environment"], unique=False)
    op.create_index(op.f("ix_payment_gateways_is_active"), "payment_gateways", ["is_active"], unique=False)
    op.create_index(op.f("ix_payment_gateways_is_default"), "payment_gateways", ["is_default"], unique=False)
    op.create_index(op.f("ix_payment_gateways_provider"), "payment_gateways", ["provider"], unique=False)
    op.create_index(op.f("ix_payment_gateways_restaurant_id"), "payment_gateways", ["restaurant_id"], unique=False)
    op.create_index(op.f("ix_payment_gateways_status"), "payment_gateways", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_payment_gateways_status"), table_name="payment_gateways")
    op.drop_index(op.f("ix_payment_gateways_restaurant_id"), table_name="payment_gateways")
    op.drop_index(op.f("ix_payment_gateways_provider"), table_name="payment_gateways")
    op.drop_index(op.f("ix_payment_gateways_is_default"), table_name="payment_gateways")
    op.drop_index(op.f("ix_payment_gateways_is_active"), table_name="payment_gateways")
    op.drop_index(op.f("ix_payment_gateways_environment"), table_name="payment_gateways")
    op.drop_table("payment_gateways")
