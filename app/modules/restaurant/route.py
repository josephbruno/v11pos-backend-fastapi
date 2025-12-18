from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.response import success_response, error_response
from app.modules.user.model import User
from app.modules.restaurant.schema import (
    RestaurantCreate,
    RestaurantUpdate,
    RestaurantResponse,
    SubscriptionPlanCreate,
    SubscriptionPlanUpdate,
    SubscriptionPlanResponse,
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionResponse,
    InvoiceCreate,
    InvoiceResponse,
    RestaurantInvitationCreate,
    RestaurantInvitationResponse,
    RestaurantOwnerResponse
)
from app.modules.restaurant.service import (
    RestaurantService,
    SubscriptionPlanService,
    SubscriptionService,
    InvoiceService,
    RestaurantInvitationService
)


router = APIRouter(prefix="/restaurants", tags=["Restaurants"])


# Restaurant Endpoints

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_restaurant(
    restaurant_data: RestaurantCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new restaurant
    
    - **name**: Restaurant name
    - **slug**: Unique URL-friendly identifier
    - **business_name**: Legal business name
    - **email**: Contact email
    - **phone**: Contact phone
    - **gstin**: GST Number (India)
    - **fssai_license**: FSSAI License (India)
    - **pan_number**: PAN Card (India)
    """
    try:
        # Check if slug already exists
        existing = await RestaurantService.get_restaurant_by_slug(db, restaurant_data.slug)
        if existing:
            return error_response(
                message="Restaurant creation failed",
                error_code="SLUG_EXISTS",
                error_details=f"Slug '{restaurant_data.slug}' is already taken"
            )
        
        restaurant = await RestaurantService.create_restaurant(
            db,
            restaurant_data,
            current_user.id
        )
        
        return success_response(
            message="Restaurant created successfully",
            data=RestaurantResponse.model_validate(restaurant).model_dump()
        )
    
    except IntegrityError as e:
        return error_response(
            message="Restaurant creation failed",
            error_code="INTEGRITY_ERROR",
            error_details="Slug or email already exists"
        )
    except Exception as e:
        return error_response(
            message="Restaurant creation failed",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.get("/my-restaurants")
async def get_my_restaurants(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all restaurants owned by current user"""
    try:
        restaurants = await RestaurantService.get_user_restaurants(
            db,
            current_user.id,
            skip=skip,
            limit=limit
        )
        
        restaurants_data = [
            RestaurantResponse.model_validate(r).model_dump()
            for r in restaurants
        ]
        
        return success_response(
            message="Restaurants retrieved successfully",
            data=restaurants_data
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve restaurants",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.get("/{restaurant_id}")
async def get_restaurant(
    restaurant_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get restaurant by ID"""
    try:
        restaurant = await RestaurantService.get_restaurant_by_id(db, restaurant_id)
        
        if not restaurant:
            return error_response(
                message="Restaurant not found",
                error_code="NOT_FOUND",
                error_details=f"Restaurant with ID {restaurant_id} not found"
            )
        
        return success_response(
            message="Restaurant retrieved successfully",
            data=RestaurantResponse.model_validate(restaurant).model_dump()
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve restaurant",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.get("/slug/{slug}")
async def get_restaurant_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Get restaurant by slug (public endpoint)"""
    try:
        restaurant = await RestaurantService.get_restaurant_by_slug(db, slug)
        
        if not restaurant:
            return error_response(
                message="Restaurant not found",
                error_code="NOT_FOUND",
                error_details=f"Restaurant with slug '{slug}' not found"
            )
        
        return success_response(
            message="Restaurant retrieved successfully",
            data=RestaurantResponse.model_validate(restaurant).model_dump()
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve restaurant",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.put("/{restaurant_id}")
async def update_restaurant(
    restaurant_id: str,
    restaurant_data: RestaurantUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update restaurant"""
    try:
        restaurant = await RestaurantService.update_restaurant(
            db,
            restaurant_id,
            restaurant_data
        )
        
        if not restaurant:
            return error_response(
                message="Restaurant not found",
                error_code="NOT_FOUND",
                error_details=f"Restaurant with ID {restaurant_id} not found"
            )
        
        return success_response(
            message="Restaurant updated successfully",
            data=RestaurantResponse.model_validate(restaurant).model_dump()
        )
    except Exception as e:
        return error_response(
            message="Failed to update restaurant",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.delete("/{restaurant_id}")
async def delete_restaurant(
    restaurant_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete restaurant (soft delete)"""
    try:
        deleted = await RestaurantService.delete_restaurant(db, restaurant_id)
        
        if not deleted:
            return error_response(
                message="Restaurant not found",
                error_code="NOT_FOUND",
                error_details=f"Restaurant with ID {restaurant_id} not found"
            )
        
        return success_response(
            message="Restaurant deleted successfully",
            data={"deleted_restaurant_id": restaurant_id}
        )
    except Exception as e:
        return error_response(
            message="Failed to delete restaurant",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


# Subscription Plan Endpoints

@router.post("/subscription-plans", status_code=status.HTTP_201_CREATED)
async def create_subscription_plan(
    plan_data: SubscriptionPlanCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new subscription plan (admin only)"""
    try:
        if not current_user.is_superuser:
            return error_response(
                message="Access denied",
                error_code="FORBIDDEN",
                error_details="Only superusers can create subscription plans"
            )
        
        plan = await SubscriptionPlanService.create_plan(db, plan_data)
        
        return success_response(
            message="Subscription plan created successfully",
            data=SubscriptionPlanResponse.model_validate(plan).model_dump()
        )
    except IntegrityError:
        return error_response(
            message="Plan creation failed",
            error_code="INTEGRITY_ERROR",
            error_details="Plan name already exists"
        )
    except Exception as e:
        return error_response(
            message="Failed to create plan",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.get("/subscription-plans")
async def get_subscription_plans(db: AsyncSession = Depends(get_db)):
    """Get all active subscription plans (public endpoint)"""
    try:
        plans = await SubscriptionPlanService.get_active_plans(db)
        plans_data = [
            SubscriptionPlanResponse.model_validate(p).model_dump()
            for p in plans
        ]
        
        return success_response(
            message="Subscription plans retrieved successfully",
            data=plans_data
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve plans",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


# Subscription Endpoints

@router.post("/{restaurant_id}/subscriptions", status_code=status.HTTP_201_CREATED)
async def create_subscription(
    restaurant_id: str,
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new subscription for restaurant"""
    try:
        subscription = await SubscriptionService.create_subscription(db, subscription_data)
        
        return success_response(
            message="Subscription created successfully",
            data=SubscriptionResponse.model_validate(subscription).model_dump()
        )
    except ValueError as e:
        return error_response(
            message="Subscription creation failed",
            error_code="INVALID_PLAN",
            error_details=str(e)
        )
    except Exception as e:
        return error_response(
            message="Failed to create subscription",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.get("/{restaurant_id}/subscription")
async def get_active_subscription(
    restaurant_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get active subscription for restaurant"""
    try:
        subscription = await SubscriptionService.get_active_subscription(db, restaurant_id)
        
        if not subscription:
            return error_response(
                message="No active subscription found",
                error_code="NOT_FOUND",
                error_details=f"No active subscription for restaurant {restaurant_id}"
            )
        
        return success_response(
            message="Subscription retrieved successfully",
            data=SubscriptionResponse.model_validate(subscription).model_dump()
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve subscription",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.post("/subscriptions/{subscription_id}/cancel")
async def cancel_subscription(
    subscription_id: str,
    reason: str = None,
    immediate: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel a subscription"""
    try:
        subscription = await SubscriptionService.cancel_subscription(
            db,
            subscription_id,
            current_user.id,
            reason,
            immediate
        )
        
        if not subscription:
            return error_response(
                message="Subscription not found",
                error_code="NOT_FOUND",
                error_details=f"Subscription with ID {subscription_id} not found"
            )
        
        return success_response(
            message="Subscription cancelled successfully",
            data=SubscriptionResponse.model_validate(subscription).model_dump()
        )
    except Exception as e:
        return error_response(
            message="Failed to cancel subscription",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


# Invoice Endpoints

@router.get("/{restaurant_id}/invoices")
async def get_restaurant_invoices(
    restaurant_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all invoices for a restaurant"""
    try:
        invoices = await InvoiceService.get_restaurant_invoices(
            db,
            restaurant_id,
            skip=skip,
            limit=limit
        )
        
        invoices_data = [
            InvoiceResponse.model_validate(i).model_dump()
            for i in invoices
        ]
        
        return success_response(
            message="Invoices retrieved successfully",
            data=invoices_data
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve invoices",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


# Invitation Endpoints

@router.post("/{restaurant_id}/invitations", status_code=status.HTTP_201_CREATED)
async def create_invitation(
    restaurant_id: str,
    invitation_data: RestaurantInvitationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a restaurant invitation"""
    try:
        invitation = await RestaurantInvitationService.create_invitation(
            db,
            restaurant_id,
            invitation_data,
            current_user.id
        )
        
        return success_response(
            message="Invitation created successfully",
            data=RestaurantInvitationResponse.model_validate(invitation).model_dump()
        )
    except Exception as e:
        return error_response(
            message="Failed to create invitation",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.post("/invitations/{token}/accept")
async def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Accept a restaurant invitation"""
    try:
        invitation = await RestaurantInvitationService.accept_invitation(
            db,
            token,
            current_user.id
        )
        
        if not invitation:
            return error_response(
                message="Invitation not found or expired",
                error_code="INVALID_TOKEN",
                error_details="Invalid or expired invitation token"
            )
        
        return success_response(
            message="Invitation accepted successfully",
            data=RestaurantInvitationResponse.model_validate(invitation).model_dump()
        )
    except Exception as e:
        return error_response(
            message="Failed to accept invitation",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


# Usage Limit Endpoints

@router.get("/{restaurant_id}/usage-limits")
async def check_usage_limits(
    restaurant_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Check usage limits for restaurant"""
    try:
        restaurant = await RestaurantService.get_restaurant_by_id(db, restaurant_id)
        
        if not restaurant:
            return error_response(
                message="Restaurant not found",
                error_code="NOT_FOUND",
                error_details=f"Restaurant with ID {restaurant_id} not found"
            )
        
        usage_data = {
            "users": {
                "current": restaurant.current_users,
                "max": restaurant.max_users,
                "available": restaurant.max_users - restaurant.current_users,
                "percentage": (restaurant.current_users / restaurant.max_users * 100) if restaurant.max_users > 0 else 0
            },
            "products": {
                "current": restaurant.current_products,
                "max": restaurant.max_products,
                "available": restaurant.max_products - restaurant.current_products,
                "percentage": (restaurant.current_products / restaurant.max_products * 100) if restaurant.max_products > 0 else 0
            },
            "orders": {
                "current": restaurant.current_orders_this_month,
                "max": restaurant.max_orders_per_month,
                "available": restaurant.max_orders_per_month - restaurant.current_orders_this_month,
                "percentage": (restaurant.current_orders_this_month / restaurant.max_orders_per_month * 100) if restaurant.max_orders_per_month > 0 else 0
            }
        }
        
        return success_response(
            message="Usage limits retrieved successfully",
            data=usage_data
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve usage limits",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )
