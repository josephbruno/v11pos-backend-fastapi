from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import (
    get_current_active_user,
    get_current_superadmin,
    get_current_platform_admin,
    is_restaurant_admin,
)
from app.core.response import success_response, error_response
from app.modules.user.model import User
from app.modules.restaurant.model import SubscriptionPlanType, SubscriptionStatus
from app.modules.restaurant.schema import (
    RestaurantCreate,
    RestaurantUpdate,
    RestaurantResponse,
    SubscriptionPlanCreate,
    SubscriptionPlanUpdate,
    SubscriptionPlanResponse,
    SubscriptionCreate,
    SubscriptionResponse,
    InvoiceResponse,
    RestaurantInvitationCreate,
    RestaurantInvitationResponse,
    SubscriptionCheckoutRequest,
    SubscriptionVerifyRequest,
    SubscriptionAssignRequest,
    RestaurantSubscriptionStatusUpdate,
)
from app.modules.restaurant.service import (
    RestaurantService,
    SubscriptionPlanService,
    SubscriptionService,
    InvoiceService,
    RestaurantInvitationService,
)
from app.modules.billing.service import BillingService
from app.modules.billing.razorpay_client import RazorpayNotConfiguredError
from app.modules.restaurant.enforcement import SubscriptionEnforcementService


router = APIRouter(prefix="/restaurants", tags=["Restaurants"])


