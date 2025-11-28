"""
Analytics and Reports API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.customer import Customer
from app.models.user import StaffPerformance, User
from app.response_formatter import success_response, created_response, list_response, deleted_response, error_response


analytics_router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])
reports_router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


# Analytics endpoints
@analytics_router.get("/dashboard")
def get_dashboard_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get dashboard analytics overview
    """
    # Default to last 30 days if no dates provided
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    # Total orders
    total_orders = db.query(func.count(Order.id)).filter(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= end_date
        )
    ).scalar()
    
    # Total revenue
    total_revenue = db.query(func.sum(Order.total)).filter(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status == 'completed'
        )
    ).scalar() or 0
    
    # Average order value
    avg_order_value = int(total_revenue / total_orders) if total_orders > 0 else 0
    
    # Total customers
    total_customers = db.query(func.count(Customer.id)).scalar()
    
    # Orders by status
    orders_by_status = db.query(
        Order.status,
        func.count(Order.id).label('count')
    ).filter(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= end_date
        )
    ).group_by(Order.status).all()
    
    # Orders by type
    orders_by_type = db.query(
        Order.order_type,
        func.count(Order.id).label('count'),
        func.sum(Order.total).label('revenue')
    ).filter(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status == 'completed'
        )
    ).group_by(Order.order_type).all()
    
    return {
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "overview": {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "avg_order_value": avg_order_value,
            "total_customers": total_customers
        },
        "orders_by_status": [
            {
                "status": status,
                "count": count
            }
            for status, count in orders_by_status
        ],
        "orders_by_type": [
            {
                "order_type": order_type,
                "count": count,
                "revenue": revenue or 0
            }
            for order_type, count, revenue in orders_by_type
        ]
    }


@analytics_router.get("/sales")
def get_sales_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    group_by: str = Query("day", regex="^(hour|day|week|month)$"),
    db: Session = Depends(get_db)
):
    """
    Get sales analytics with time-based grouping
    """
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    # Get completed orders
    orders = db.query(Order).filter(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status == 'completed'
        )
    ).all()
    
    # Group by time period
    sales_by_period = {}
    for order in orders:
        if group_by == "hour":
            period_key = order.created_at.strftime("%Y-%m-%d %H:00")
        elif group_by == "day":
            period_key = order.created_at.strftime("%Y-%m-%d")
        elif group_by == "week":
            period_key = order.created_at.strftime("%Y-W%W")
        else:  # month
            period_key = order.created_at.strftime("%Y-%m")
        
        if period_key not in sales_by_period:
            sales_by_period[period_key] = {
                "period": period_key,
                "orders": 0,
                "revenue": 0,
                "items_sold": 0
            }
        
        sales_by_period[period_key]["orders"] += 1
        sales_by_period[period_key]["revenue"] += order.total
        sales_by_period[period_key]["items_sold"] += len(order.items)
    
    return {
        "period": {
            "start_date": start_date,
            "end_date": end_date,
            "group_by": group_by
        },
        "sales_data": sorted(sales_by_period.values(), key=lambda x: x["period"])
    }


