from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from typing import Optional, List
from datetime import datetime, timedelta
from app.modules.kds.model import (
    KitchenStation,
    KitchenDisplay,
    KitchenDisplayItem,
    StationType,
    DisplayStatus,
    ItemStatus
)
from app.modules.kds.schema import KitchenStationCreate, KitchenStationUpdate
from app.modules.order.model import Order, OrderItem


class KDSService:
    """Service layer for Kitchen Display System operations"""
    
    @staticmethod
    async def create_station(db: AsyncSession, station_data: KitchenStationCreate) -> KitchenStation:
        """Create a new kitchen station"""
        # Convert lists to dict format for JSON storage
        departments_dict = {"items": station_data.departments} if station_data.departments else None
        printer_tags_dict = {"items": station_data.printer_tags} if station_data.printer_tags else None
        assigned_staff_dict = {"items": station_data.assigned_staff} if station_data.assigned_staff else None
        
        db_station = KitchenStation(
            restaurant_id=station_data.restaurant_id,
            name=station_data.name,
            station_type=station_data.station_type,
            description=station_data.description,
            floor=station_data.floor,
            section=station_data.section,
            display_order=station_data.display_order,
            color_code=station_data.color_code,
            departments=departments_dict,
            printer_tags=printer_tags_dict,
            max_concurrent_orders=station_data.max_concurrent_orders,
            average_prep_time=station_data.average_prep_time,
            auto_accept_orders=station_data.auto_accept_orders,
            alert_on_new_order=station_data.alert_on_new_order,
            show_customer_names=station_data.show_customer_names,
            show_table_numbers=station_data.show_table_numbers,
            assigned_staff=assigned_staff_dict
        )
        
        db.add(db_station)
        await db.commit()
        await db.refresh(db_station)
        
        return db_station
    
    @staticmethod
    async def get_station_by_id(db: AsyncSession, station_id: str) -> Optional[KitchenStation]:
        """Get kitchen station by ID"""
        result = await db.execute(
            select(KitchenStation).where(KitchenStation.id == station_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_stations(
        db: AsyncSession,
        restaurant_id: str,
        station_type: Optional[StationType] = None,
        is_active: Optional[bool] = None,
        is_online: Optional[bool] = None
    ) -> List[KitchenStation]:
        """Get kitchen stations for a restaurant"""
        query = select(KitchenStation).where(KitchenStation.restaurant_id == restaurant_id)
        
        if station_type is not None:
            query = query.where(KitchenStation.station_type == station_type)
        
        if is_active is not None:
            query = query.where(KitchenStation.is_active == is_active)
        
        if is_online is not None:
            query = query.where(KitchenStation.is_online == is_online)
        
        query = query.order_by(KitchenStation.display_order.asc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def update_station(
        db: AsyncSession,
        station_id: str,
        station_data: KitchenStationUpdate
    ) -> Optional[KitchenStation]:
        """Update kitchen station"""
        station = await KDSService.get_station_by_id(db, station_id)
        
        if not station:
            return None
        
        update_data = station_data.model_dump(exclude_unset=True)
        
        # Convert lists to dict format for JSON fields
        if "departments" in update_data and update_data["departments"] is not None:
            update_data["departments"] = {"items": update_data["departments"]}
        if "printer_tags" in update_data and update_data["printer_tags"] is not None:
            update_data["printer_tags"] = {"items": update_data["printer_tags"]}
        if "assigned_staff" in update_data and update_data["assigned_staff"] is not None:
            update_data["assigned_staff"] = {"items": update_data["assigned_staff"]}
        
        for field, value in update_data.items():
            setattr(station, field, value)
        
        await db.commit()
        await db.refresh(station)
        
        return station
    
    @staticmethod
    async def delete_station(db: AsyncSession, station_id: str) -> bool:
        """Delete kitchen station"""
        station = await KDSService.get_station_by_id(db, station_id)
        
        if not station:
            return False
        
        station.is_active = False
        await db.commit()
        
        return True
    
    @staticmethod
    async def route_order_to_stations(
        db: AsyncSession,
        order_id: str,
        user_id: Optional[str] = None
    ) -> List[KitchenDisplay]:
        """
        Route an order to appropriate kitchen stations based on items
        """
        # Get order with items
        order_result = await db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = order_result.scalar_one_or_none()
        
        if not order:
            return []
        
        # Get order items
        items_result = await db.execute(
            select(OrderItem).where(OrderItem.order_id == order_id)
        )
        order_items = list(items_result.scalars().all())
        
        # Get all active stations for the restaurant
        stations = await KDSService.get_stations(
            db,
            restaurant_id=order.restaurant_id,
            is_active=True
        )
        
        # Group items by station based on department/printer_tag
        station_items = {}
        for item in order_items:
            for station in stations:
                # Check if item's department or printer_tag matches station
                if station.departments and item.department:
                    dept_list = station.departments.get("items", [])
                    if item.department in dept_list:
                        if station.id not in station_items:
                            station_items[station.id] = []
                        station_items[station.id].append(item)
                        break
                elif station.printer_tags and item.printer_tag:
                    tag_list = station.printer_tags.get("items", [])
                    if item.printer_tag in tag_list:
                        if station.id not in station_items:
                            station_items[station.id] = []
                        station_items[station.id].append(item)
                        break
        
        # If no items were routed, route all to main kitchen
        if not station_items:
            main_kitchen = next(
                (s for s in stations if s.station_type == StationType.MAIN_KITCHEN),
                stations[0] if stations else None
            )
            if main_kitchen:
                station_items[main_kitchen.id] = order_items
        
        # Create displays for each station
        displays = []
        for station_id, items in station_items.items():
            station = next((s for s in stations if s.id == station_id), None)
            if not station:
                continue
            
            # Calculate estimated prep time
            est_prep = station.average_prep_time or 15
            due_time = datetime.utcnow() + timedelta(minutes=est_prep)
            
            # Get table number if applicable
            table_number = None
            if order.table_id:
                table_result = await db.execute(
                    select("tables").where("tables.id" == order.table_id)
                )
                # This is simplified - proper implementation would import Table model
            
            # Create kitchen display
            display = KitchenDisplay(
                restaurant_id=order.restaurant_id,
                station_id=station_id,
                order_id=order.id,
                order_number=order.order_number,
                order_type=order.order_type.value if hasattr(order.order_type, 'value') else order.order_type,
                table_number=table_number,
                customer_name=order.guest_name or (order.customer_id if order.customer_id else None),
                status=DisplayStatus.ACKNOWLEDGED if station.auto_accept_orders else DisplayStatus.NEW,
                priority=1 if order.is_priority else 0,
                estimated_prep_time=est_prep,
                due_time=due_time,
                is_rush=order.is_priority,
                special_instructions=order.special_instructions,
                kitchen_notes=order.kitchen_notes,
                total_items=len(items),
                completed_items=0
            )
            
            if station.auto_accept_orders:
                display.acknowledged_at = datetime.utcnow()
                display.acknowledged_by = user_id
            
            db.add(display)
            await db.flush()
            
            # Create display items
            for idx, item in enumerate(items):
                display_item = KitchenDisplayItem(
                    display_id=display.id,
                    order_item_id=item.id,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    modifiers=item.modifiers,
                    customization=item.customization,
                    status=ItemStatus.PENDING,
                    display_order=idx,
                    is_complimentary=item.is_complimentary,
                    notes=item.notes
                )
                db.add(display_item)
            
            displays.append(display)
        
        await db.commit()
        
        for display in displays:
            await db.refresh(display)
        
        # Send WebSocket notification for new orders (imported lazily to avoid circular import)
        try:
            from app.modules.kds.websocket import kds_manager
            from app.modules.kds.schema import KitchenDisplayResponse, KitchenDisplayItemResponse
            
            for display in displays:
                items = await KDSService.get_display_items(db, display.id)
                display_response = KitchenDisplayResponse.model_validate(display)
                display_response.items = [KitchenDisplayItemResponse.model_validate(item) for item in items]
                
                await kds_manager.notify_new_order(
                    restaurant_id=display.restaurant_id,
                    station_id=display.station_id,
                    display_data=display_response.model_dump(mode='json')
                )
        except Exception as e:
            # Don't fail the operation if WebSocket notification fails
            print(f"WebSocket notification failed: {str(e)}")
        
        return displays
    
    @staticmethod
    async def get_display_by_id(db: AsyncSession, display_id: str) -> Optional[KitchenDisplay]:
        """Get kitchen display by ID"""
        result = await db.execute(
            select(KitchenDisplay).where(KitchenDisplay.id == display_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_display_items(db: AsyncSession, display_id: str) -> List[KitchenDisplayItem]:
        """Get items for a kitchen display"""
        result = await db.execute(
            select(KitchenDisplayItem)
            .where(KitchenDisplayItem.display_id == display_id)
            .order_by(KitchenDisplayItem.display_order.asc())
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_station_displays(
        db: AsyncSession,
        station_id: str,
        status: Optional[DisplayStatus] = None,
        limit: int = 100
    ) -> List[KitchenDisplay]:
        """Get displays for a kitchen station"""
        query = select(KitchenDisplay).where(KitchenDisplay.station_id == station_id)
        
        if status is not None:
            query = query.where(KitchenDisplay.status == status)
        else:
            # Exclude completed and cancelled by default
            query = query.where(
                KitchenDisplay.status.not_in([DisplayStatus.COMPLETED, DisplayStatus.CANCELLED])
            )
        
        query = query.order_by(
            KitchenDisplay.priority.desc(),
            KitchenDisplay.received_at.asc()
        ).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def acknowledge_display(
        db: AsyncSession,
        display_id: str,
        user_id: Optional[str] = None
    ) -> Optional[KitchenDisplay]:
        """Acknowledge a kitchen display (kitchen has seen the order)"""
        display = await KDSService.get_display_by_id(db, display_id)
        
        if not display:
            return None
        
        old_status = display.status
        
        if display.status == DisplayStatus.NEW:
            display.status = DisplayStatus.ACKNOWLEDGED
            display.acknowledged_at = datetime.utcnow()
            display.acknowledged_by = user_id
            
            await db.commit()
            await db.refresh(display)
            
            # Send WebSocket notification
            try:
                from app.modules.kds.websocket import kds_manager
                await kds_manager.notify_status_change(
                    restaurant_id=display.restaurant_id,
                    station_id=display.station_id,
                    display_id=display_id,
                    old_status=old_status,
                    new_status=display.status
                )
            except Exception as e:
                print(f"WebSocket notification failed: {str(e)}")
        
        return display
    
    @staticmethod
    async def start_display(
        db: AsyncSession,
        display_id: str,
        user_id: Optional[str] = None
    ) -> Optional[KitchenDisplay]:
        """Start preparing a kitchen display"""
        display = await KDSService.get_display_by_id(db, display_id)
        
        if not display:
            return None
        
        old_status = display.status
        
        if display.status in [DisplayStatus.NEW, DisplayStatus.ACKNOWLEDGED]:
            display.status = DisplayStatus.IN_PROGRESS
            display.started_at = datetime.utcnow()
            display.prepared_by = user_id
            
            # Auto-acknowledge if not already
            if not display.acknowledged_at:
                display.acknowledged_at = datetime.utcnow()
                display.acknowledged_by = user_id
            
            await db.commit()
            await db.refresh(display)
            
            # Send WebSocket notification
            try:
                from app.modules.kds.websocket import kds_manager
                await kds_manager.notify_status_change(
                    restaurant_id=display.restaurant_id,
                    station_id=display.station_id,
                    display_id=display_id,
                    old_status=old_status,
                    new_status=display.status
                )
            except Exception as e:
                print(f"WebSocket notification failed: {str(e)}")
        
        return display
    
    @staticmethod
    async def complete_display(
        db: AsyncSession,
        display_id: str,
        user_id: Optional[str] = None
    ) -> Optional[KitchenDisplay]:
        """Mark a kitchen display as ready/completed"""
        display = await KDSService.get_display_by_id(db, display_id)
        
        if not display:
            return None
        
        old_status = display.status
        display.status = DisplayStatus.READY
        display.ready_at = datetime.utcnow()
        
        # Calculate actual prep time
        if display.started_at:
            display.actual_prep_time = int((display.ready_at - display.started_at).total_seconds() / 60)
        
        # Mark all items as ready
        items = await KDSService.get_display_items(db, display_id)
        for item in items:
            if item.status != ItemStatus.CANCELLED:
                item.status = ItemStatus.READY
                item.completed_at = datetime.utcnow()
                if not item.prepared_by:
                    item.prepared_by = user_id
        
        display.completed_items = len([i for i in items if i.status == ItemStatus.READY])
        
        await db.commit()
        await db.refresh(display)
        
        # Send WebSocket notifications
        try:
            from app.modules.kds.websocket import kds_manager
            
            # Notify status change
            await kds_manager.notify_status_change(
                restaurant_id=display.restaurant_id,
                station_id=display.station_id,
                display_id=display_id,
                old_status=old_status,
                new_status=display.status
            )
            
            # Notify POS that order is ready
            await kds_manager.notify_order_completed(
                restaurant_id=display.restaurant_id,
                order_id=display.order_id,
                order_data={
                    "order_id": display.order_id,
                    "order_number": display.order_number,
                    "table_number": display.table_number,
                    "actual_prep_time": display.actual_prep_time
                }
            )
        except Exception as e:
            print(f"WebSocket notification failed: {str(e)}")
        
        return display
    
    @staticmethod
    async def bump_display(
        db: AsyncSession,
        display_id: str
    ) -> Optional[KitchenDisplay]:
        """Bump (remove) a display from the kitchen screen"""
        display = await KDSService.get_display_by_id(db, display_id)
        
        if not display:
            return None
        
        display.status = DisplayStatus.COMPLETED
        display.completed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(display)
        
        return display
    
    @staticmethod
    async def update_item_status(
        db: AsyncSession,
        item_id: str,
        new_status: ItemStatus,
        user_id: Optional[str] = None
    ) -> Optional[KitchenDisplayItem]:
        """Update status of a kitchen display item"""
        result = await db.execute(
            select(KitchenDisplayItem).where(KitchenDisplayItem.id == item_id)
        )
        item = result.scalar_one_or_none()
        
        if not item:
            return None
        
        old_status = item.status
        now = datetime.utcnow()
        item.status = new_status
        
        if new_status == ItemStatus.PREPARING and not item.started_at:
            item.started_at = now
            item.prepared_by = user_id
        elif new_status == ItemStatus.READY:
            item.completed_at = now
            if item.started_at:
                item.prep_time = int((now - item.started_at).total_seconds())
            if not item.prepared_by:
                item.prepared_by = user_id
        
        # Update display completed items count
        display = await KDSService.get_display_by_id(db, item.display_id)
        if display:
            items = await KDSService.get_display_items(db, item.display_id)
            display.completed_items = len([i for i in items if i.status in [ItemStatus.READY, ItemStatus.SERVED]])
        
        await db.commit()
        await db.refresh(item)
        
        # Send WebSocket notification
        if display:
            try:
                from app.modules.kds.websocket import kds_manager
                await kds_manager.notify_item_status_change(
                    restaurant_id=display.restaurant_id,
                    station_id=display.station_id,
                    display_id=item.display_id,
                    item_id=item_id,
                    old_status=old_status,
                    new_status=new_status
                )
            except Exception as e:
                print(f"WebSocket notification failed: {str(e)}")
        
        return item
    
    @staticmethod
    async def get_station_performance(
        db: AsyncSession,
        station_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Get performance metrics for a kitchen station"""
        query = select(KitchenDisplay).where(KitchenDisplay.station_id == station_id)
        
        if start_date:
            query = query.where(KitchenDisplay.received_at >= start_date)
        if end_date:
            query = query.where(KitchenDisplay.received_at <= end_date)
        
        # Total orders
        total_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = total_result.scalar_one()
        
        # Completed orders
        completed_query = query.where(KitchenDisplay.status == DisplayStatus.COMPLETED)
        completed_result = await db.execute(select(func.count()).select_from(completed_query.subquery()))
        completed = completed_result.scalar_one()
        
        # Average prep time
        avg_query = select(func.avg(KitchenDisplay.actual_prep_time)).where(
            and_(
                KitchenDisplay.station_id == station_id,
                KitchenDisplay.actual_prep_time.isnot(None)
            )
        )
        if start_date:
            avg_query = avg_query.where(KitchenDisplay.received_at >= start_date)
        if end_date:
            avg_query = avg_query.where(KitchenDisplay.received_at <= end_date)
        
        avg_result = await db.execute(avg_query)
        avg_prep = avg_result.scalar_one() or 0
        
        # Delayed orders
        delayed_result = await db.execute(
            select(func.count()).select_from(
                query.where(KitchenDisplay.is_delayed == True).subquery()
            )
        )
        delayed = delayed_result.scalar_one()
        
        # Current active orders
        active_result = await db.execute(
            select(func.count()).where(
                and_(
                    KitchenDisplay.station_id == station_id,
                    KitchenDisplay.status.in_([
                        DisplayStatus.NEW,
                        DisplayStatus.ACKNOWLEDGED,
                        DisplayStatus.IN_PROGRESS
                    ])
                )
            )
        )
        active = active_result.scalar_one()
        
        # On-time percentage
        on_time_pct = 0.0
        if completed > 0:
            on_time = completed - delayed
            on_time_pct = (on_time / completed) * 100
        
        # Get station info
        station = await KDSService.get_station_by_id(db, station_id)
        
        return {
            "station_id": station_id,
            "station_name": station.name if station else "Unknown",
            "total_orders": total,
            "completed_orders": completed,
            "average_prep_time": float(avg_prep),
            "on_time_percentage": round(on_time_pct, 2),
            "delayed_orders": delayed,
            "current_active_orders": active
        }
