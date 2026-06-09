from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.core.query_datetime import (
    QueryDateInput,
    to_query_end_datetime,
    to_query_start_datetime,
)
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.response import success_response, error_response
from app.modules.order.schema import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    OrderItemCreate,
    OrderItemUpdate,
    OrderItemResponse,
    OrderStatusUpdate,
    OrderPaymentUpdate,
    OrderCancelRequest,
    OrderAddItems,
    OrderStatistics
)
from app.modules.order.model import PaymentMethod
from app.modules.payment.service import OrderPaymentService
from app.modules.order.model import OrderType, OrderStatus, PaymentStatus
from app.modules.order.service import OrderService
from app.modules.order.websocket import order_ws_manager
from app.modules.user.model import User


router = APIRouter(prefix="/orders", tags=["orders"])


@router.websocket("/ws/{restaurant_id}")
async def websocket_orders(websocket: WebSocket, restaurant_id: str):
    """
    WebSocket endpoint for real-time order updates scoped by restaurant.

    Example:
        const ws = new WebSocket('ws://localhost:8000/api/v1/orders/ws/<restaurant_id>');
    """
    await order_ws_manager.connect(websocket, restaurant_id)
    try:
        while True:
            data = await websocket.receive_json()
            if isinstance(data, dict) and data.get("type") == "ping":
                await websocket.send_json(
                    {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
    except WebSocketDisconnect:
        order_ws_manager.disconnect(websocket, restaurant_id)
    except Exception:
        order_ws_manager.disconnect(websocket, restaurant_id)


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new order with items
    
    - **restaurant_id**: Restaurant ID (required)
    - **order_type**: Type of order (dine_in, takeaway, delivery, etc.)
    - **items**: List of order items (required, min 1)
    - **customer_id**: Registered customer ID
    - **table_id**: Table ID (for dine-in orders)
    - **guest_name/phone/email**: Guest information for non-registered customers
    - **delivery_address**: Delivery address (for delivery orders)
    - **special_instructions**: Special requests for the order
    - **scheduled_for**: Schedule order for future time
    """
    try:
        from app.modules.restaurant.enforcement import SubscriptionEnforcementService
        from app.modules.restaurant.service import RestaurantService

        await SubscriptionEnforcementService.assert_within_limit(
            db, order_data.restaurant_id, "orders"
        )
        order = await OrderService.create_order(db, order_data, created_by=current_user.id)
        await RestaurantService.increment_usage(db, order_data.restaurant_id, "orders")
        
        # Load items for response
        items = await OrderService.get_order_items(db, order.id)
        order_response = OrderResponse.model_validate(order)
        order_response.items = [OrderItemResponse.model_validate(item) for item in items]

        # Best-effort WebSocket notification (do not affect response on failure)
        try:
            await order_ws_manager.broadcast(
                order_data.restaurant_id,
                {
                    "type": "order_created",
                    "restaurant_id": order_data.restaurant_id,
                    "order_id": str(order.id),
                    "order": order_response.model_dump(),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
        except Exception:
            pass

        try:
            from app.modules.kds.service import KDSService

            await KDSService.route_order_to_stations(
                db, str(order.id), current_user.id
            )
        except Exception:
            pass
        
        return success_response(
            data=order_response,
            message="Order created successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        return error_response(
            message="Failed to create order",
            error_code="ORDER_CREATE_ERROR",
            error_details=str(e)
        )


@router.get("/{order_id}", response_model=dict)
async def get_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get order by ID with items"""
    order = await OrderService.get_order_by_id(db, order_id, include_items=True)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Items are already loaded via selectinload
    order_response = OrderResponse.model_validate(order)
    
    return success_response(
        data=order_response,
        message="Order retrieved successfully"
    )


@router.get("/number/{order_number}", response_model=dict)
async def get_order_by_number(
    order_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get order by order number"""
    order = await OrderService.get_order_by_number(db, order_number)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Load items
    items = await OrderService.get_order_items(db, order.id)
    order_response = OrderResponse.model_validate(order)
    order_response.items = [OrderItemResponse.model_validate(item) for item in items]
    
    return success_response(
        data=order_response,
        message="Order retrieved successfully"
    )


@router.get("/restaurant/{restaurant_id}", response_model=dict)
async def get_restaurant_orders(
    restaurant_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    order_type: Optional[OrderType] = Query(None, description="Filter by order type"),
    status: Optional[OrderStatus] = Query(None, description="Filter by status"),
    payment_status: Optional[PaymentStatus] = Query(None, description="Filter by payment status"),
    customer_id: Optional[str] = Query(None, description="Filter by customer"),
    table_id: Optional[str] = Query(None, description="Filter by table"),
    start_date: QueryDateInput = Query(None, description="Filter from date (YYYY-MM-DD or ISO datetime)"),
    end_date: QueryDateInput = Query(None, description="Filter to date (YYYY-MM-DD or ISO datetime)"),
    search: Optional[str] = Query(None, description="Search by order number, guest name, or phone"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get paginated list of orders for a restaurant with filtering
    
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return (max 100)
    - **order_type**: Filter by order type
    - **status**: Filter by order status
    - **payment_status**: Filter by payment status
    - **customer_id**: Filter by customer
    - **table_id**: Filter by table
    - **start_date/end_date**: Filter by date range
    - **search**: Search by order number, guest name, or phone
    """
    orders, total = await OrderService.get_orders(
        db,
        restaurant_id=restaurant_id,
        skip=skip,
        limit=limit,
        order_type=order_type,
        status=status,
        payment_status=payment_status,
        customer_id=customer_id,
        table_id=table_id,
        start_date=to_query_start_datetime(start_date),
        end_date=to_query_end_datetime(end_date),
        search=search
    )
    
    # Load items for each order
    orders_with_items = []
    for order in orders:
        items = await OrderService.get_order_items(db, order.id)
        order_response = OrderResponse.model_validate(order)
        order_response.items = [OrderItemResponse.model_validate(item) for item in items]
        orders_with_items.append(order_response)
    
    return success_response(
        data={
            "total": total,
            "skip": skip,
            "limit": limit,
            "orders": orders_with_items
        },
        message="Orders retrieved successfully"
    )


@router.get("/restaurant/{restaurant_id}/statistics", response_model=dict)
async def get_order_statistics(
    restaurant_id: str,
    start_date: QueryDateInput = Query(None, description="Filter from date (YYYY-MM-DD or ISO datetime)"),
    end_date: QueryDateInput = Query(None, description="Filter to date (YYYY-MM-DD or ISO datetime)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get order statistics for a restaurant
    
    Returns counts by status, total revenue, and average order value
    """
    stats = await OrderService.get_order_statistics(
        db,
        restaurant_id=restaurant_id,
        start_date=to_query_start_datetime(start_date),
        end_date=to_query_end_datetime(end_date)
    )
    
    return success_response(
        data=stats,
        message="Order statistics retrieved successfully"
    )


@router.put("/{order_id}", response_model=dict)
async def update_order(
    order_id: str,
    order_data: OrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update order information"""
    order = await OrderService.update_order(db, order_id, order_data)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Load items
    items = await OrderService.get_order_items(db, order_id)
    order_response = OrderResponse.model_validate(order)
    order_response.items = [OrderItemResponse.model_validate(item) for item in items]

    try:
        await order_ws_manager.broadcast(
            str(order.restaurant_id),
            {
                "type": "order_updated",
                "restaurant_id": str(order.restaurant_id),
                "order_id": str(order.id),
                "order": order_response.model_dump(),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    except Exception:
        pass
    
    return success_response(
        data=order_response,
        message="Order updated successfully"
    )


@router.patch("/{order_id}/status", response_model=dict)
async def update_order_status(
    order_id: str,
    status_data: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update order status only
    
    - **status**: New order status
    """
    order = await OrderService.update_order(
        db,
        order_id,
        OrderUpdate(status=status_data.status)
    )
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Reload order with items using selectinload
    order = await OrderService.get_order_by_id(db, order_id, include_items=True)
    order_response = OrderResponse.model_validate(order)

    try:
        await order_ws_manager.broadcast(
            str(order.restaurant_id),
            {
                "type": "order_status_updated",
                "restaurant_id": str(order.restaurant_id),
                "order_id": str(order.id),
                "status": status_data.status.value,
                "order": order_response.model_dump(),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    except Exception:
        pass
    
    return success_response(
        data=order_response,
        message=f"Order status updated to {status_data.status.value}"
    )


@router.patch("/{order_id}/payment", response_model=dict)
async def update_order_payment(
    order_id: str,
    payment_data: OrderPaymentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update order payment information
    
    - **payment_method**: Payment method used
    - **payment_status**: Payment status
    - **paid_amount**: Amount paid
    - **payment_details**: Additional payment details (transaction ID, etc.)
    """
    existing = await OrderService.get_order_by_id(db, order_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    paid_amount = payment_data.paid_amount
    if paid_amount is None and payment_data.payment_status == PaymentStatus.PAID:
        paid_amount = existing.total_amount

    payment_method = payment_data.payment_method or PaymentMethod.CASH

    order = await OrderService.update_order(
        db,
        order_id,
        OrderUpdate(
            payment_method=payment_method,
            payment_status=payment_data.payment_status,
            paid_amount=paid_amount if paid_amount is not None else existing.paid_amount,
        )
    )
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Update payment details if provided
    if payment_data.payment_details:
        order.payment_details = payment_data.payment_details
        db.add(order)

    if payment_data.payment_status == PaymentStatus.PAID:
        await OrderPaymentService.mark_order_payments_paid(
            db,
            order_id,
            payment_method=payment_method.value if payment_method else None,
            paid_amount=paid_amount,
        )
        is_pos_source = (
            (existing.source or "").lower() == "pos"
            or getattr(existing, "is_pos_order", False)
            or (not existing.source and bool(existing.created_by))
        )
        if is_pos_source and order.status != OrderStatus.COMPLETED.value:
            order.status = OrderStatus.COMPLETED.value
            if not order.completed_at:
                order.completed_at = datetime.utcnow()
            db.add(order)

    await db.commit()
    await db.refresh(order)
    
    # Load items
    items = await OrderService.get_order_items(db, order_id)
    order_response = OrderResponse.model_validate(order)
    order_response.items = [OrderItemResponse.model_validate(item) for item in items]
    
    return success_response(
        data=order_response,
        message="Payment information updated successfully"
    )


@router.post("/{order_id}/items", response_model=dict)
async def add_items_to_order(
    order_id: str,
    items_data: OrderAddItems,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add items to an existing order
    
    - **items**: List of items to add
    """
    order = await OrderService.add_items_to_order(db, order_id, items_data.items)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Load all items
    items = await OrderService.get_order_items(db, order_id)
    order_response = OrderResponse.model_validate(order)
    order_response.items = [OrderItemResponse.model_validate(item) for item in items]
    
    return success_response(
        data=order_response,
        message="Items added to order successfully"
    )


@router.put("/items/{item_id}", response_model=dict)
async def update_order_item(
    item_id: str,
    item_data: OrderItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an order item"""
    item = await OrderService.update_order_item(db, item_id, item_data)
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order item not found"
        )
    
    return success_response(
        data=OrderItemResponse.model_validate(item),
        message="Order item updated successfully"
    )


@router.delete("/items/{item_id}", response_model=dict)
async def delete_order_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an order item"""
    success = await OrderService.delete_order_item(db, item_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order item not found"
        )
    
    return success_response(
        data={"id": item_id},
        message="Order item deleted successfully"
    )


@router.post("/{order_id}/cancel", response_model=dict)
async def cancel_order(
    order_id: str,
    reason: Optional[str] = Query(None, description="Cancellation reason"),
    body: Optional[OrderCancelRequest] = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel an order
    
    - **order_id**: Order ID
    - **reason**: Optional cancellation reason (query param or JSON body)
    """
    cancel_reason = reason or (body.reason if body else None)
    order = await OrderService.cancel_order(db, order_id, cancel_reason)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Load items
    items = await OrderService.get_order_items(db, order_id)
    order_response = OrderResponse.model_validate(order)
    order_response.items = [OrderItemResponse.model_validate(item) for item in items]
    
    return success_response(
        data=order_response,
        message="Order cancelled successfully"
    )
