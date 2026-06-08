"""Celery tasks for subscription lifecycle."""

from __future__ import annotations

import asyncio
from datetime import datetime

from sqlalchemy import select, update

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.modules.restaurant.model import Restaurant, SubscriptionPlanType, SubscriptionStatus


async def _expire_trials() -> int:
    now = datetime.utcnow()
    count = 0
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Restaurant).where(
                Restaurant.trial_ends_at.isnot(None),
                Restaurant.trial_ends_at < now,
                Restaurant.subscription_plan == SubscriptionPlanType.TRIAL,
                Restaurant.subscription_status == SubscriptionStatus.ACTIVE,
            )
        )
        restaurants = result.scalars().all()
        for r in restaurants:
            r.subscription_status = SubscriptionStatus.EXPIRED
            r.is_suspended = True
            r.suspension_reason = "Trial period expired"
            count += 1
        await db.commit()
    return count


async def _reset_monthly_orders() -> int:
    async with AsyncSessionLocal() as db:
        await db.execute(update(Restaurant).values(current_orders_this_month=0))
        await db.commit()
    return 0


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="billing.expire_trials")
def expire_trials_task():
    return _run_async(_expire_trials())


@celery_app.task(name="billing.reset_monthly_orders")
def reset_monthly_orders_task():
    return _run_async(_reset_monthly_orders())
