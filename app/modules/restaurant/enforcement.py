"""Subscription and usage-limit enforcement for multi-tenant restaurants."""

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.restaurant.model import Restaurant, SubscriptionStatus
from app.modules.restaurant.service import RestaurantService


class SubscriptionEnforcementService:
    """Guards restaurant operations based on subscription state and plan limits."""

    @staticmethod
    def is_trial_valid(restaurant: Restaurant) -> bool:
        if restaurant.trial_ends_at is None:
            return False
        return datetime.utcnow() < restaurant.trial_ends_at

    @staticmethod
    def is_subscription_operational(restaurant: Restaurant) -> bool:
        if restaurant.is_suspended:
            return False
        if SubscriptionEnforcementService.is_trial_valid(restaurant):
            return True
        if restaurant.subscription_status in (
            SubscriptionStatus.CANCELLED,
            SubscriptionStatus.EXPIRED,
            SubscriptionStatus.SUSPENDED,
            SubscriptionStatus.PAST_DUE,
        ):
            return False
        return restaurant.subscription_status == SubscriptionStatus.ACTIVE

    @staticmethod
    async def assert_operational(db: AsyncSession, restaurant_id: str) -> Restaurant:
        restaurant = await RestaurantService.get_restaurant_by_id(db, restaurant_id)
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurant not found",
            )
        if not SubscriptionEnforcementService.is_subscription_operational(restaurant):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "SUBSCRIPTION_INACTIVE",
                    "message": "Subscription inactive or trial expired. Please renew your plan.",
                    "subscription_status": restaurant.subscription_status.value,
                    "trial_ends_at": restaurant.trial_ends_at.isoformat()
                    if restaurant.trial_ends_at
                    else None,
                },
            )
        return restaurant

    @staticmethod
    async def assert_within_limit(
        db: AsyncSession,
        restaurant_id: str,
        resource_type: str,
    ) -> Restaurant:
        restaurant = await SubscriptionEnforcementService.assert_operational(db, restaurant_id)
        within = await RestaurantService.check_usage_limits(db, restaurant_id, resource_type)
        if not within:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "USAGE_LIMIT_EXCEEDED",
                    "message": f"Plan limit reached for {resource_type}. Upgrade your subscription.",
                    "resource": resource_type,
                },
            )
        return restaurant
