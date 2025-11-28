"""
Order API routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.order import Order, OrderItem, OrderItemModifier, OrderStatusHistory, KOTGroup
from app.models.product import Product
from app.models.customer import Customer
from app.schemas.order import (
    OrderCreate, OrderUpdate, OrderResponse, OrderWithItemsResponse,
    OrderStatusUpdate, PaymentCreate
)
from app.schemas.pagination import PaginationParams
from app.enums import OrderStatus, PaymentStatus, KOTStatus
from app.utils import generate_order_number, calculate_order_total, paginate_query, create_paginated_response
from app.response_formatter import success_response, created_response, list_response, deleted_response, error_response

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])


@router.get("/")
def list_orders(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status: Optional[OrderStatus] = None,
    payment_status: Optional[PaymentStatus] = None,
    order_type: Optional[str] = None,
    customer_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """
    List all orders with pagination and optional filtering
    """
    query = db.query(Order)
    
    if status:
        query = query.filter(Order.status == status)
    
    if payment_status:
        query = query.filter(Order.payment_status == payment_status)
    
    if order_type:
        query = query.filter(Order.order_type == order_type)
    
    if customer_id:
        query = query.filter(Order.customer_id == customer_id)
    
    if start_date:
        query = query.filter(Order.created_at >= start_date)
    
    if end_date:
        query = query.filter(Order.created_at <= end_date)
    
    query = query.order_by(Order.created_at.desc())
    
    # Apply pagination
    pagination = PaginationParams(page=page, page_size=page_size)
    orders, pagination_meta = paginate_query(query, pagination)
    
    return create_paginated_response(orders, pagination_meta, "Orders retrieved successfully")


@router.get("/{order_id}", response_model=OrderWithItemsResponse)
def get_order(order_id: str, db: Session = Depends(get_db)):
    """
    Get a specific order by ID with all items
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
    return order


@router.get("/number/{order_number}", response_model=OrderWithItemsResponse)
def get_order_by_number(order_number: str, db: Session = Depends(get_db)):
    """
    Get a specific order by order number
    """
    order = db.query(Order).filter(Order.order_number == order_number).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with number {order_number} not found"
        )
    return order


