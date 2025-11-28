"""
User and staff schemas
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
import uuid
from app.enums import UserRole, UserStatus, DayOfWeek


class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=1, max_length=20)
    role: UserRole = UserRole.STAFF
    status: UserStatus = UserStatus.ACTIVE
    avatar: Optional[str] = Field(None, max_length=500)
    permissions: List[str] = []


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    avatar: Optional[str] = None
    permissions: Optional[List[str]] = None
    password: Optional[str] = Field(None, min_length=8)


class UserResponse(UserBase):
    id: uuid.UUID
    join_date: datetime
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ShiftScheduleBase(BaseModel):
    day: DayOfWeek
    start_time: str = Field(..., pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    end_time: str = Field(..., pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    position: str = Field(..., min_length=1, max_length=50)
    is_active: bool = True


class ShiftScheduleCreate(ShiftScheduleBase):
    user_id: uuid.UUID


class ShiftScheduleUpdate(BaseModel):
    day: Optional[DayOfWeek] = None
    start_time: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    end_time: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    position: Optional[str] = None
    is_active: Optional[bool] = None


class ShiftScheduleResponse(ShiftScheduleBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StaffPerformanceResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    orders_handled: int
    total_revenue: int  # in cents
    avg_order_value: int  # in cents
    customer_rating: int  # rating * 100
    punctuality_score: int
    last_calculated: datetime
    
    @property
    def total_revenue_display(self) -> float:
        return self.total_revenue / 100
    
    @property
    def avg_order_value_display(self) -> float:
        return self.avg_order_value / 100
    
    @property
    def customer_rating_display(self) -> float:
        return self.customer_rating / 100
    
    class Config:
        from_attributes = True
