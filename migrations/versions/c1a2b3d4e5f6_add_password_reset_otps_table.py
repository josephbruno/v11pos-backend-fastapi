"""add password_reset_otps table

Revision ID: c1a2b3d4e5f6
Revises: 9d4e2b7a6c10
Create Date: 2026-06-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c1a2b3d4e5f6"
down_revision: Union[str, None] = "9d4e2b7a6c10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "password_reset_otps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("otp_hash", sa.String(255), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_password_reset_otps_id"), "password_reset_otps", ["id"], unique=False)
    op.create_index(op.f("ix_password_reset_otps_email"), "password_reset_otps", ["email"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_password_reset_otps_email"), table_name="password_reset_otps")
    op.drop_index(op.f("ix_password_reset_otps_id"), table_name="password_reset_otps")
    op.drop_table("password_reset_otps")
