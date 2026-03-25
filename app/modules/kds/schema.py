from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.modules.kds.model import StationType, DisplayStatus, ItemStatus


# Kitchen Station Schemas
class KitchenStationBase(BaseModel):
    """Base kitchen station schema"""
    name: str = Field(..., min_length=1, max_length=100)
    station_type: StationType
    description: Optional[str] = Field(None, max_length=500)
    floor: Optional[str] = Field(None, max_length=50)
    section: Optional[str] = Field(None, max_length=100)
    display_order: int = Field(default=0)
    color_code: Optional[str] = Field(None, max_length=7, pattern=r'^#[0-9A-Fa-f]{6}$')
    departments: Optional[List[str]] = None
    printer_tags: Optional[List[str]] = None
    max_concurrent_orders: Optional[int] = Field(None, ge=1)
    average_prep_time: Optional[int] = Field(None, ge=1)
    auto_accept_orders: bool = False
    alert_on_new_order: bool = True
    show_customer_names: bool = True
    show_table_numbers: bool = True
    assigned_staff: Optional[List[str]] = None


class KitchenStationCreate(KitchenStationBase):
    """Schema for creating a kitchen station"""
    restaurant_id: str


class KitchenStationUpdate(BaseModel):
    """Schema for updating a kitchen station"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    station_type: Optional[StationType] = None
    description: Optional[str] = Field(None, max_length=500)
    floor: Optional[str] = Field(None, max_length=50)
    section: Optional[str] = Field(None, max_length=100)
    display_order: Optional[int] = None
    color_code: Optional[str] = Field(None, max_length=7, pattern=r'^#[0-9A-Fa-f]{6}$')
    departments: Optional[List[str]] = None
    printer_tags: Optional[List[str]] = None
    max_concurrent_orders: Optional[int] = Field(None, ge=1)
    average_prep_time: Optional[int] = Field(None, ge=1)
    auto_accept_orders: Optional[bool] = None
    alert_on_new_order: Optional[bool] = None
    show_customer_names: Optional[bool] = None
    show_table_numbers: Optional[bool] = None
    is_active: Optional[bool] = None
    is_online: Optional[bool] = None
    assigned_staff: Optional[List[str]] = None


class KitchenStationResponse(KitchenStationBase):
    """Schema for kitchen station response"""
    id: str
    restaurant_id: str
    is_active: bool
    is_online: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Kitchen Display Item Schemas
class KitchenDisplayItemResponse(BaseModel):
    """Schema for kitchen display item response"""
    id: str
    display_id: str
    order_item_id: str
    product_name: str
    quantity: int
    modifiers: Optional[Dict[str, Any]]
    customization: Optional[str]
    status: ItemStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    prep_time: Optional[int]
    prepared_by: Optional[str]
    display_order: int
    is_complimentary: bool
    requires_attention: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Kitchen Display Schemas
class KitchenDisplayResponse(BaseModel):
    """Schema for kitchen display response"""
    id: str
    restaurant_id: str
    station_id: str
    order_id: str
    order_number: str
    order_type: str
    table_number: Optional[str]
    customer_name: Optional[str]
    status: DisplayStatus
    received_at: datetime
    acknowledged_at: Optional[datetime]
    started_at: Optional[datetime]
    ready_at: Optional[datetime]
    completed_at: Optional[datetime]
    priority: int
    estimated_prep_time: Optional[int]
    actual_prep_time: Optional[int]
    due_time: Optional[datetime]
    is_delayed: bool
    is_rush: bool
    alert_sent: bool
    acknowledged_by: Optional[str]
    prepared_by: Optional[str]
    special_instructions: Optional[str]
    kitchen_notes: Optional[str]
    total_items: int
    completed_items: int
    created_at: datetime
    updated_at: datetime
    items: List[KitchenDisplayItemResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


class KitchenDisplayListResponse(BaseModel):
    """Schema for paginated kitchen display list response"""
    total: int
    displays: List[KitchenDisplayResponse]
    
    model_config = ConfigDict(from_attributes=True)


class DisplayStatusUpdate(BaseModel):
    """Schema for updating display status"""
    status: DisplayStatus


class ItemStatusUpdate(BaseModel):
    """Schema for updating item status"""
    status: ItemStatus


class BumpOrderRequest(BaseModel):
    """Schema for bumping/completing an order"""
    display_id: str


class BulkItemStatusUpdate(BaseModel):
    """Schema for bulk updating item statuses"""
    item_ids: List[str]
    status: ItemStatus


class StationStatusUpdate(BaseModel):
    """Schema for updating station online/offline status"""
    is_online: bool


class KitchenPerformance(BaseModel):
    """Schema for kitchen performance metrics"""
    station_id: str
    station_name: str
    total_orders: int
    completed_orders: int
    average_prep_time: float
    on_time_percentage: float
    delayed_orders: int
    current_active_orders: int
    
    model_config = ConfigDict(from_attributes=True)
