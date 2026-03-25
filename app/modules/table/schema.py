from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from app.modules.table.model import TableStatus


class TableBase(BaseModel):
    """Base table schema"""
    restaurant_id: str
    table_number: str = Field(..., min_length=1, max_length=50)
    table_name: Optional[str] = Field(None, max_length=100)
    capacity: int = Field(..., ge=1, le=100)
    min_capacity: Optional[int] = Field(None, ge=1)
    floor: Optional[str] = Field(None, max_length=50)
    section: Optional[str] = Field(None, max_length=100)
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    image: Optional[str] = Field(None, max_length=500)
    qr_code: Optional[str] = Field(None, max_length=500)
    status: Optional[TableStatus] = TableStatus.AVAILABLE
    is_bookable: Optional[bool] = True
    is_outdoor: Optional[bool] = False
    is_accessible: Optional[bool] = True
    has_power_outlet: Optional[bool] = False
    minimum_spend: Optional[int] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=1000)


class TableCreate(TableBase):
    """Schema for creating a table"""
    pass


class TableUpdate(BaseModel):
    """Schema for updating a table"""
    table_number: Optional[str] = Field(None, min_length=1, max_length=50)
    table_name: Optional[str] = Field(None, max_length=100)
    capacity: Optional[int] = Field(None, ge=1, le=100)
    min_capacity: Optional[int] = Field(None, ge=1)
    floor: Optional[str] = Field(None, max_length=50)
    section: Optional[str] = Field(None, max_length=100)
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    image: Optional[str] = Field(None, max_length=500)
    qr_code: Optional[str] = Field(None, max_length=500)
    status: Optional[TableStatus] = None
    is_active: Optional[bool] = None
    is_bookable: Optional[bool] = None
    is_outdoor: Optional[bool] = None
    is_accessible: Optional[bool] = None
    has_power_outlet: Optional[bool] = None
    minimum_spend: Optional[int] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=1000)


class TableResponse(TableBase):
    """Schema for table response"""
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TableListResponse(BaseModel):
    """Schema for paginated table list response"""
    total: int
    tables: list[TableResponse]
    
    model_config = ConfigDict(from_attributes=True)


class TableStatusUpdate(BaseModel):
    """Schema for updating table status only"""
    status: TableStatus