@router.post("/", response_model=OrderWithItemsResponse, status_code=status.HTTP_201_CREATED)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    """
    Create a new order
    """
    # Verify customer exists if customer_id provided
    if order.customer_id:
        customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with id {order.customer_id} not found"
            )
    
    # Calculate order totals
    subtotal = 0
    
    for item in order.items:
        # Verify product exists
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {item.product_id} not found"
            )
        
        # Check stock availability
        if product.stock < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product '{product.name}'. Available: {product.stock}"
            )
        
        # Calculate item total
        item_total = item.unit_price * item.quantity
        
        # Add modifiers price
        for modifier in item.modifiers:
            item_total += modifier.price * item.quantity
        
        subtotal += item_total
    
    # Calculate tax and service charge (simplified - should use tax rules)
    tax_total = int(subtotal * 0.10)  # 10% tax
    service_charge = int(subtotal * 0.05)  # 5% service charge
    
    # Calculate discount
    discount = order.discount_code if hasattr(order, 'discount_code') else 0
    
    # Calculate total
    total = subtotal + tax_total + service_charge - discount + order.tip
    
    # Generate order number
    order_number = generate_order_number()
    
    # Create order
    order_data = order.model_dump(exclude={'items'})
    order_data.update({
        'order_number': order_number,
        'subtotal': subtotal,
        'tax_total': tax_total,
        'service_charge': service_charge,
        'discount': discount,
        'total': total,
        'status': OrderStatus.CONFIRMED,
        'payment_status': PaymentStatus.PENDING
    })
    
    db_order = Order(**order_data)
    db.add(db_order)
    db.flush()  # Get order ID
    
    # Create order items
    for item_data in order.items:
        item_dict = item_data.model_dump(exclude={'modifiers'})
        item_dict['order_id'] = db_order.id
        
        # Calculate item total price
        item_total = item_data.unit_price * item_data.quantity
        for mod in item_data.modifiers:
            item_total += mod.price * item_data.quantity
        item_dict['total_price'] = item_total
        
        # Get product department
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        item_dict['department'] = product.department
        item_dict['printer_tag'] = product.printer_tag
        
        db_item = OrderItem(**item_dict)
        db.add(db_item)
        db.flush()
        
        # Create order item modifiers
        for modifier_data in item_data.modifiers:
            modifier_dict = modifier_data.model_dump()
            modifier_dict['order_item_id'] = db_item.id
            db_modifier = OrderItemModifier(**modifier_dict)
            db.add(db_modifier)
        
        # Reduce product stock
        product.stock -= item_data.quantity
    
    # Add order status history
    status_history = OrderStatusHistory(
        order_id=db_order.id,
        status=OrderStatus.CONFIRMED.value,
        notes="Order created"
    )
    db.add(status_history)
    
    # Update customer stats if customer exists
    if order.customer_id:
        customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
        if customer:
            customer.total_spent += total
            customer.visit_count += 1
            customer.last_visit = datetime.now()
    
    db.commit()
    db.refresh(db_order)
    return db_order


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: str,
    order: OrderUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing order
    """
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
    
    # Update only provided fields
    update_data = order.model_dump(exclude_unset=True)
    
    # Add status history if status changed
    if 'status' in update_data and update_data['status'] != db_order.status:
        status_history = OrderStatusHistory(
            order_id=order_id,
            status=update_data['status'].value,
            notes=update_data.get('notes', 'Status updated')
        )
        db.add(status_history)
        
        # Update timestamps based on status
        if update_data['status'] == OrderStatus.CONFIRMED:
            db_order.accepted_at = datetime.now()
        elif update_data['status'] == OrderStatus.PREPARING:
            db_order.preparing_at = datetime.now()
        elif update_data['status'] == OrderStatus.READY:
            db_order.ready_at = datetime.now()
        elif update_data['status'] == OrderStatus.COMPLETED:
            db_order.completed_at = datetime.now()
        elif update_data['status'] == OrderStatus.CANCELLED:
            db_order.cancelled_at = datetime.now()
    
    for field, value in update_data.items():
        setattr(db_order, field, value)
    
    db.commit()
    db.refresh(db_order)
    return db_order


@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: str,
    status_update: OrderStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Update order status
    """
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
    
    db_order.status = status_update.status
    
    # Add status history
    status_history = OrderStatusHistory(
        order_id=order_id,
        status=status_update.status.value,
        notes=status_update.notes
    )
    db.add(status_history)
    
    # Update timestamps
    if status_update.status == OrderStatus.CONFIRMED:
        db_order.accepted_at = datetime.now()
    elif status_update.status == OrderStatus.PREPARING:
        db_order.preparing_at = datetime.now()
    elif status_update.status == OrderStatus.READY:
        db_order.ready_at = datetime.now()
    elif status_update.status == OrderStatus.COMPLETED:
        db_order.completed_at = datetime.now()
    elif status_update.status == OrderStatus.CANCELLED:
        db_order.cancelled_at = datetime.now()
    
    db.commit()
    db.refresh(db_order)
    return db_order


