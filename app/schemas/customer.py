"""
Customer and Loyalty Pydantic schemas
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime
import re


# Customer Schemas
class CustomerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=10, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        # Remove non-numeric characters
        phone = re.sub(r'\D', '', v)
        if len(phone) < 10:
            raise ValueError('Phone number must be at least 10 digits')
        return v


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    is_blacklisted: Optional[bool] = None


class CustomerResponse(CustomerBase):
    id: str
    loyalty_points: int
    total_spent: int
    visit_count: int
    last_visit: Optional[datetime] = None
    is_blacklisted: bool
    created_at: datetime
    updated_at: datetime
    
    @property
    def total_spent_display(self) -> float:
        return self.total_spent / 100
    
    class Config:
        from_attributes = True


# Customer Tag Schemas
class CustomerTagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field(default='#00A19D', pattern=r'^#[0-9A-Fa-f]{6}$')
    benefits: List[str] = Field(default_factory=list)
    discount_percentage: int = Field(default=0, ge=0, le=10000)
    priority: int = Field(default=0, ge=0)


class CustomerTagCreate(CustomerTagBase):
    pass


class CustomerTagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    benefits: Optional[List[str]] = None
    discount_percentage: Optional[int] = Field(None, ge=0, le=10000)
    priority: Optional[int] = Field(None, ge=0)


class CustomerTagResponse(CustomerTagBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    @property
    def discount_percentage_display(self) -> float:
        return self.discount_percentage / 100
    
    class Config:
        from_attributes = True


# Loyalty Rule Schemas
class LoyaltyRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    earn_rate: int = Field(default=100, ge=0)
    redeem_rate: int = Field(default=100, ge=0)
    min_redeem_points: int = Field(default=100, ge=0)
    max_redeem_percentage: int = Field(default=50, ge=0, le=100)
    expiry_days: Optional[int] = Field(None, ge=1)
    active: bool = True
    priority: int = Field(default=0, ge=0)
    applicable_tags: Optional[List[str]] = None


class LoyaltyRuleCreate(LoyaltyRuleBase):
    pass


class LoyaltyRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    earn_rate: Optional[int] = Field(None, ge=0)
    redeem_rate: Optional[int] = Field(None, ge=0)
    min_redeem_points: Optional[int] = Field(None, ge=0)
    max_redeem_percentage: Optional[int] = Field(None, ge=0, le=100)
    expiry_days: Optional[int] = Field(None, ge=1)
    active: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0)
    applicable_tags: Optional[List[str]] = None


class LoyaltyRuleResponse(LoyaltyRuleBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Loyalty Transaction Schemas
class LoyaltyTransactionResponse(BaseModel):
    id: str
    customer_id: str
    order_id: Optional[str] = None
    points: int
    operation: str
    reason: Optional[str] = None
    balance_before: int
    balance_after: int
    expires_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
