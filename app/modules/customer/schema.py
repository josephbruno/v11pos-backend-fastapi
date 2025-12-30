from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional


class CustomerBase(BaseModel):
    """Base customer schema"""
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    notes: Optional[str] = Field(None, max_length=1000)


class CustomerCreate(CustomerBase):
    """Schema for creating a customer"""
    pass


class CustomerUpdate(BaseModel):
    """Schema for updating a customer"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    notes: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None


class CustomerResponse(CustomerBase):
    """Schema for customer response"""
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CustomerListResponse(BaseModel):
    """Schema for paginated customer list response"""
    total: int
    customers: list[CustomerResponse]
    
    model_config = ConfigDict(from_attributes=True)
