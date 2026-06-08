"""Billing orchestration: Razorpay sync, checkout, webhooks, restaurant state sync."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.modules.billing.razorpay_client import (
    RazorpayNotConfiguredError,
    cancel_razorpay_subscription,
    create_razorpay_plan,
    create_razorpay_subscription,
    get_razorpay_client,
)
from app.modules.restaurant.model import (
    Invoice,
    InvoiceStatus,
    Restaurant,
    Subscription,
    SubscriptionPlan,
    SubscriptionPlanType,
    SubscriptionStatus,
)
from app.modules.restaurant.schema import InvoiceCreate
from app.modules.restaurant.service import InvoiceService, RestaurantService, SubscriptionPlanService


class BillingService:
    @staticmethod
    async def sync_plan_to_razorpay(db: AsyncSession, plan: SubscriptionPlan) -> SubscriptionPlan:
        """Create or refresh Razorpay plans for monthly/yearly billing cycles."""
        if plan.name == SubscriptionPlanType.TRIAL.value:
            return plan

        try:
            if plan.price_monthly > 0 and not plan.razorpay_plan_id_monthly:
                rz_monthly = create_razorpay_plan(
                    period="monthly",
                    interval=1,
                    item_name=f"{plan.display_name} (Monthly)",
                    amount_paise=plan.price_monthly,
                    description=plan.description,
                )
                plan.razorpay_plan_id_monthly = rz_monthly["id"]

            if plan.price_yearly > 0 and not plan.razorpay_plan_id_yearly:
                rz_yearly = create_razorpay_plan(
                    period="yearly",
                    interval=1,
                    item_name=f"{plan.display_name} (Yearly)",
                    amount_paise=plan.price_yearly,
                    description=plan.description,
                )
                plan.razorpay_plan_id_yearly = rz_yearly["id"]

            await db.commit()
            await db.refresh(plan)
        except RazorpayNotConfiguredError:
            pass
        return plan

    @staticmethod
    async def sync_restaurant_from_plan(
        db: AsyncSession,
        restaurant: Restaurant,
        plan: SubscriptionPlan,
        subscription: Subscription | None = None,
        status: SubscriptionStatus = SubscriptionStatus.ACTIVE,
    ) -> Restaurant:
        restaurant.subscription_plan = SubscriptionPlanType(plan.name)
        restaurant.subscription_status = status
        restaurant.max_users = plan.max_users
        restaurant.max_products = plan.max_products
        restaurant.max_orders_per_month = plan.max_orders_per_month
        restaurant.max_locations = plan.max_locations
        restaurant.features = plan.features
        if subscription:
            restaurant.subscription_started_at = subscription.started_at
            if subscription.trial_end:
                restaurant.trial_ends_at = subscription.trial_end
        restaurant.is_suspended = status not in (SubscriptionStatus.ACTIVE,)
        await db.commit()
        await db.refresh(restaurant)
        return restaurant

    @staticmethod
    async def create_checkout(
        db: AsyncSession,
        restaurant_id: str,
        plan_id: str,
        billing_cycle: str = "monthly",
    ) -> dict[str, Any]:
        restaurant = await RestaurantService.get_restaurant_by_id(db, restaurant_id)
        if not restaurant:
            raise ValueError("Restaurant not found")

        plan_result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
        )
        plan = plan_result.scalar_one_or_none()
        if not plan or not plan.is_active:
            raise ValueError("Plan not found or inactive")

        await BillingService.sync_plan_to_razorpay(db, plan)
        await db.refresh(plan)

        rz_plan_id = (
            plan.razorpay_plan_id_monthly
            if billing_cycle == "monthly"
            else plan.razorpay_plan_id_yearly
        )
        if not rz_plan_id:
            raise RazorpayNotConfiguredError("Razorpay plan not synced for this billing cycle")

        total_count = 12 if billing_cycle == "monthly" else 1
        rz_sub = create_razorpay_subscription(
            plan_id=rz_plan_id,
            total_count=total_count,
            notes={
                "restaurant_id": restaurant_id,
                "plan_id": plan.id,
                "billing_cycle": billing_cycle,
            },
        )

        now = datetime.utcnow()
        period_end = now + timedelta(days=30 if billing_cycle == "monthly" else 365)

        subscription = Subscription(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            plan=SubscriptionPlanType(plan.name),
            plan_name=plan.display_name,
            status=SubscriptionStatus.PAST_DUE,
            price_per_month=plan.price_monthly,
            price_per_year=plan.price_yearly,
            billing_cycle=billing_cycle,
            started_at=now,
            current_period_start=now,
            current_period_end=period_end,
            payment_method="razorpay",
            payment_gateway_subscription_id=rz_sub["id"],
        )
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)

        return {
            "subscription_id": subscription.id,
            "razorpay_subscription_id": rz_sub["id"],
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
            "plan_name": plan.display_name,
            "amount": plan.price_monthly if billing_cycle == "monthly" else plan.price_yearly,
            "currency": "INR",
            "billing_cycle": billing_cycle,
            "prefill": {
                "name": restaurant.business_name or restaurant.name,
                "email": restaurant.email,
                "contact": restaurant.phone,
            },
        }

    @staticmethod
    async def assign_subscription_admin(
        db: AsyncSession,
        restaurant_id: str,
        plan_name: str,
        billing_cycle: str = "monthly",
    ) -> Subscription:
        plan = await SubscriptionPlanService.get_plan_by_name(db, plan_name)
        if not plan:
            raise ValueError(f"Plan {plan_name} not found")

        restaurant = await RestaurantService.get_restaurant_by_id(db, restaurant_id)
        if not restaurant:
            raise ValueError("Restaurant not found")

        now = datetime.utcnow()
        period_end = now + timedelta(days=30 if billing_cycle == "monthly" else 365)

        subscription = Subscription(
            id=str(uuid.uuid4()),
            restaurant_id=restaurant_id,
            plan=SubscriptionPlanType(plan.name),
            plan_name=plan.display_name,
            status=SubscriptionStatus.ACTIVE,
            price_per_month=plan.price_monthly,
            price_per_year=plan.price_yearly,
            billing_cycle=billing_cycle,
            started_at=now,
            current_period_start=now,
            current_period_end=period_end,
            payment_method="admin_assigned",
        )
        db.add(subscription)
        await db.flush()
        await BillingService.sync_restaurant_from_plan(
            db, restaurant, plan, subscription, SubscriptionStatus.ACTIVE
        )
        await db.refresh(subscription)
        return subscription

    @staticmethod
    async def handle_webhook(db: AsyncSession, event: dict[str, Any]) -> None:
        event_type = event.get("event", "")
        payload = event.get("payload", {})

        if event_type == "subscription.activated":
            await BillingService._on_subscription_activated(db, payload)
        elif event_type == "subscription.charged":
            await BillingService._on_subscription_charged(db, payload)
        elif event_type in ("subscription.cancelled", "subscription.halted"):
            await BillingService._on_subscription_ended(db, payload, event_type)
        elif event_type == "payment.failed":
            await BillingService._on_payment_failed(db, payload)

    @staticmethod
    async def _get_subscription_by_rz_id(
        db: AsyncSession, rz_subscription_id: str
    ) -> Optional[Subscription]:
        result = await db.execute(
            select(Subscription).where(
                Subscription.payment_gateway_subscription_id == rz_subscription_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _on_subscription_activated(db: AsyncSession, payload: dict) -> None:
        entity = payload.get("subscription", {}).get("entity", {})
        rz_id = entity.get("id")
        if not rz_id:
            return
        subscription = await BillingService._get_subscription_by_rz_id(db, rz_id)
        if not subscription:
            return

        subscription.status = SubscriptionStatus.ACTIVE
        plan = await SubscriptionPlanService.get_plan_by_name(db, subscription.plan.value)
        if plan:
            restaurant = await RestaurantService.get_restaurant_by_id(db, subscription.restaurant_id)
            if restaurant:
                await BillingService.sync_restaurant_from_plan(
                    db, restaurant, plan, subscription, SubscriptionStatus.ACTIVE
                )
        await db.commit()

    @staticmethod
    async def _on_subscription_charged(db: AsyncSession, payload: dict) -> None:
        payment = payload.get("payment", {}).get("entity", {})
        rz_sub_id = payment.get("subscription_id")
        if not rz_sub_id:
            return
        subscription = await BillingService._get_subscription_by_rz_id(db, rz_sub_id)
        if not subscription:
            return

        amount = int(payment.get("amount", 0))
        subscription.last_payment_date = datetime.utcnow()
        subscription.status = SubscriptionStatus.ACTIVE

        invoice_data = InvoiceCreate(
            subscription_id=subscription.id,
            restaurant_id=subscription.restaurant_id,
            amount=amount,
            tax=0,
            total=amount,
            currency="INR",
            description=f"Subscription charge — {subscription.plan_name}",
        )
        await InvoiceService.create_invoice(db, invoice_data)

        plan = await SubscriptionPlanService.get_plan_by_name(db, subscription.plan.value)
        if plan:
            restaurant = await RestaurantService.get_restaurant_by_id(db, subscription.restaurant_id)
            if restaurant:
                await BillingService.sync_restaurant_from_plan(
                    db, restaurant, plan, subscription, SubscriptionStatus.ACTIVE
                )

    @staticmethod
    async def _on_subscription_ended(
        db: AsyncSession, payload: dict, event_type: str
    ) -> None:
        entity = payload.get("subscription", {}).get("entity", {})
        rz_id = entity.get("id")
        if not rz_id:
            return
        subscription = await BillingService._get_subscription_by_rz_id(db, rz_id)
        if not subscription:
            return

        subscription.status = (
            SubscriptionStatus.CANCELLED
            if event_type == "subscription.cancelled"
            else SubscriptionStatus.SUSPENDED
        )
        subscription.ended_at = datetime.utcnow()

        restaurant = await RestaurantService.get_restaurant_by_id(db, subscription.restaurant_id)
        if restaurant:
            restaurant.subscription_status = subscription.status
            restaurant.is_suspended = True
        await db.commit()

    @staticmethod
    async def _on_payment_failed(db: AsyncSession, payload: dict) -> None:
        payment = payload.get("payment", {}).get("entity", {})
        rz_sub_id = payment.get("subscription_id")
        if not rz_sub_id:
            return
        subscription = await BillingService._get_subscription_by_rz_id(db, rz_sub_id)
        if not subscription:
            return
        subscription.status = SubscriptionStatus.PAST_DUE
        restaurant = await RestaurantService.get_restaurant_by_id(db, subscription.restaurant_id)
        if restaurant:
            restaurant.subscription_status = SubscriptionStatus.PAST_DUE
        await db.commit()

    @staticmethod
    async def cancel_razorpay_if_needed(
        db: AsyncSession,
        subscription: Subscription,
        immediate: bool = False,
    ) -> None:
        if not subscription.payment_gateway_subscription_id:
            return
        try:
            cancel_razorpay_subscription(
                subscription.payment_gateway_subscription_id,
                cancel_at_cycle_end=not immediate,
            )
        except RazorpayNotConfiguredError:
            pass

    @staticmethod
    async def verify_checkout(
        db: AsyncSession,
        restaurant_id: str,
        razorpay_subscription_id: str,
    ) -> Optional[Subscription]:
        """Poll Razorpay subscription status after checkout."""
        try:
            client = get_razorpay_client()
            rz_sub = client.subscription.fetch(razorpay_subscription_id)
        except Exception:
            return None

        status_map = {
            "active": SubscriptionStatus.ACTIVE,
            "authenticated": SubscriptionStatus.ACTIVE,
            "created": SubscriptionStatus.PAST_DUE,
            "halted": SubscriptionStatus.SUSPENDED,
            "cancelled": SubscriptionStatus.CANCELLED,
            "completed": SubscriptionStatus.EXPIRED,
        }
        rz_status = rz_sub.get("status", "")
        sub = await BillingService._get_subscription_by_rz_id(db, razorpay_subscription_id)
        if not sub or sub.restaurant_id != restaurant_id:
            return None

        new_status = status_map.get(rz_status, SubscriptionStatus.PAST_DUE)
        if new_status == SubscriptionStatus.ACTIVE:
            sub.status = SubscriptionStatus.ACTIVE
            plan = await SubscriptionPlanService.get_plan_by_name(db, sub.plan.value)
            if plan:
                restaurant = await RestaurantService.get_restaurant_by_id(db, restaurant_id)
                if restaurant:
                    await BillingService.sync_restaurant_from_plan(
                        db, restaurant, plan, sub, SubscriptionStatus.ACTIVE
                    )
        await db.commit()
        await db.refresh(sub)
        return sub
