from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime, timedelta
from app.modules.order.model import Order, OrderItem, OrderType, OrderStatus, PaymentStatus
from app.modules.order.schema import OrderCreate, OrderUpdate, OrderItemCreate, OrderItemUpdate
import random
import string


class OrderService:
    """Service layer for order operations"""
    
    @staticmethod
    def generate_order_number() -> str:
        """Generate unique order number"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = ''.join(random.choices(string.digits, k=4))
        return f"ORD-{timestamp}-{random_suffix}"
    
    @staticmethod
    def calculate_item_total(item: OrderItemCreate) -> int:
        """Calculate total price for an order item"""
        base_price = item.unit_price + item.modifiers_price
        subtotal = base_price * item.quantity
        total = subtotal - item.discount_amount + item.tax_amount
        return max(0, total)
    
    @staticmethod
    def calculate_order_totals(items: List[OrderItem], discount_amount: int = 0, 
                              delivery_fee: int = 0, service_charge: int = 0, 
                              tip_amount: int = 0) -> dict:
        """Calculate order totals"""
        subtotal = sum(item.total_price for item in items)
        tax_total = sum(item.tax_amount for item in items)
        total = subtotal - discount_amount + delivery_fee + service_charge + tip_amount
        
        return {
            "subtotal": subtotal,
            "tax_amount": tax_total,
            "discount_amount": discount_amount,
            "delivery_fee": delivery_fee,
            "service_charge": service_charge,
            "tip_amount": tip_amount,
            "total_amount": max(0, total)
        }
    
    @staticmethod
    async def create_order(db: AsyncSession, order_data: OrderCreate, created_by: Optional[str] = None) -> Order:
        """
        Create a new order with items
        
        Args:
            db: Database session
            order_data: Order creation data
            created_by: User ID who created the order
            
        Returns:
            Created order with items
        """
        # Generate order number
        order_number = OrderService.generate_order_number()
        
        # Create order
        db_order = Order(
            restaurant_id=order_data.restaurant_id,
            order_number=order_number,
            order_type=order_data.order_type,
            customer_id=order_data.customer_id,
            table_id=order_data.table_id,
            created_by=created_by,
            guest_name=order_data.guest_name,
            guest_phone=order_data.guest_phone,
            guest_email=order_data.guest_email,
            delivery_address=order_data.delivery_address,
            delivery_latitude=order_data.delivery_latitude,
            delivery_longitude=order_data.delivery_longitude,
            delivery_instructions=order_data.delivery_instructions,
            scheduled_for=order_data.scheduled_for,
            guest_count=order_data.guest_count,
            special_instructions=order_data.special_instructions,
            kitchen_notes=order_data.kitchen_notes,
            staff_notes=order_data.staff_notes,
            discount_code=order_data.discount_code,
            discount_type=order_data.discount_type,
            source=order_data.source,
            source_details=order_data.source_details,
            is_priority=order_data.is_priority,
            requires_cutlery=order_data.requires_cutlery,
            status=OrderStatus.PENDING
        )
        
        db.add(db_order)
        await db.flush()  # Get order ID
        
        # Create order items
        order_items = []
        for item_data in order_data.items:
            total_price = OrderService.calculate_item_total(item_data)
            
            db_item = OrderItem(
                order_id=db_order.id,
                product_id=item_data.product_id,
                product_name=item_data.product_name,
                product_image=item_data.product_image,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                modifiers=item_data.modifiers,
                customization=item_data.customization,
                modifiers_price=item_data.modifiers_price,
                discount_amount=item_data.discount_amount,
                tax_amount=item_data.tax_amount,
                total_price=total_price,
                department=item_data.department,
                printer_tag=item_data.printer_tag,
                is_complimentary=item_data.is_complimentary,
                notes=item_data.notes,
                status="pending"
            )
            order_items.append(db_item)
            db.add(db_item)
        
        # Calculate and update order totals
        totals = OrderService.calculate_order_totals(order_items)
        db_order.subtotal = totals["subtotal"]
        db_order.tax_amount = totals["tax_amount"]
        db_order.total_amount = totals["total_amount"]
        
        await db.commit()
        await db.refresh(db_order)
        
        # Load items relationship
        result = await db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == db_order.id)
        )
        return result.scalar_one()
    
    @staticmethod
    async def get_order_by_id(db: AsyncSession, order_id: str, include_items: bool = True) -> Optional[Order]:
        """Get order by ID with optional items"""
        query = select(Order).where(Order.id == order_id)
        
        if include_items:
            query = query.options(selectinload(Order.items))
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_order_items(db: AsyncSession, order_id: str) -> List[OrderItem]:
        """Get all items for an order"""
        result = await db.execute(
            select(OrderItem).where(OrderItem.order_id == order_id)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_order_by_number(db: AsyncSession, order_number: str) -> Optional[Order]:
        """Get order by order number"""
        result = await db.execute(
            select(Order).where(Order.order_number == order_number)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_order_for_customer(
        db: AsyncSession,
        order_id: str,
        customer_id: str,
        restaurant_id: Optional[str],
    ) -> Optional[Order]:
        """Single order only if it belongs to the customer at the given restaurant."""
        if not restaurant_id:
            return None
        q = (
            select(Order)
            .options(selectinload(Order.items))
            .where(
                Order.id == order_id,
                Order.restaurant_id == restaurant_id,
                Order.customer_id == customer_id,
            )
        )
        result = await db.execute(q)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_orders_for_customer(
        db: AsyncSession,
        *,
        customer_id: str,
        restaurant_id: Optional[str],
        skip: int = 0,
        limit: int = 50,
        status: Optional[OrderStatus] = None,
    ) -> tuple[List[Order], int]:
        """Paginated orders for a registered customer (scoped by restaurant)."""
        if not restaurant_id:
            return [], 0

        filters = [
            Order.restaurant_id == restaurant_id,
            Order.customer_id == customer_id,
        ]
        if status is not None:
            filters.append(Order.status == status.value)

        base = select(Order).where(and_(*filters))
        count_result = await db.execute(select(func.count()).select_from(base.subquery()))
        total = count_result.scalar_one()

        list_q = (
            select(Order)
            .options(selectinload(Order.items))
            .where(and_(*filters))
            .order_by(desc(Order.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(list_q)
        return list(result.scalars().all()), total

    @staticmethod
    async def get_orders(
        db: AsyncSession,
        restaurant_id: str,
        skip: int = 0,
        limit: int = 100,
        order_type: Optional[OrderType] = None,
        status: Optional[OrderStatus] = None,
        payment_status: Optional[PaymentStatus] = None,
        customer_id: Optional[str] = None,
        table_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search: Optional[str] = None
    ) -> tuple[List[Order], int]:
        """Get paginated list of orders with filtering"""
        query = select(Order).where(Order.restaurant_id == restaurant_id)
        
        # Apply filters
        if order_type is not None:
            query = query.where(Order.order_type == order_type)
        
        if status is not None:
            query = query.where(Order.status == status)
        
        if payment_status is not None:
            query = query.where(Order.payment_status == payment_status)
        
        if customer_id is not None:
            query = query.where(Order.customer_id == customer_id)
        
        if table_id is not None:
            query = query.where(Order.table_id == table_id)
        
        if start_date is not None:
            query = query.where(Order.created_at >= start_date)
        
        if end_date is not None:
            query = query.where(Order.created_at <= end_date)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Order.order_number.ilike(search_pattern),
                    Order.guest_name.ilike(search_pattern),
                    Order.guest_phone.ilike(search_pattern)
                )
            )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()
        
        # Apply pagination and ordering
        query = query.order_by(desc(Order.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        orders = list(result.scalars().all())
        
        return orders, total
    
    @staticmethod
    async def update_order(
        db: AsyncSession,
        order_id: str,
        order_data: OrderUpdate
    ) -> Optional[Order]:
        """Update order"""
        order = await OrderService.get_order_by_id(db, order_id)
        
        if not order:
            return None
        
        # Update only provided fields
        update_data = order_data.model_dump(exclude_unset=True)
        
        # Handle status changes with timestamps
        if "status" in update_data:
            new_status = update_data["status"]
            now = datetime.utcnow()
            
            if new_status == OrderStatus.CONFIRMED and not order.confirmed_at:
                order.confirmed_at = now
            elif new_status == OrderStatus.PREPARING and not order.preparing_at:
                order.preparing_at = now
            elif new_status == OrderStatus.READY and not order.ready_at:
                order.ready_at = now
            elif new_status == OrderStatus.COMPLETED and not order.completed_at:
                order.completed_at = now
            elif new_status == OrderStatus.CANCELLED and not order.cancelled_at:
                order.cancelled_at = now
        
        for field, value in update_data.items():
            if field != "status":
                setattr(order, field, value)
            else:
                order.status = value
        
        # Recalculate totals if financial fields changed
        if any(field in update_data for field in ["discount_amount", "delivery_fee", "service_charge", "tip_amount"]):
            items = await OrderService.get_order_items(db, order_id)
            totals = OrderService.calculate_order_totals(
                items,
                order.discount_amount,
                order.delivery_fee,
                order.service_charge,
                order.tip_amount
            )
            order.total_amount = totals["total_amount"]
        
        await db.commit()
        await db.refresh(order)
        
        return order
    
    @staticmethod
    async def add_items_to_order(
        db: AsyncSession,
        order_id: str,
        items: List[OrderItemCreate]
    ) -> Optional[Order]:
        """Add items to existing order"""
        order = await OrderService.get_order_by_id(db, order_id)
        
        if not order:
            return None
        
        # Create new items
        for item_data in items:
            total_price = OrderService.calculate_item_total(item_data)
            
            db_item = OrderItem(
                order_id=order_id,
                product_id=item_data.product_id,
                product_name=item_data.product_name,
                product_image=item_data.product_image,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                modifiers=item_data.modifiers,
                customization=item_data.customization,
                modifiers_price=item_data.modifiers_price,
                discount_amount=item_data.discount_amount,
                tax_amount=item_data.tax_amount,
                total_price=total_price,
                department=item_data.department,
                printer_tag=item_data.printer_tag,
                is_complimentary=item_data.is_complimentary,
                notes=item_data.notes,
                status="pending"
            )
            db.add(db_item)
        
        # Recalculate order totals
        all_items = await OrderService.get_order_items(db, order_id)
        totals = OrderService.calculate_order_totals(
            all_items,
            order.discount_amount,
            order.delivery_fee,
            order.service_charge,
            order.tip_amount
        )
        
        order.subtotal = totals["subtotal"]
        order.tax_amount = totals["tax_amount"]
        order.total_amount = totals["total_amount"]
        
        await db.commit()
        await db.refresh(order)
        
        return order
    
    @staticmethod
    async def update_order_item(
        db: AsyncSession,
        item_id: str,
        item_data: OrderItemUpdate
    ) -> Optional[OrderItem]:
        """Update order item"""
        result = await db.execute(
            select(OrderItem).where(OrderItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        
        if not item:
            return None
        
        # Update only provided fields
        update_data = item_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)
        
        # Recalculate item total if quantity or prices changed
        if any(field in update_data for field in ["quantity", "modifiers_price", "discount_amount"]):
            base_price = item.unit_price + item.modifiers_price
            subtotal = base_price * item.quantity
            item.total_price = max(0, subtotal - item.discount_amount + item.tax_amount)
        
        await db.commit()
        await db.refresh(item)
        
        # Recalculate order totals
        order = await OrderService.get_order_by_id(db, item.order_id)
        if order:
            all_items = await OrderService.get_order_items(db, item.order_id)
            totals = OrderService.calculate_order_totals(
                all_items,
                order.discount_amount,
                order.delivery_fee,
                order.service_charge,
                order.tip_amount
            )
            
            order.subtotal = totals["subtotal"]
            order.tax_amount = totals["tax_amount"]
            order.total_amount = totals["total_amount"]
            
            await db.commit()
        
        return item
    
    @staticmethod
    async def delete_order_item(db: AsyncSession, item_id: str) -> bool:
        """Delete order item and recalculate order totals"""
        result = await db.execute(
            select(OrderItem).where(OrderItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        
        if not item:
            return False
        
        order_id = item.order_id
        await db.delete(item)
        await db.commit()
        
        # Recalculate order totals
        order = await OrderService.get_order_by_id(db, order_id)
        if order:
            remaining_items = await OrderService.get_order_items(db, order_id)
            
            if remaining_items:
                totals = OrderService.calculate_order_totals(
                    remaining_items,
                    order.discount_amount,
                    order.delivery_fee,
                    order.service_charge,
                    order.tip_amount
                )
                
                order.subtotal = totals["subtotal"]
                order.tax_amount = totals["tax_amount"]
                order.total_amount = totals["total_amount"]
            else:
                # If no items left, reset totals
                order.subtotal = 0
                order.tax_amount = 0
                order.total_amount = 0
            
            await db.commit()
        
        return True
    
    @staticmethod
    async def cancel_order(db: AsyncSession, order_id: str, reason: Optional[str] = None) -> Optional[Order]:
        """Cancel an order"""
        order = await OrderService.get_order_by_id(db, order_id)
        
        if not order:
            return None
        
        order.status = OrderStatus.CANCELLED
        order.cancelled_at = datetime.utcnow()
        if reason:
            order.staff_notes = f"{order.staff_notes or ''}\nCancellation reason: {reason}".strip()
        
        await db.commit()
        await db.refresh(order)
        
        return order
    
    @staticmethod
    async def get_order_statistics(
        db: AsyncSession,
        restaurant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Get order statistics for a restaurant"""
        query = select(Order).where(Order.restaurant_id == restaurant_id)
        
        if start_date:
            query = query.where(Order.created_at >= start_date)
        if end_date:
            query = query.where(Order.created_at <= end_date)
        
        # Total orders
        total_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()
        
        # Count by status
        statuses = {}
        for status in OrderStatus:
            status_query = select(func.count()).select_from(
                query.where(Order.status == status).subquery()
            )
            status_result = await db.execute(status_query)
            statuses[f"{status.value}_orders"] = status_result.scalar_one()
        
        # Revenue (completed orders only)
        revenue_query = select(func.sum(Order.total_amount)).select_from(
            query.where(Order.status == OrderStatus.COMPLETED).subquery()
        )
        revenue_result = await db.execute(revenue_query)
        total_revenue = revenue_result.scalar_one() or 0
        
        # Average order value
        avg_value = int(total_revenue / statuses["completed_orders"]) if statuses["completed_orders"] > 0 else 0
        
        return {
            "total_orders": total,
            **statuses,
            "total_revenue": total_revenue,
            "average_order_value": avg_value
        }
