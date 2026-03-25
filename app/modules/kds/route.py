from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.response import success_response, error_response
from app.modules.kds.schema import (
    KitchenStationCreate,
    KitchenStationUpdate,
    KitchenStationResponse,
    KitchenDisplayResponse,
    KitchenDisplayItemResponse,
    DisplayStatusUpdate,
    ItemStatusUpdate,
    BumpOrderRequest,
    BulkItemStatusUpdate,
    StationStatusUpdate,
    KitchenPerformance
)
from app.modules.kds.model import StationType, DisplayStatus, ItemStatus
from app.modules.kds.service import KDSService
from app.modules.kds.printer import KOTPrinter
from app.modules.kds.websocket import kds_manager
from app.modules.user.model import User


router = APIRouter(prefix="/kds", tags=["kitchen-display-system"])


# Kitchen Station Endpoints
@router.post("/stations", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_station(
    station_data: KitchenStationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new kitchen station
    
    - **name**: Station name (required)
    - **station_type**: Type (main_kitchen, grill, bar, etc.)
    - **departments**: List of department tags this station handles
    - **printer_tags**: List of printer tags for routing
    - **display_order**: Order in station list
    - **color_code**: Hex color for UI (#RRGGBB)
    - **max_concurrent_orders**: Maximum concurrent orders
    - **average_prep_time**: Average preparation time in minutes
    - **auto_accept_orders**: Automatically acknowledge new orders
    """
    try:
        station = await KDSService.create_station(db, station_data)
        return success_response(
            data=KitchenStationResponse.model_validate(station),
            message="Kitchen station created successfully"
        )
    except Exception as e:
        return error_response(
            message="Failed to create kitchen station",
            error=str(e)
        )


@router.get("/stations/{station_id}", response_model=dict)
async def get_station(
    station_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get kitchen station by ID"""
    station = await KDSService.get_station_by_id(db, station_id)
    
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kitchen station not found"
        )
    
    return success_response(
        data=KitchenStationResponse.model_validate(station),
        message="Station retrieved successfully"
    )


@router.get("/stations/restaurant/{restaurant_id}", response_model=dict)
async def get_restaurant_stations(
    restaurant_id: str,
    station_type: Optional[StationType] = Query(None, description="Filter by station type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_online: Optional[bool] = Query(None, description="Filter by online status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get kitchen stations for a restaurant
    
    - **station_type**: Filter by type
    - **is_active**: Filter by active status
    - **is_online**: Filter by online status
    """
    stations = await KDSService.get_stations(
        db,
        restaurant_id=restaurant_id,
        station_type=station_type,
        is_active=is_active,
        is_online=is_online
    )
    
    return success_response(
        data={
            "total": len(stations),
            "stations": [KitchenStationResponse.model_validate(s) for s in stations]
        },
        message="Stations retrieved successfully"
    )


@router.put("/stations/{station_id}", response_model=dict)
async def update_station(
    station_id: str,
    station_data: KitchenStationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update kitchen station"""
    station = await KDSService.update_station(db, station_id, station_data)
    
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kitchen station not found"
        )
    
    return success_response(
        data=KitchenStationResponse.model_validate(station),
        message="Station updated successfully"
    )


@router.patch("/stations/{station_id}/status", response_model=dict)
async def update_station_status(
    station_id: str,
    status_data: StationStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update station online/offline status"""
    station = await KDSService.update_station(
        db,
        station_id,
        KitchenStationUpdate(is_online=status_data.is_online)
    )
    
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kitchen station not found"
        )
    
    return success_response(
        data=KitchenStationResponse.model_validate(station),
        message=f"Station is now {'online' if status_data.is_online else 'offline'}"
    )


@router.delete("/stations/{station_id}", response_model=dict)
async def delete_station(
    station_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deactivate kitchen station"""
    success = await KDSService.delete_station(db, station_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kitchen station not found"
        )
    
    return success_response(
        data={"id": station_id},
        message="Station deactivated successfully"
    )


# Kitchen Display Endpoints
@router.post("/displays/route/{order_id}", response_model=dict)
async def route_order_to_stations(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Route an order to appropriate kitchen stations
    
    Creates kitchen displays for each relevant station based on order items
    """
    try:
        displays = await KDSService.route_order_to_stations(db, order_id, current_user.id)
        
        # Load items for each display
        displays_with_items = []
        for display in displays:
            items = await KDSService.get_display_items(db, display.id)
            display_response = KitchenDisplayResponse.model_validate(display)
            display_response.items = [KitchenDisplayItemResponse.model_validate(item) for item in items]
            displays_with_items.append(display_response)
        
        return success_response(
            data={
                "total_displays": len(displays),
                "displays": displays_with_items
            },
            message="Order routed to kitchen stations successfully"
        )
    except Exception as e:
        return error_response(
            message="Failed to route order",
            error=str(e)
        )


@router.get("/displays/{display_id}", response_model=dict)
async def get_display(
    display_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get kitchen display by ID with items"""
    display = await KDSService.get_display_by_id(db, display_id)
    
    if not display:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Display not found"
        )
    
    items = await KDSService.get_display_items(db, display_id)
    display_response = KitchenDisplayResponse.model_validate(display)
    display_response.items = [KitchenDisplayItemResponse.model_validate(item) for item in items]
    
    return success_response(
        data=display_response,
        message="Display retrieved successfully"
    )


@router.get("/displays/station/{station_id}", response_model=dict)
async def get_station_displays(
    station_id: str,
    status: Optional[DisplayStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get displays for a kitchen station
    
    Returns active displays by default (excludes completed/cancelled)
    """
    displays = await KDSService.get_station_displays(db, station_id, status, limit)
    
    # Load items for each display
    displays_with_items = []
    for display in displays:
        items = await KDSService.get_display_items(db, display.id)
        display_response = KitchenDisplayResponse.model_validate(display)
        display_response.items = [KitchenDisplayItemResponse.model_validate(item) for item in items]
        displays_with_items.append(display_response)
    
    return success_response(
        data={
            "total": len(displays),
            "displays": displays_with_items
        },
        message="Station displays retrieved successfully"
    )


@router.post("/displays/{display_id}/acknowledge", response_model=dict)
async def acknowledge_display(
    display_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Acknowledge a display (kitchen has seen it)"""
    display = await KDSService.acknowledge_display(db, display_id, current_user.id)
    
    if not display:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Display not found"
        )
    
    items = await KDSService.get_display_items(db, display_id)
    display_response = KitchenDisplayResponse.model_validate(display)
    display_response.items = [KitchenDisplayItemResponse.model_validate(item) for item in items]
    
    return success_response(
        data=display_response,
        message="Display acknowledged"
    )


@router.post("/displays/{display_id}/start", response_model=dict)
async def start_display(
    display_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start preparing a display"""
    display = await KDSService.start_display(db, display_id, current_user.id)
    
    if not display:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Display not found"
        )
    
    items = await KDSService.get_display_items(db, display_id)
    display_response = KitchenDisplayResponse.model_validate(display)
    display_response.items = [KitchenDisplayItemResponse.model_validate(item) for item in items]
    
    return success_response(
        data=display_response,
        message="Display preparation started"
    )


@router.post("/displays/{display_id}/complete", response_model=dict)
async def complete_display(
    display_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark display as ready/completed"""
    display = await KDSService.complete_display(db, display_id, current_user.id)
    
    if not display:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Display not found"
        )
    
    items = await KDSService.get_display_items(db, display_id)
    display_response = KitchenDisplayResponse.model_validate(display)
    display_response.items = [KitchenDisplayItemResponse.model_validate(item) for item in items]
    
    return success_response(
        data=display_response,
        message="Display marked as ready"
    )


@router.post("/displays/{display_id}/bump", response_model=dict)
async def bump_display(
    display_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bump (remove) display from kitchen screen"""
    display = await KDSService.bump_display(db, display_id)
    
    if not display:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Display not found"
        )
    
    return success_response(
        data={"id": display_id},
        message="Display bumped successfully"
    )


# Kitchen Display Item Endpoints
@router.patch("/items/{item_id}/status", response_model=dict)
async def update_item_status(
    item_id: str,
    status_data: ItemStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update individual item status"""
    item = await KDSService.update_item_status(
        db,
        item_id,
        status_data.status,
        current_user.id
    )
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Display item not found"
        )
    
    return success_response(
        data=KitchenDisplayItemResponse.model_validate(item),
        message=f"Item status updated to {status_data.status.value}"
    )


@router.post("/items/bulk/status", response_model=dict)
async def bulk_update_item_status(
    bulk_data: BulkItemStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk update item statuses"""
    updated_items = []
    
    for item_id in bulk_data.item_ids:
        item = await KDSService.update_item_status(
            db,
            item_id,
            bulk_data.status,
            current_user.id
        )
        if item:
            updated_items.append(item)
    
    return success_response(
        data={
            "updated_count": len(updated_items),
            "items": [KitchenDisplayItemResponse.model_validate(item) for item in updated_items]
        },
        message=f"Updated {len(updated_items)} items"
    )


# Performance and Analytics
@router.get("/stations/{station_id}/performance", response_model=dict)
async def get_station_performance(
    station_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date for metrics"),
    end_date: Optional[datetime] = Query(None, description="End date for metrics"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get performance metrics for a kitchen station
    
    Returns order counts, average prep time, on-time percentage, etc.
    """
    performance = await KDSService.get_station_performance(
        db,
        station_id,
        start_date,
        end_date
    )
    
    return success_response(
        data=performance,
        message="Performance metrics retrieved successfully"
    )


# KOT (Kitchen Order Ticket) Printing Endpoints
@router.get("/displays/{display_id}/kot/text", response_class=PlainTextResponse)
async def get_kot_text(
    display_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate Kitchen Order Ticket in plain text format
    
    Suitable for thermal printers or text-based printing systems
    """
    display = await KDSService.get_display_by_id(db, display_id)
    
    if not display:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Display not found"
        )
    
    station = await KDSService.get_station_by_id(db, display.station_id)
    items = await KDSService.get_display_items(db, display_id)
    
    kot_text = KOTPrinter.generate_kot_text(display, items, station)
    
    return PlainTextResponse(content=kot_text, media_type="text/plain")


@router.get("/displays/{display_id}/kot/html", response_class=HTMLResponse)
async def get_kot_html(
    display_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate Kitchen Order Ticket in HTML format
    
    Suitable for web printing or PDF generation
    Can be used with window.print() or PDF rendering libraries
    """
    display = await KDSService.get_display_by_id(db, display_id)
    
    if not display:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Display not found"
        )
    
    station = await KDSService.get_station_by_id(db, display.station_id)
    items = await KDSService.get_display_items(db, display_id)
    
    kot_html = KOTPrinter.generate_kot_html(display, items, station)
    
    return HTMLResponse(content=kot_html)


@router.get("/displays/{display_id}/kot/json", response_model=dict)
async def get_kot_json(
    display_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate Kitchen Order Ticket in JSON format
    
    Suitable for integration with printer systems or third-party services
    """
    display = await KDSService.get_display_by_id(db, display_id)
    
    if not display:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Display not found"
        )
    
    station = await KDSService.get_station_by_id(db, display.station_id)
    items = await KDSService.get_display_items(db, display_id)
    
    kot_json = KOTPrinter.generate_kot_json(display, items, station)
    
    return success_response(
        data=kot_json,
        message="KOT generated successfully"
    )


@router.post("/displays/{display_id}/kot/print", response_model=dict)
async def print_kot(
    display_id: str,
    format: str = Query("text", description="Format: text, html, or json"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger KOT printing for a display
    
    This endpoint generates the KOT and returns the formatted content.
    In production, this would integrate with your printer service/hardware.
    
    - **format**: text (thermal printer), html (web print/PDF), or json (API integration)
    """
    display = await KDSService.get_display_by_id(db, display_id)
    
    if not display:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Display not found"
        )
    
    station = await KDSService.get_station_by_id(db, display.station_id)
    items = await KDSService.get_display_items(db, display_id)
    
    if format == "text":
        content = KOTPrinter.generate_kot_text(display, items, station)
        content_type = "text/plain"
    elif format == "html":
        content = KOTPrinter.generate_kot_html(display, items, station)
        content_type = "text/html"
    elif format == "json":
        content = KOTPrinter.generate_kot_json(display, items, station)
        content_type = "application/json"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid format. Choose: text, html, or json"
        )
    
    # In production, you would send this to a printer service here
    # Example: await printer_service.print(content, station.printer_tags)
    
    return success_response(
        data={
            "display_id": display_id,
            "order_number": display.order_number,
            "station": station.name,
            "format": format,
            "content_type": content_type,
            "printed_at": datetime.utcnow().isoformat(),
            "content": content if format == "json" else f"Content ready ({len(str(content))} chars)"
        },
        message=f"KOT printed successfully in {format} format"
    )


# WebSocket Endpoints for Real-time Updates
@router.websocket("/ws/station/{restaurant_id}/{station_id}")
async def websocket_station(
    websocket: WebSocket,
    restaurant_id: str,
    station_id: str
):
    """
    WebSocket endpoint for kitchen display stations
    
    Provides real-time updates for:
    - New orders routed to this station
    - Status changes from other clients
    - Item completion updates
    - Order delays and alerts
    
    Usage:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/kds/ws/station/restaurant-id/station-id');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Update:', data);
    };
    ```
    """
    await kds_manager.connect_station(websocket, restaurant_id, station_id)
    
    try:
        while True:
            # Receive messages from client (for bidirectional communication)
            data = await websocket.receive_json()
            
            # Handle client messages
            if data.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
            elif data.get("type") == "status_update":
                # Broadcast status update to POS and other stations
                await kds_manager.notify_status_change(
                    restaurant_id=restaurant_id,
                    station_id=station_id,
                    display_id=data.get("display_id"),
                    old_status=data.get("old_status"),
                    new_status=data.get("new_status"),
                    display_data=data.get("display_data")
                )
    
    except WebSocketDisconnect:
        kds_manager.disconnect_station(websocket, restaurant_id, station_id)
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        kds_manager.disconnect_station(websocket, restaurant_id, station_id)


@router.websocket("/ws/pos/{restaurant_id}")
async def websocket_pos(
    websocket: WebSocket,
    restaurant_id: str
):
    """
    WebSocket endpoint for POS terminals
    
    Provides real-time updates about order preparation:
    - Order status changes (acknowledged, in progress, ready, completed)
    - Item-level preparation status
    - Order completion notifications
    - Delay alerts
    
    Usage:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/kds/ws/pos/restaurant-id');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'order_ready') {
            notifyServer(data.order_id);
        }
    };
    ```
    """
    await kds_manager.connect_pos(websocket, restaurant_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        kds_manager.disconnect_pos(websocket, restaurant_id)
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        kds_manager.disconnect_pos(websocket, restaurant_id)


@router.websocket("/ws/admin")
async def websocket_admin(websocket: WebSocket):
    """
    WebSocket endpoint for admin monitoring
    
    Receives all KDS updates across all restaurants and stations.
    Useful for system monitoring and analytics dashboards.
    
    Usage:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/kds/ws/admin');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        updateDashboard(data);
    };
    ```
    """
    await kds_manager.connect_admin(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except WebSocketDisconnect:
        kds_manager.disconnect_admin(websocket)
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        kds_manager.disconnect_admin(websocket)


@router.get("/ws/connections", response_model=dict)
async def get_websocket_connections(
    restaurant_id: Optional[str] = Query(None, description="Filter by restaurant"),
    current_user: User = Depends(get_current_user)
):
    """
    Get count of active WebSocket connections
    
    Returns the number of connected stations, POS terminals, and admins
    """
    connections = kds_manager.get_active_connections_count(restaurant_id)
    
    return success_response(
        data=connections,
        message="Active connections retrieved successfully"
    )
