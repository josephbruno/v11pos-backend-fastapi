"""Seed default subscription plans on startup."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.modules.restaurant.model import SubscriptionPlan
from app.modules.user.model import User  # noqa: F401
from app.modules.staff.model import Role  # noqa: F401


DEFAULT_PLANS = [
    {
        "name": "trial",
        "display_name": "Free Trial",
        "description": "14-day trial with basic features",
        "tagline": "Try before you buy",
        "price_monthly": 0,
        "price_yearly": 0,
        "max_users": 2,
        "max_products": 50,
        "max_orders_per_month": 100,
        "max_locations": 1,
        "max_storage_gb": 1,
        "features": ["pos", "basic_reports"],
        "trial_days": 14,
        "sort_order": 0,
        "is_public": True,
    },
    {
        "name": "basic",
        "display_name": "Basic",
        "description": "Essential POS for small restaurants",
        "tagline": "Get started",
        "price_monthly": 99900,
        "price_yearly": 999900,
        "max_users": 5,
        "max_products": 200,
        "max_orders_per_month": 2000,
        "max_locations": 1,
        "max_storage_gb": 5,
        "features": ["pos", "qr_ordering", "basic_reports"],
        "trial_days": 0,
        "sort_order": 1,
        "is_featured": False,
        "is_public": True,
    },
    {
        "name": "pro",
        "display_name": "Pro",
        "description": "Advanced features for growing restaurants",
        "tagline": "Most popular",
        "price_monthly": 249900,
        "price_yearly": 2499900,
        "max_users": 15,
        "max_products": 1000,
        "max_orders_per_month": 10000,
        "max_locations": 3,
        "max_storage_gb": 20,
        "features": ["pos", "qr_ordering", "analytics", "loyalty", "kds"],
        "trial_days": 0,
        "sort_order": 2,
        "is_featured": True,
        "badge": "Popular",
        "is_public": True,
    },
    {
        "name": "enterprise",
        "display_name": "Enterprise",
        "description": "Unlimited scale for multi-location brands",
        "tagline": "Scale without limits",
        "price_monthly": 499900,
        "price_yearly": 4999900,
        "max_users": 100,
        "max_products": 10000,
        "max_orders_per_month": 100000,
        "max_locations": 20,
        "max_storage_gb": 100,
        "features": ["pos", "qr_ordering", "analytics", "loyalty", "kds", "api_access", "priority_support"],
        "trial_days": 0,
        "sort_order": 3,
        "is_public": True,
    },
]


async def seed_subscription_plans(db: AsyncSession) -> None:
    for plan_data in DEFAULT_PLANS:
        result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.name == plan_data["name"])
        )
        if result.scalar_one_or_none():
            continue
        plan = SubscriptionPlan(
            id=str(uuid.uuid4()),
            is_active=True,
            is_public=plan_data.get("is_public", True),
            is_featured=plan_data.get("is_featured", False),
            badge=plan_data.get("badge"),
            discount_yearly=0,
            **{k: v for k, v in plan_data.items() if k not in ("is_public", "is_featured", "badge")},
        )
        db.add(plan)
    await db.commit()


async def run_seed_subscription_plans() -> None:
    async with AsyncSessionLocal() as db:
        await seed_subscription_plans(db)