# ── Restaurant CRUD ──────────────────────────────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_restaurant(
    restaurant_data: RestaurantCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        existing = await RestaurantService.get_restaurant_by_slug(db, restaurant_data.slug)
        if existing:
            return error_response(
                message="Restaurant creation failed",
                error_code="SLUG_EXISTS",
                error_details=f"Slug '{restaurant_data.slug}' is already taken",
            )
        restaurant = await RestaurantService.create_restaurant(db, restaurant_data, current_user.id)
        return success_response(
            message="Restaurant created successfully",
            data=RestaurantResponse.model_validate(restaurant).model_dump(),
        )
    except IntegrityError:
        return error_response(
            message="Restaurant creation failed",
            error_code="INTEGRITY_ERROR",
            error_details="Slug or email already exists",
        )
    except Exception as e:
        return error_response(
            message="Restaurant creation failed",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.get("/all")
async def list_all_restaurants(
    skip: int = 0,
    limit: int = 500,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_superadmin),
):
    try:
        from sqlalchemy import select
        from app.modules.restaurant.model import Restaurant

        result = await db.execute(
            select(Restaurant)
            .where(Restaurant.deleted_at.is_(None))
            .order_by(Restaurant.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        restaurants = result.scalars().all()
        data = [RestaurantResponse.model_validate(r).model_dump() for r in restaurants]
        return success_response(message="All restaurants retrieved", data=data)
    except Exception as e:
        return error_response(message="Failed to retrieve restaurants", error_details=str(e))


@router.get("/my-restaurants")
async def get_my_restaurants(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        restaurants = await RestaurantService.get_user_restaurants(
            db, current_user.id, skip=skip, limit=limit
        )
        return success_response(
            message="Restaurants retrieved successfully",
            data=[RestaurantResponse.model_validate(r).model_dump() for r in restaurants],
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve restaurants",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


# ── Subscription plans (static paths before /{restaurant_id}) ─────────────────

@router.get("/subscription-plans")
async def get_subscription_plans(db: AsyncSession = Depends(get_db)):
    try:
        plans = await SubscriptionPlanService.get_active_plans(db)
        return success_response(
            message="Subscription plans retrieved successfully",
            data=[SubscriptionPlanResponse.model_validate(p).model_dump() for p in plans],
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve plans",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.get("/subscription-plans/all")
async def get_all_subscription_plans(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_platform_admin),
):
    try:
        plans = await SubscriptionPlanService.get_all_plans(db)
        return success_response(
            message="All subscription plans retrieved",
            data=[SubscriptionPlanResponse.model_validate(p).model_dump() for p in plans],
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve plans",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.post("/subscription-plans", status_code=status.HTTP_201_CREATED)
async def create_subscription_plan(
    plan_data: SubscriptionPlanCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_platform_admin),
):
    try:
        plan = await SubscriptionPlanService.create_plan(db, plan_data)
        plan = await BillingService.sync_plan_to_razorpay(db, plan)
        return success_response(
            message="Subscription plan created successfully",
            data=SubscriptionPlanResponse.model_validate(plan).model_dump(),
        )
    except IntegrityError:
        return error_response(
            message="Plan creation failed",
            error_code="INTEGRITY_ERROR",
            error_details="Plan name already exists",
        )
    except Exception as e:
        return error_response(
            message="Failed to create plan",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.put("/subscription-plans/{plan_id}")
async def update_subscription_plan(
    plan_id: str,
    plan_data: SubscriptionPlanUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_platform_admin),
):
    try:
        plan = await SubscriptionPlanService.update_plan(db, plan_id, plan_data)
        if not plan:
            return error_response(
                message="Plan not found",
                error_code="NOT_FOUND",
                error_details=f"Plan {plan_id} not found",
            )
        plan = await BillingService.sync_plan_to_razorpay(db, plan)
        return success_response(
            message="Subscription plan updated successfully",
            data=SubscriptionPlanResponse.model_validate(plan).model_dump(),
        )
    except Exception as e:
        return error_response(
            message="Failed to update plan",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.patch("/subscription-plans/{plan_id}/status")
async def update_subscription_plan_status(
    plan_id: str,
    is_active: bool,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_platform_admin),
):
    try:
        plan = await SubscriptionPlanService.update_plan(
            db, plan_id, SubscriptionPlanUpdate(is_active=is_active)
        )
        if not plan:
            return error_response(message="Plan not found", error_code="NOT_FOUND")
        return success_response(
            message="Plan status updated",
            data=SubscriptionPlanResponse.model_validate(plan).model_dump(),
        )
    except Exception as e:
        return error_response(message="Failed to update plan status", error_details=str(e))


@router.get("/subscriptions")
async def list_all_subscriptions(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[SubscriptionStatus] = Query(None, alias="status"),
    plan: Optional[SubscriptionPlanType] = Query(None),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_platform_admin),
):
    try:
        subs = await SubscriptionService.list_subscriptions(
            db, status_filter=status_filter, plan_filter=plan, skip=skip, limit=limit
        )
        return success_response(
            message="Subscriptions retrieved",
            data=[SubscriptionResponse.model_validate(s).model_dump() for s in subs],
        )
    except Exception as e:
        return error_response(message="Failed to list subscriptions", error_details=str(e))


@router.post("/subscriptions/{subscription_id}/cancel")
async def cancel_subscription(
    subscription_id: str,
    reason: str = None,
    immediate: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        sub = await SubscriptionService.get_subscription_by_id(db, subscription_id)
        if not sub:
            return error_response(
                message="Subscription not found",
                error_code="NOT_FOUND",
            )
        if not await is_restaurant_admin(db, current_user, sub.restaurant_id):
            return error_response(message="Access denied", error_code="FORBIDDEN")

        subscription = await SubscriptionService.cancel_subscription(
            db, subscription_id, current_user.id, reason, immediate
        )
        return success_response(
            message="Subscription cancelled successfully",
            data=SubscriptionResponse.model_validate(subscription).model_dump(),
        )
    except Exception as e:
        return error_response(
            message="Failed to cancel subscription",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.get("/slug/{slug}")
async def get_restaurant_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    try:
        restaurant = await RestaurantService.get_restaurant_by_slug(db, slug)
        if not restaurant:
            return error_response(
                message="Restaurant not found",
                error_code="NOT_FOUND",
                error_details=f"Restaurant with slug '{slug}' not found",
            )
        return success_response(
            message="Restaurant retrieved successfully",
            data=RestaurantResponse.model_validate(restaurant).model_dump(),
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve restaurant",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


# ── Restaurant by ID ───────────────────────────────────────────────────────────

@router.get("/{restaurant_id}")
async def get_restaurant(
    restaurant_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        restaurant = await RestaurantService.get_restaurant_by_id(db, restaurant_id)
        if not restaurant:
            return error_response(
                message="Restaurant not found",
                error_code="NOT_FOUND",
            )
        return success_response(
            message="Restaurant retrieved successfully",
            data=RestaurantResponse.model_validate(restaurant).model_dump(),
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve restaurant",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.put("/{restaurant_id}")
async def update_restaurant(
    restaurant_id: str,
    restaurant_data: RestaurantUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        restaurant = await RestaurantService.update_restaurant(db, restaurant_id, restaurant_data)
        if not restaurant:
            return error_response(message="Restaurant not found", error_code="NOT_FOUND")
        return success_response(
            message="Restaurant updated successfully",
            data=RestaurantResponse.model_validate(restaurant).model_dump(),
        )
    except Exception as e:
        return error_response(
            message="Failed to update restaurant",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.delete("/{restaurant_id}")
async def delete_restaurant(
    restaurant_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        deleted = await RestaurantService.delete_restaurant(db, restaurant_id)
        if not deleted:
            return error_response(message="Restaurant not found", error_code="NOT_FOUND")
        return success_response(
            message="Restaurant deleted successfully",
            data={"deleted_restaurant_id": restaurant_id},
        )
    except Exception as e:
        return error_response(
            message="Failed to delete restaurant",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


# ── Per-restaurant subscription ──────────────────────────────────────────────

@router.get("/{restaurant_id}/subscription")
async def get_active_subscription(
    restaurant_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not await is_restaurant_admin(db, current_user, restaurant_id):
        return error_response(message="Access denied", error_code="FORBIDDEN")
    try:
        subscription = await SubscriptionService.get_active_subscription(db, restaurant_id)
        if not subscription:
            restaurant = await RestaurantService.get_restaurant_by_id(db, restaurant_id)
            return success_response(
                message="No paid subscription; showing restaurant plan info",
                data={
                    "subscription": None,
                    "restaurant_plan": restaurant.subscription_plan.value if restaurant else None,
                    "subscription_status": restaurant.subscription_status.value if restaurant else None,
                    "trial_ends_at": restaurant.trial_ends_at.isoformat() if restaurant and restaurant.trial_ends_at else None,
                },
            )
        return success_response(
            message="Subscription retrieved successfully",
            data=SubscriptionResponse.model_validate(subscription).model_dump(),
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve subscription",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.post("/{restaurant_id}/subscriptions", status_code=status.HTTP_201_CREATED)
async def create_subscription(
    restaurant_id: str,
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not await is_restaurant_admin(db, current_user, restaurant_id):
        return error_response(message="Access denied", error_code="FORBIDDEN")
    subscription_data.restaurant_id = restaurant_id
    try:
        subscription = await SubscriptionService.create_subscription(db, subscription_data)
        return success_response(
            message="Subscription created successfully",
            data=SubscriptionResponse.model_validate(subscription).model_dump(),
        )
    except ValueError as e:
        return error_response(
            message="Subscription creation failed",
            error_code="INVALID_PLAN",
            error_details=str(e),
        )
    except Exception as e:
        return error_response(
            message="Failed to create subscription",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.post("/{restaurant_id}/subscriptions/checkout")
async def subscription_checkout(
    restaurant_id: str,
    body: SubscriptionCheckoutRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not await is_restaurant_admin(db, current_user, restaurant_id):
        return error_response(message="Access denied", error_code="FORBIDDEN")
    try:
        checkout = await BillingService.create_checkout(
            db, restaurant_id, body.plan_id, body.billing_cycle
        )
        return success_response(message="Checkout created", data=checkout)
    except RazorpayNotConfiguredError as e:
        return error_response(
            message="Payment gateway not configured",
            error_code="RAZORPAY_NOT_CONFIGURED",
            error_details=str(e),
        )
    except ValueError as e:
        return error_response(message="Checkout failed", error_code="INVALID_REQUEST", error_details=str(e))
    except Exception as e:
        return error_response(message="Checkout failed", error_code="INTERNAL_ERROR", error_details=str(e))


@router.post("/{restaurant_id}/subscriptions/verify")
async def subscription_verify(
    restaurant_id: str,
    body: SubscriptionVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not await is_restaurant_admin(db, current_user, restaurant_id):
        return error_response(message="Access denied", error_code="FORBIDDEN")
    try:
        sub = await BillingService.verify_checkout(db, restaurant_id, body.razorpay_subscription_id)
        if not sub:
            return error_response(message="Subscription not verified", error_code="NOT_FOUND")
        return success_response(
            message="Subscription verified",
            data=SubscriptionResponse.model_validate(sub).model_dump(),
        )
    except Exception as e:
        return error_response(message="Verification failed", error_details=str(e))


@router.post("/{restaurant_id}/subscriptions/assign", status_code=status.HTTP_201_CREATED)
async def assign_subscription(
    restaurant_id: str,
    body: SubscriptionAssignRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_platform_admin),
):
    try:
        subscription = await BillingService.assign_subscription_admin(
            db, restaurant_id, body.plan_name, body.billing_cycle
        )
        return success_response(
            message="Subscription assigned",
            data=SubscriptionResponse.model_validate(subscription).model_dump(),
        )
    except ValueError as e:
        return error_response(message="Assignment failed", error_code="INVALID_REQUEST", error_details=str(e))
    except Exception as e:
        return error_response(message="Assignment failed", error_details=str(e))


@router.patch("/{restaurant_id}/subscription-status")
async def update_restaurant_subscription_status(
    restaurant_id: str,
    body: RestaurantSubscriptionStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_platform_admin),
):
    try:
        restaurant = await RestaurantService.get_restaurant_by_id(db, restaurant_id)
        if not restaurant:
            return error_response(message="Restaurant not found", error_code="NOT_FOUND")
        restaurant.subscription_status = body.subscription_status
        restaurant.is_suspended = body.is_suspended
        restaurant.suspension_reason = body.suspension_reason
        await db.commit()
        await db.refresh(restaurant)
        return success_response(
            message="Subscription status updated",
            data=RestaurantResponse.model_validate(restaurant).model_dump(),
        )
    except Exception as e:
        return error_response(message="Failed to update status", error_details=str(e))


@router.get("/{restaurant_id}/invoices")
async def get_restaurant_invoices(
    restaurant_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not await is_restaurant_admin(db, current_user, restaurant_id):
        return error_response(message="Access denied", error_code="FORBIDDEN")
    try:
        invoices = await InvoiceService.get_restaurant_invoices(db, restaurant_id, skip=skip, limit=limit)
        return success_response(
            message="Invoices retrieved successfully",
            data=[InvoiceResponse.model_validate(i).model_dump() for i in invoices],
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve invoices",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.get("/{restaurant_id}/usage-limits")
async def check_usage_limits(
    restaurant_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not await is_restaurant_admin(db, current_user, restaurant_id):
        return error_response(message="Access denied", error_code="FORBIDDEN")
    try:
        restaurant = await RestaurantService.get_restaurant_by_id(db, restaurant_id)
        if not restaurant:
            return error_response(message="Restaurant not found", error_code="NOT_FOUND")

        usage_data = {
            "subscription_plan": restaurant.subscription_plan.value,
            "subscription_status": restaurant.subscription_status.value,
            "trial_ends_at": restaurant.trial_ends_at.isoformat() if restaurant.trial_ends_at else None,
            "is_operational": SubscriptionEnforcementService.is_subscription_operational(restaurant),
            "users": {
                "current": restaurant.current_users,
                "max": restaurant.max_users,
                "available": max(0, restaurant.max_users - restaurant.current_users),
                "percentage": (restaurant.current_users / restaurant.max_users * 100)
                if restaurant.max_users > 0
                else 0,
            },
            "products": {
                "current": restaurant.current_products,
                "max": restaurant.max_products,
                "available": max(0, restaurant.max_products - restaurant.current_products),
                "percentage": (restaurant.current_products / restaurant.max_products * 100)
                if restaurant.max_products > 0
                else 0,
            },
            "orders": {
                "current": restaurant.current_orders_this_month,
                "max": restaurant.max_orders_per_month,
                "available": max(
                    0, restaurant.max_orders_per_month - restaurant.current_orders_this_month
                ),
                "percentage": (
                    restaurant.current_orders_this_month / restaurant.max_orders_per_month * 100
                )
                if restaurant.max_orders_per_month > 0
                else 0,
            },
        }
        return success_response(message="Usage limits retrieved successfully", data=usage_data)
    except Exception as e:
        return error_response(
            message="Failed to retrieve usage limits",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


# ── Invitations ──────────────────────────────────────────────────────────────

@router.post("/{restaurant_id}/invitations", status_code=status.HTTP_201_CREATED)
async def create_invitation(
    restaurant_id: str,
    invitation_data: RestaurantInvitationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        invitation = await RestaurantInvitationService.create_invitation(
            db, restaurant_id, invitation_data, current_user.id
        )
        return success_response(
            message="Invitation created successfully",
            data=RestaurantInvitationResponse.model_validate(invitation).model_dump(),
        )
    except Exception as e:
        return error_response(
            message="Failed to create invitation",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )


@router.post("/invitations/{token}/accept")
async def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        invitation = await RestaurantInvitationService.accept_invitation(db, token, current_user.id)
        if not invitation:
            return error_response(
                message="Invitation not found or expired",
                error_code="INVALID_TOKEN",
            )
        return success_response(
            message="Invitation accepted successfully",
            data=RestaurantInvitationResponse.model_validate(invitation).model_dump(),
        )
    except Exception as e:
        return error_response(
            message="Failed to accept invitation",
            error_code="INTERNAL_ERROR",
            error_details=str(e),
        )
