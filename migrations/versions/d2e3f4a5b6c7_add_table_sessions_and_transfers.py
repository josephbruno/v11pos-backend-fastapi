"""add table_sessions and table_transfers tables

Revision ID: d2e3f4a5b6c7
Revises: c1a2b3d4e5f6
Create Date: 2026-06-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d2e3f4a5b6c7"
down_revision: Union[str, None] = "c1a2b3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "table_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("restaurant_id", sa.String(length=36), nullable=False),
        sa.Column("table_id", sa.String(length=36), nullable=False),
        sa.Column("customer_id", sa.String(length=36), nullable=False),
        sa.Column("active_order_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["active_order_id"], ["orders.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["table_id"], ["tables.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_table_sessions_customer_id"), "table_sessions", ["customer_id"], unique=False)
    op.create_index(op.f("ix_table_sessions_restaurant_id"), "table_sessions", ["restaurant_id"], unique=False)
    op.create_index(op.f("ix_table_sessions_table_id"), "table_sessions", ["table_id"], unique=False)
    op.create_index(op.f("ix_table_sessions_active_order_id"), "table_sessions", ["active_order_id"], unique=False)
    op.create_index(op.f("ix_table_sessions_status"), "table_sessions", ["status"], unique=False)

    op.create_table(
        "table_transfers",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("restaurant_id", sa.String(length=36), nullable=False),
        sa.Column("customer_id", sa.String(length=36), nullable=False),
        sa.Column("old_table_id", sa.String(length=36), nullable=False),
        sa.Column("new_table_id", sa.String(length=36), nullable=False),
        sa.Column("order_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("resolved_by", sa.String(length=36), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("audit_log", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["new_table_id"], ["tables.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["old_table_id"], ["tables.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["resolved_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_table_transfers_customer_id"), "table_transfers", ["customer_id"], unique=False)
    op.create_index(op.f("ix_table_transfers_restaurant_id"), "table_transfers", ["restaurant_id"], unique=False)
    op.create_index(op.f("ix_table_transfers_old_table_id"), "table_transfers", ["old_table_id"], unique=False)
    op.create_index(op.f("ix_table_transfers_new_table_id"), "table_transfers", ["new_table_id"], unique=False)
    op.create_index(op.f("ix_table_transfers_status"), "table_transfers", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_table_transfers_status"), table_name="table_transfers")
    op.drop_index(op.f("ix_table_transfers_new_table_id"), table_name="table_transfers")
    op.drop_index(op.f("ix_table_transfers_old_table_id"), table_name="table_transfers")
    op.drop_index(op.f("ix_table_transfers_restaurant_id"), table_name="table_transfers")
    op.drop_index(op.f("ix_table_transfers_customer_id"), table_name="table_transfers")
    op.drop_table("table_transfers")
    op.drop_index(op.f("ix_table_sessions_status"), table_name="table_sessions")
    op.drop_index(op.f("ix_table_sessions_active_order_id"), table_name="table_sessions")
    op.drop_index(op.f("ix_table_sessions_table_id"), table_name="table_sessions")
    op.drop_index(op.f("ix_table_sessions_restaurant_id"), table_name="table_sessions")
    op.drop_index(op.f("ix_table_sessions_customer_id"), table_name="table_sessions")
    op.drop_table("table_sessions")
