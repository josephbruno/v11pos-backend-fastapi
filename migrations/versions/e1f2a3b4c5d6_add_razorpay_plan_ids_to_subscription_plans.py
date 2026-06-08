"""add razorpay plan ids to subscription_plans

Revision ID: e1f2a3b4c5d6
Revises: d2e3f4a5b6c7
Create Date: 2026-06-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, None] = "d2e3f4a5b6c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "subscription_plans",
        sa.Column("razorpay_plan_id_monthly", sa.String(255), nullable=True),
    )
    op.add_column(
        "subscription_plans",
        sa.Column("razorpay_plan_id_yearly", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("subscription_plans", "razorpay_plan_id_yearly")
    op.drop_column("subscription_plans", "razorpay_plan_id_monthly")
