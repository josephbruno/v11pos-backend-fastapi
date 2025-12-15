"""
Platform Admin Routes - SuperAdmin Dashboard
Monitor and manage all restaurants across the platform
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import Optional

from app.database import get_db
from app.dependencies import require_platform_admin
from app.models.restaurant import Restaurant, Subscription, SubscriptionPlan
from app.models.user import User
from app.models.product import Product
from app.models.order import Order
from app.models.customer import Customer
from app.response_formatter import success_response, error_response

router = APIRouter(prefix="/api/v1/platform", tags=["Platform Admin"])


@router.get("/dashboard")
async def platform_dashboard(
    token_data: dict = Depends(require_platform_admin),
    db: Session = Depends(get_db)
):
    """
    Platform-wide dashboard for SuperAdmin
    Shows overview of all restaurants, users, orders, and revenue
    """
    
    # Restaurant stats
    total_restaurants = db.query(Restaurant).count()
    active_restaurants = db.query(Restaurant).filter(
        Restaurant.is_active == True,
        Restaurant.is_suspended == False
    ).count()
    suspended_restaurants = db.query(Restaurant).filter(
        Restaurant.is_suspended == True
    ).count()
    
    # User stats
    total_users = db.query(User).filter(User.restaurant_id.isnot(None)).count()
    
    # Product stats
    total_products = db.query(Product).count()
    
    # Order stats
    total_orders = db.query(Order).count()
    total_revenue = db.query(func.sum(Order.total)).scalar() or 0
    
    # Subscription breakdown
    subscriptions_by_plan = db.query(
        Restaurant.subscription_plan,
        func.count(Restaurant.id).label('count')
    ).filter(
        Restaurant.is_active == True
    ).group_by(Restaurant.subscription_plan).all()
    
    # Recent activity (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    new_restaurants_30d = db.query(Restaurant).filter(
        Restaurant.created_at >= thirty_days_ago
    ).count()
    
    new_orders_30d = db.query(Order).filter(
        Order.created_at >= thirty_days_ago
    ).count()
    
    revenue_30d = db.query(func.sum(Order.total)).filter(
        Order.created_at >= thirty_days_ago
    ).scalar() or 0
    
    # Recent restaurants
    recent_restaurants = db.query(Restaurant).order_by(
        desc(Restaurant.created_at)
    ).limit(10).all()
    
    return success_response(
        data={
            "overview": {
                "total_restaurants": total_restaurants,
                "active_restaurants": active_restaurants,
                "suspended_restaurants": suspended_restaurants,
                "total_users": total_users,
                "total_products": total_products,
                "total_orders": total_orders,
                "total_revenue": total_revenue / 100  # Convert cents to dollars
            },
            "subscriptions": {
                plan: count for plan, count in subscriptions_by_plan
            },
            "recent_activity": {
                "new_restaurants_30d": new_restaurants_30d,
                "new_orders_30d": new_orders_30d,
                "revenue_30d": revenue_30d / 100
            },
            "recent_restaurants": [
                {
                    "id": r.id,
                    "name": r.name,
                    "slug": r.slug,
                    "email": r.email,
                    "plan": r.subscription_plan,
                    "status": r.subscription_status,
                    "is_active": r.is_active,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                }
                for r in recent_restaurants
            ]
        },
        message="Platform dashboard data retrieved successfully"
    )


@router.get("/restaurants")
async def list_all_restaurants(
    token_data: dict = Depends(require_platform_admin),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = Query(None, regex="^(active|inactive|suspended|all)$"),
    plan: Optional[str] = Query(None),
    search: Optional[str] = None
):
    """
    List all restaurants with filtering options
    SuperAdmin only
    """
    
    query = db.query(Restaurant)
    
    # Apply filters
    if status == "active":
        query = query.filter(Restaurant.is_active == True, Restaurant.is_suspended == False)
    elif status == "inactive":
        query = query.filter(Restaurant.is_active == False)
    elif status == "suspended":
        query = query.filter(Restaurant.is_suspended == True)
    
    if plan:
        query = query.filter(Restaurant.subscription_plan == plan)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Restaurant.name.like(search_pattern)) |
            (Restaurant.email.like(search_pattern)) |
            (Restaurant.slug.like(search_pattern))
        )
    
    total = query.count()
    restaurants = query.order_by(desc(Restaurant.created_at)).offset(skip).limit(limit).all()
    
    return success_response(
        data={
            "restaurants": [
                {
                    "id": r.id,
                    "name": r.name,
                    "slug": r.slug,
                    "email": r.email,
                    "phone": r.phone,
                    "city": r.city,
                    "country": r.country,
                    "plan": r.subscription_plan,
                    "status": r.subscription_status,
                    "is_active": r.is_active,
                    "is_suspended": r.is_suspended,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "usage": {
                        "users": f"{r.current_users}/{r.max_users}",
                        "products": f"{r.current_products}/{r.max_products}",
                        "orders_this_month": f"{r.current_orders_this_month}/{r.max_orders_per_month}"
                    }
                }
                for r in restaurants
            ],
            "pagination": {
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_more": (skip + limit) < total
            }
        },
        message=f"Retrieved {len(restaurants)} restaurants"
    )


@router.get("/restaurants/{restaurant_id}")
async def get_restaurant_details(
    restaurant_id: str,
    token_data: dict = Depends(require_platform_admin),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific restaurant
    SuperAdmin only
    """
    
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()
    
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    # Get detailed stats
    users_count = db.query(User).filter(User.restaurant_id == restaurant_id).count()
    products_count = db.query(Product).filter(Product.restaurant_id == restaurant_id).count()
    customers_count = db.query(Customer).filter(Customer.restaurant_id == restaurant_id).count()
    orders_count = db.query(Order).filter(Order.restaurant_id == restaurant_id).count()
    
    total_revenue = db.query(func.sum(Order.total)).filter(
        Order.restaurant_id == restaurant_id
    ).scalar() or 0
    
    # Recent orders
    recent_orders = db.query(Order).filter(
        Order.restaurant_id == restaurant_id
    ).order_by(desc(Order.created_at)).limit(10).all()
    
    # Get subscription info
    subscription = db.query(Subscription).filter(
        Subscription.restaurant_id == restaurant_id,
        Subscription.status == 'active'
    ).first()
    
    return success_response(
        data={
            "restaurant": {
                "id": restaurant.id,
                "name": restaurant.name,
                "slug": restaurant.slug,
                "business_name": restaurant.business_name,
                "email": restaurant.email,
                "phone": restaurant.phone,
                "address": restaurant.address,
                "city": restaurant.city,
                "state": restaurant.state,
                "country": restaurant.country,
                "postal_code": restaurant.postal_code,
                "timezone": restaurant.timezone,
                "currency": restaurant.currency,
                "language": restaurant.language,
                "plan": restaurant.subscription_plan,
                "status": restaurant.subscription_status,
                "is_active": restaurant.is_active,
                "is_suspended": restaurant.is_suspended,
                "suspension_reason": restaurant.suspension_reason,
                "created_at": restaurant.created_at.isoformat() if restaurant.created_at else None,
                "last_activity": restaurant.last_activity.isoformat() if restaurant.last_activity else None
            },
            "stats": {
                "users": users_count,
                "products": products_count,
                "customers": customers_count,
                "orders": orders_count,
                "revenue": total_revenue / 100
            },
            "limits": {
                "max_users": restaurant.max_users,
                "max_products": restaurant.max_products,
                "max_orders_per_month": restaurant.max_orders_per_month,
                "current_users": restaurant.current_users,
                "current_products": restaurant.current_products,
                "current_orders_this_month": restaurant.current_orders_this_month
            },
            "subscription": {
                "plan": subscription.plan if subscription else None,
                "status": subscription.status if subscription else None,
                "started_at": subscription.started_at.isoformat() if subscription and subscription.started_at else None,
                "current_period_end": subscription.current_period_end.isoformat() if subscription and subscription.current_period_end else None
            } if subscription else None,
            "recent_orders": [
                {
                    "id": o.id,
                    "order_number": o.order_number,
                    "total": o.total / 100,
                    "status": o.status,
                    "created_at": o.created_at.isoformat() if o.created_at else None
                }
                for o in recent_orders
            ]
        },
        message="Restaurant details retrieved successfully"
    )


