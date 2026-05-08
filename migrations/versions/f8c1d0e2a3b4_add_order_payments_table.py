"""Add order_payments table

Revision ID: f8c1d0e2a3b4
Revises: e8d0a1f92c33
Create Date: 2026-05-04 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f8c1d0e2a3b4"
down_revision: Union[str, None] = "e8d0a1f92c33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "order_payments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("restaurant_id", sa.String(length=36), nullable=False),
        sa.Column("order_id", sa.String(length=36), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column(
            "payment_status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("payment_method", sa.String(length=20), nullable=True),
        sa.Column("gateway", sa.String(length=50), nullable=True),
        sa.Column("gateway_transaction_id", sa.String(length=100), nullable=True),
        sa.Column("payment_reference", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_order_payments_order_id"), "order_payments", ["order_id"], unique=False)
    op.create_index(op.f("ix_order_payments_restaurant_id"), "order_payments", ["restaurant_id"], unique=False)
    op.create_index(
        op.f("ix_order_payments_payment_status"), "order_payments", ["payment_status"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_order_payments_payment_status"), table_name="order_payments")
    op.drop_index(op.f("ix_order_payments_restaurant_id"), table_name="order_payments")
    op.drop_index(op.f("ix_order_payments_order_id"), table_name="order_payments")
    op.drop_table("order_payments")