@router.post("/{order_id}/payment", response_model=OrderResponse)
def process_payment(
    order_id: str,
    payment: PaymentCreate,
    db: Session = Depends(get_db)
):
    """
    Process payment for an order
    """
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
    
    if db_order.payment_status == PaymentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order payment already completed"
        )
    
    # Verify payment amount
    if payment.amount != db_order.total:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment amount {payment.amount} does not match order total {db_order.total}"
        )
    
    db_order.payment_method = payment.payment_method
    db_order.transaction_id = payment.transaction_id
    db_order.payment_status = PaymentStatus.COMPLETED
    
    # Update order status if still pending
    if db_order.status == OrderStatus.CONFIRMED:
        db_order.status = OrderStatus.PREPARING
        db_order.preparing_at = datetime.now()
    
    db.commit()
    db.refresh(db_order)
    return db_order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_order(order_id: str, reason: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Cancel an order
    """
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
    
    if db_order.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order with status {db_order.status}"
        )
    
    db_order.status = OrderStatus.CANCELLED
    db_order.cancelled_at = datetime.now()
    db_order.notes = reason if reason else "Order cancelled"
    
    # Add status history
    status_history = OrderStatusHistory(
        order_id=order_id,
        status=OrderStatus.CANCELLED.value,
        notes=reason or "Order cancelled"
    )
    db.add(status_history)
    
    # Restore product stock
    for item in db_order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.stock += item.quantity
    
    db.commit()
    return None


@router.put("/{order_id}/kot/{department}/status")
def update_kot_status(
    order_id: str,
    department: str,
    kot_status: KOTStatus,
    db: Session = Depends(get_db)
):
    """
    Update KOT status for a specific department
    """
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
    
    # Find or create KOT group for this department
    kot_group = db.query(KOTGroup).filter(
        KOTGroup.order_id == order_id,
        KOTGroup.department == department
    ).first()
    
    if not kot_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No KOT found for department {department} in this order"
        )
    
    kot_group.status = kot_status.value
    kot_group.updated_at = datetime.now()
    
    db.commit()
    db.refresh(kot_group)
    
    return {
        "message": f"KOT status updated to {kot_status.value} for department {department}",
        "kot_group": {
            "id": kot_group.id,
            "department": kot_group.department,
            "status": kot_group.status,
            "kot_number": kot_group.kot_number
        }
    }


@router.post("/{order_id}/print-kot")
def print_kot(
    order_id: str,
    department: Optional[str] = None,
    printer: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Print KOT for kitchen/bar
    """
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
    
    # Get items to print
    query = db.query(OrderItem).filter(OrderItem.order_id == order_id)
    if department:
        query = query.filter(OrderItem.department == department)
    
    items = query.all()
    
    if not items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No items found for department {department}" if department else "No items found in order"
        )
    
    # Group items by department if not specified
    departments_printed = set()
    for item in items:
        dept = item.department
        departments_printed.add(dept)
        
        # Find or create KOT group
        kot_group = db.query(KOTGroup).filter(
            KOTGroup.order_id == order_id,
            KOTGroup.department == dept
        ).first()
        
        if not kot_group:
            # Generate KOT number
            kot_count = db.query(KOTGroup).filter(KOTGroup.department == dept).count()
            kot_number = f"KOT-{dept[:3].upper()}-{kot_count + 1:04d}"
            
            kot_group = KOTGroup(
                order_id=order_id,
                department=dept,
                kot_number=kot_number,
                status=KOTStatus.PENDING.value,
                printer_tag=item.printer_tag or "default"
            )
            db.add(kot_group)
    
    db.commit()
    
    return {
        "message": "KOT printed successfully",
        "order_id": order_id,
        "order_number": db_order.order_number,
        "departments": list(departments_printed),
        "printer": printer or "default",
        "items_count": len(items),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/{order_id}/track")
def track_order(order_id: str, db: Session = Depends(get_db)):
    """
    Get order tracking information (public endpoint - no auth required)
    """
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order not found"
        )
    
    # Get status history
    status_history = db.query(OrderStatusHistory).filter(
        OrderStatusHistory.order_id == order_id
    ).order_by(OrderStatusHistory.created_at.asc()).all()
    
    # Get KOT groups
    kot_groups = db.query(KOTGroup).filter(
        KOTGroup.order_id == order_id
    ).all()
    
    return {
        "order_number": db_order.order_number,
        "status": db_order.status.value,
        "order_type": db_order.order_type,
        "created_at": db_order.created_at,
        "confirmed_at": db_order.accepted_at,
        "preparing_at": db_order.preparing_at,
        "ready_at": db_order.ready_at,
        "completed_at": db_order.completed_at,
        "estimated_time": db_order.estimated_time,
        "status_history": [
            {
                "status": h.status,
                "notes": h.notes,
                "timestamp": h.created_at
            }
            for h in status_history
        ],
        "kot_status": [
            {
                "department": k.department,
                "kot_number": k.kot_number,
                "status": k.status,
                "updated_at": k.updated_at
            }
            for k in kot_groups
        ]
    }
