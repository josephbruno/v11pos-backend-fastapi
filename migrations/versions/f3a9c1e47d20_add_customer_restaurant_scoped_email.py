"""add customer restaurant_id and scope email per restaurant

Revision ID: f3a9c1e47d20
Revises: 8b0c2c7f93a1
Create Date: 2026-05-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "f3a9c1e47d20"
down_revision: Union[str, None] = "8b0c2c7f93a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "customers",
        sa.Column("restaurant_id", sa.String(length=36), nullable=True),
    )
    op.create_foreign_key(
        "fk_customers_restaurant_id",
        "customers",
        "restaurants",
        ["restaurant_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(op.f("ix_customers_restaurant_id"), "customers", ["restaurant_id"], unique=False)

    bind = op.get_bind()
    n_restaurants = bind.execute(sa.text("SELECT COUNT(*) FROM restaurants")).scalar_one()

    if int(n_restaurants) == 1:
        bind.execute(
            sa.text(
                """
                UPDATE customers
                SET restaurant_id = (SELECT id FROM restaurants ORDER BY created_at ASC LIMIT 1)
                WHERE restaurant_id IS NULL
                """
            )
        )

    op.add_column(
        "customer_email_otps",
        sa.Column("restaurant_id", sa.String(length=36), nullable=True),
    )
    op.create_foreign_key(
        "fk_customer_email_otps_restaurant_id",
        "customer_email_otps",
        "restaurants",
        ["restaurant_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        op.f("ix_customer_email_otps_restaurant_id"),
        "customer_email_otps",
        ["restaurant_id"],
        unique=False,
    )

    bind.execute(
        sa.text(
            """
            UPDATE customer_email_otps o
            INNER JOIN customers c ON o.customer_id = c.id
            SET o.restaurant_id = c.restaurant_id
            WHERE o.restaurant_id IS NULL AND c.restaurant_id IS NOT NULL
            """
        )
    )

    bind.execute(sa.text("DELETE FROM customer_email_otps WHERE restaurant_id IS NULL"))

    n_otp_null = bind.execute(
        sa.text("SELECT COUNT(*) FROM customer_email_otps WHERE restaurant_id IS NULL")
    ).scalar_one()
    if int(n_otp_null) == 0:
        op.alter_column(
            "customer_email_otps",
            "restaurant_id",
            existing_type=sa.String(length=36),
            nullable=False,
        )

    n_cust_null = bind.execute(
        sa.text("SELECT COUNT(*) FROM customers WHERE restaurant_id IS NULL")
    ).scalar_one()
    if int(n_cust_null) == 0:
        op.alter_column(
            "customers",
            "restaurant_id",
            existing_type=sa.String(length=36),
            nullable=False,
        )
        op.create_unique_constraint(
            "uq_customers_restaurant_email",
            "customers",
            ["restaurant_id", "email"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    uqs = {c["name"] for c in insp.get_unique_constraints("customers")}
    if "uq_customers_restaurant_email" in uqs:
        op.drop_constraint("uq_customers_restaurant_email", "customers", type_="unique")

    op.drop_constraint("fk_customer_email_otps_restaurant_id", "customer_email_otps", type_="foreignkey")
    op.drop_index(op.f("ix_customer_email_otps_restaurant_id"), table_name="customer_email_otps")
    op.drop_column("customer_email_otps", "restaurant_id")

    op.drop_constraint("fk_customers_restaurant_id", "customers", type_="foreignkey")
    op.drop_index(op.f("ix_customers_restaurant_id"), table_name="customers")
    op.drop_column("customers", "restaurant_id")