@analytics_router.get("/products")
def get_product_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get product performance analytics
    """
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    # Get product sales data
    product_sales = db.query(
        OrderItem.product_id,
        Product.name,
        Product.category_id,
        func.sum(OrderItem.quantity).label('total_quantity'),
        func.sum(OrderItem.total_price).label('total_revenue'),
        func.count(OrderItem.id).label('order_count')
    ).join(
        Order, OrderItem.order_id == Order.id
    ).join(
        Product, OrderItem.product_id == Product.id
    ).filter(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status == 'completed'
        )
    ).group_by(
        OrderItem.product_id,
        Product.name,
        Product.category_id
    ).order_by(
        func.sum(OrderItem.total_price).desc()
    ).limit(limit).all()
    
    return {
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "top_products": [
            {
                "product_id": product_id,
                "product_name": name,
                "category_id": category_id,
                "quantity_sold": int(total_quantity),
                "total_revenue": int(total_revenue),
                "order_count": int(order_count),
                "avg_price": int(total_revenue / total_quantity) if total_quantity > 0 else 0
            }
            for product_id, name, category_id, total_quantity, total_revenue, order_count in product_sales
        ]
    }


@analytics_router.get("/orders")
def get_order_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get order statistics
    """
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    # Total orders
    total_orders = db.query(func.count(Order.id)).filter(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= end_date
        )
    ).scalar()
    
    # Completed orders
    completed_orders = db.query(func.count(Order.id)).filter(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status == 'completed'
        )
    ).scalar()
    
    # Cancelled orders
    cancelled_orders = db.query(func.count(Order.id)).filter(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status == 'cancelled'
        )
    ).scalar()
    
    # Average items per order
    avg_items = db.query(
        func.avg(func.count(OrderItem.id))
    ).join(
        Order, OrderItem.order_id == Order.id
    ).filter(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= end_date
        )
    ).group_by(Order.id).scalar() or 0
    
    # Order completion rate
    completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
    
    # Orders by payment method
    orders_by_payment = db.query(
        Order.payment_method,
        func.count(Order.id).label('count'),
        func.sum(Order.total).label('revenue')
    ).filter(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status == 'completed'
        )
    ).group_by(Order.payment_method).all()
    
    return {
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "overview": {
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "cancelled_orders": cancelled_orders,
            "completion_rate": round(completion_rate, 2),
            "avg_items_per_order": round(float(avg_items), 2)
        },
        "by_payment_method": [
            {
                "payment_method": payment_method,
                "order_count": count,
                "revenue": revenue or 0
            }
            for payment_method, count, revenue in orders_by_payment
        ]
    }


@analytics_router.get("/staff")
def get_staff_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get staff performance analytics
    """
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    # Get staff performance data
    staff_performance = db.query(
        User.id,
        User.name,
        User.role,
        func.count(Order.id).label('orders_handled'),
        func.sum(Order.total).label('total_revenue'),
        func.avg(Order.total).label('avg_order_value')
    ).join(
        Order, User.id == Order.created_by
    ).filter(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status == 'completed'
        )
    ).group_by(
        User.id,
        User.name,
        User.role
    ).order_by(
        func.sum(Order.total).desc()
    ).all()
    
    return {
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "staff_performance": [
            {
                "user_id": user_id,
                "staff_name": name,
                "role": role,
                "orders_handled": int(orders_handled),
                "total_revenue": int(total_revenue or 0),
                "avg_order_value": int(avg_order_value or 0)
            }
            for user_id, name, role, orders_handled, total_revenue, avg_order_value in staff_performance
        ]
    }


@analytics_router.get("/payments")
def get_payment_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    Get payment statistics
    """
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    # Total revenue
    total_revenue = db.query(func.sum(Order.total)).filter(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status == 'completed'
        )
    ).scalar() or 0
    
    # By payment method
    by_payment_method = db.query(
        Order.payment_method,
        func.count(Order.id).label('count'),
        func.sum(Order.total).label('revenue')
    ).filter(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status == 'completed'
        )
    ).group_by(Order.payment_method).all()
    
    # By payment status
    by_payment_status = db.query(
        Order.payment_status,
        func.count(Order.id).label('count'),
        func.sum(Order.total).label('amount')
    ).filter(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= end_date
        )
    ).group_by(Order.payment_status).all()
    
    # Tax and charges breakdown
    total_subtotal = db.query(func.sum(Order.subtotal)).filter(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status == 'completed'
        )
    ).scalar() or 0
    
    total_tax = db.query(func.sum(Order.tax_total)).filter(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status == 'completed'
        )
    ).scalar() or 0
    
    total_service_charge = db.query(func.sum(Order.service_charge)).filter(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status == 'completed'
        )
    ).scalar() or 0
    
    total_tips = db.query(func.sum(Order.tip)).filter(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status == 'completed'
        )
    ).scalar() or 0
    
    return {
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "overview": {
            "total_revenue": total_revenue,
            "total_subtotal": total_subtotal,
            "total_tax": total_tax,
            "total_service_charge": total_service_charge,
            "total_tips": total_tips
        },
        "by_payment_method": [
            {
                "payment_method": method,
                "transaction_count": count,
                "revenue": revenue or 0,
                "percentage": round((revenue or 0) / total_revenue * 100, 2) if total_revenue > 0 else 0
            }
            for method, count, revenue in by_payment_method
        ],
        "by_payment_status": [
            {
                "status": status,
                "count": count,
                "amount": amount or 0
            }
            for status, count, amount in by_payment_status
        ]
    }


