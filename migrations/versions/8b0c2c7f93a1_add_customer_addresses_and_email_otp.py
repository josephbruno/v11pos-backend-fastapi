"""Add customer addresses and email OTP tables

Revision ID: 8b0c2c7f93a1
Revises: 7e2b1c9a4d21
Create Date: 2026-04-29 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8b0c2c7f93a1"
down_revision: Union[str, None] = "7e2b1c9a4d21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customer_addresses",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("customer_id", sa.String(length=36), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=True),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("state", sa.String(length=100), nullable=True),
        sa.Column("postal_code", sa.String(length=20), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("latitude", sa.Numeric(precision=10, scale=8), nullable=True),
        sa.Column("longitude", sa.Numeric(precision=11, scale=8), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_customer_addresses_customer_id"), "customer_addresses", ["customer_id"], unique=False)
    op.create_index(op.f("ix_customer_addresses_is_active"), "customer_addresses", ["is_active"], unique=False)
    op.create_index(op.f("ix_customer_addresses_is_default"), "customer_addresses", ["is_default"], unique=False)

    op.create_table(
        "customer_email_otps",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("customer_id", sa.String(length=36), nullable=False),
        sa.Column("otp_hash", sa.String(length=255), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_customer_email_otps_customer_id"), "customer_email_otps", ["customer_id"], unique=False)
    op.create_index(op.f("ix_customer_email_otps_email"), "customer_email_otps", ["email"], unique=False)
    op.create_index(op.f("ix_customer_email_otps_expires_at"), "customer_email_otps", ["expires_at"], unique=False)
    op.create_index(op.f("ix_customer_email_otps_consumed_at"), "customer_email_otps", ["consumed_at"], unique=False)
    op.create_index(op.f("ix_customer_email_otps_created_at"), "customer_email_otps", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_customer_email_otps_created_at"), table_name="customer_email_otps")
    op.drop_index(op.f("ix_customer_email_otps_consumed_at"), table_name="customer_email_otps")
    op.drop_index(op.f("ix_customer_email_otps_expires_at"), table_name="customer_email_otps")
    op.drop_index(op.f("ix_customer_email_otps_email"), table_name="customer_email_otps")
    op.drop_index(op.f("ix_customer_email_otps_customer_id"), table_name="customer_email_otps")
    op.drop_table("customer_email_otps")

    op.drop_index(op.f("ix_customer_addresses_is_default"), table_name="customer_addresses")
    op.drop_index(op.f("ix_customer_addresses_is_active"), table_name="customer_addresses")
    op.drop_index(op.f("ix_customer_addresses_customer_id"), table_name="customer_addresses")
    op.drop_table("customer_addresses")