@router.put("/restaurants/{restaurant_id}/status")
async def update_restaurant_status(
    restaurant_id: str,
    is_active: bool,
    suspension_reason: Optional[str] = None,
    token_data: dict = Depends(require_platform_admin),
    db: Session = Depends(get_db)
):
    """
    Suspend or activate a restaurant
    SuperAdmin only
    """
    
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()
    
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    restaurant.is_active = is_active
    restaurant.is_suspended = not is_active
    
    if not is_active and suspension_reason:
        restaurant.suspension_reason = suspension_reason
    elif is_active:
        restaurant.suspension_reason = None
    
    db.commit()
    db.refresh(restaurant)
    
    action = "activated" if is_active else "suspended"
    return success_response(
        data={"restaurant_id": restaurant_id, "is_active": is_active},
        message=f"Restaurant {action} successfully"
    )


@router.get("/analytics")
async def platform_analytics(
    token_data: dict = Depends(require_platform_admin),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365)
):
    """
    Platform-wide analytics
    SuperAdmin only
    """
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Revenue by restaurant (top 10)
    revenue_by_restaurant = db.query(
        Restaurant.name,
        Restaurant.id,
        func.sum(Order.total).label('total_revenue')
    ).join(Order, Restaurant.id == Order.restaurant_id).filter(
        Order.created_at >= start_date
    ).group_by(Restaurant.id).order_by(desc('total_revenue')).limit(10).all()
    
    # Orders by status
    orders_by_status = db.query(
        Order.status,
        func.count(Order.id).label('count')
    ).filter(
        Order.created_at >= start_date
    ).group_by(Order.status).all()
    
    # Daily revenue trend
    daily_revenue = db.query(
        func.date(Order.created_at).label('date'),
        func.sum(Order.total).label('revenue')
    ).filter(
        Order.created_at >= start_date
    ).group_by(func.date(Order.created_at)).all()
    
    # Growth metrics
    new_restaurants = db.query(Restaurant).filter(
        Restaurant.created_at >= start_date
    ).count()
    
    new_users = db.query(User).filter(
        User.created_at >= start_date,
        User.restaurant_id.isnot(None)
    ).count()
    
    new_orders = db.query(Order).filter(
        Order.created_at >= start_date
    ).count()
    
    return success_response(
        data={
            "period_days": days,
            "revenue_by_restaurant": [
                {
                    "restaurant_name": name,
                    "restaurant_id": id,
                    "revenue": revenue / 100
                }
                for name, id, revenue in revenue_by_restaurant
            ],
            "orders_by_status": [
                {"status": status, "count": count}
                for status, count in orders_by_status
            ],
            "daily_revenue": [
                {
                    "date": date.isoformat(),
                    "revenue": revenue / 100
                }
                for date, revenue in daily_revenue
            ],
            "growth": {
                "new_restaurants": new_restaurants,
                "new_users": new_users,
                "new_orders": new_orders
            }
        },
        message=f"Analytics for last {days} days retrieved successfully"
    )


@router.get("/subscription-plans")
async def list_subscription_plans(
    token_data: dict = Depends(require_platform_admin),
    db: Session = Depends(get_db)
):
    """
    List all subscription plans
    SuperAdmin only
    """
    
    plans = db.query(SubscriptionPlan).order_by(SubscriptionPlan.sort_order).all()
    
    return success_response(
        data={
            "plans": [
                {
                    "id": p.id,
                    "name": p.name,
                    "display_name": p.display_name,
                    "description": p.description,
                    "price_monthly": p.price_monthly / 100,
                    "price_yearly": p.price_yearly / 100,
                    "max_users": p.max_users,
                    "max_products": p.max_products,
                    "max_orders_per_month": p.max_orders_per_month,
                    "features": p.features,
                    "is_active": p.is_active,
                    "is_featured": p.is_featured,
                    "badge": p.badge
                }
                for p in plans
            ]
        },
        message="Subscription plans retrieved successfully"
    )