# Reports endpoints
@reports_router.get("/sales")
def generate_sales_report(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    format: str = Query("json", regex="^(json|csv|pdf)$"),
    db: Session = Depends(get_db)
):
    """
    Generate sales report (exportable in JSON, CSV, PDF)
    """
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    # Get sales data
    orders = db.query(Order).filter(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status == 'completed'
        )
    ).all()
    
    total_sales = sum(order.total for order in orders)
    total_orders = len(orders)
    avg_order_value = int(total_sales / total_orders) if total_orders > 0 else 0
    
    # For now, return JSON format
    # TODO: Implement CSV and PDF export
    report_data = {
        "report_type": "sales",
        "generated_at": datetime.utcnow(),
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "summary": {
            "total_sales": total_sales,
            "total_orders": total_orders,
            "avg_order_value": avg_order_value
        },
        "orders": [
            {
                "order_number": order.order_number,
                "date": order.created_at,
                "order_type": order.order_type,
                "subtotal": order.subtotal,
                "tax": order.tax_total,
                "service_charge": order.service_charge,
                "total": order.total,
                "payment_method": order.payment_method
            }
            for order in orders
        ]
    }
    
    if format == "json":
        return report_data
    else:
        # Placeholder for CSV/PDF export
        raise HTTPException(
            status_code=501,
            detail=f"{format.upper()} export not implemented yet"
        )


@reports_router.get("/inventory")
def generate_inventory_report(
    low_stock_only: bool = Query(False),
    format: str = Query("json", regex="^(json|csv|pdf)$"),
    db: Session = Depends(get_db)
):
    """
    Generate inventory report
    """
    query = db.query(Product)
    
    if low_stock_only:
        # Products where stock is less than or equal to low_stock_threshold
        query = query.filter(Product.stock <= Product.low_stock_threshold)
    
    products = query.all()
    
    report_data = {
        "report_type": "inventory",
        "generated_at": datetime.utcnow(),
        "filters": {
            "low_stock_only": low_stock_only
        },
        "summary": {
            "total_products": len(products),
            "low_stock_items": sum(1 for p in products if p.stock <= p.low_stock_threshold)
        },
        "products": [
            {
                "product_id": product.id,
                "name": product.name,
                "sku": product.sku,
                "category_id": product.category_id,
                "current_stock": product.stock,
                "low_stock_threshold": product.low_stock_threshold,
                "unit": product.unit,
                "price": product.price,
                "is_available": product.is_available,
                "status": "low_stock" if product.stock <= product.low_stock_threshold else "in_stock"
            }
            for product in products
        ]
    }
    
    if format == "json":
        return report_data
    else:
        raise HTTPException(
            status_code=501,
            detail=f"{format.upper()} export not implemented yet"
        )


@reports_router.get("/taxes")
def generate_tax_report(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    format: str = Query("json", regex="^(json|csv|pdf)$"),
    db: Session = Depends(get_db)
):
    """
    Generate tax report
    """
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    # Get completed orders
    orders = db.query(Order).filter(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status == 'completed'
        )
    ).all()
    
    total_tax_collected = sum(order.tax_total for order in orders)
    total_service_charge = sum(order.service_charge for order in orders)
    total_subtotal = sum(order.subtotal for order in orders)
    total_revenue = sum(order.total for order in orders)
    
    report_data = {
        "report_type": "taxes",
        "generated_at": datetime.utcnow(),
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "summary": {
            "total_orders": len(orders),
            "total_subtotal": total_subtotal,
            "total_tax_collected": total_tax_collected,
            "total_service_charge": total_service_charge,
            "total_revenue": total_revenue
        },
        "orders": [
            {
                "order_number": order.order_number,
                "date": order.created_at,
                "order_type": order.order_type,
                "subtotal": order.subtotal,
                "tax": order.tax_total,
                "service_charge": order.service_charge,
                "total": order.total
            }
            for order in orders
        ]
    }
    
    if format == "json":
        return report_data
    else:
        raise HTTPException(
            status_code=501,
            detail=f"{format.upper()} export not implemented yet"
        )
