"""
Tax and Settings Pydantic schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, List
from datetime import datetime
from app.enums import TaxApplicableOn


# Tax Rule Schemas
class TaxRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., min_length=1, max_length=50)
    percentage: int = Field(..., ge=0, le=10000)
    applicable_on: TaxApplicableOn = TaxApplicableOn.ALL
    categories: Optional[List[str]] = None
    min_amount: Optional[int] = Field(None, ge=0)
    max_amount: Optional[int] = Field(None, ge=0)
    is_compounded: bool = False
    priority: int = Field(default=0, ge=0)
    active: bool = True


class TaxRuleCreate(TaxRuleBase):
    pass


class TaxRuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[str] = Field(None, min_length=1, max_length=50)
    percentage: Optional[int] = Field(None, ge=0, le=10000)
    applicable_on: Optional[TaxApplicableOn] = None
    categories: Optional[List[str]] = None
    min_amount: Optional[int] = Field(None, ge=0)
    max_amount: Optional[int] = Field(None, ge=0)
    is_compounded: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0)
    active: Optional[bool] = None


class TaxRuleResponse(TaxRuleBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    @property
    def percentage_display(self) -> float:
        return self.percentage / 100
    
    class Config:
        from_attributes = True


# Settings Schemas
class SettingsBase(BaseModel):
    restaurant_name: str = Field(..., min_length=1, max_length=200)
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    logo: Optional[str] = None
    currency: str = Field(default='USD', min_length=3, max_length=3)
    timezone: str = Field(default='UTC', min_length=1, max_length=50)
    language: str = Field(default='en', min_length=2, max_length=5)
    tax_rate: int = Field(default=0, ge=0, le=10000)
    service_charge: int = Field(default=0, ge=0, le=10000)
    enable_tipping: bool = True
    default_tip_percentages: List[int] = Field(default_factory=lambda: [10, 15, 20])
    print_kot_automatically: bool = True
    auto_print_receipt: bool = False
    email_notifications: bool = True
    sms_notifications: bool = False
    low_stock_alerts: bool = True
    business_hours: Optional[Dict] = None


class SettingsCreate(SettingsBase):
    pass


class SettingsUpdate(BaseModel):
    restaurant_name: Optional[str] = Field(None, min_length=1, max_length=200)
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    logo: Optional[str] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    timezone: Optional[str] = Field(None, min_length=1, max_length=50)
    language: Optional[str] = Field(None, min_length=2, max_length=5)
    tax_rate: Optional[int] = Field(None, ge=0, le=10000)
    service_charge: Optional[int] = Field(None, ge=0, le=10000)
    enable_tipping: Optional[bool] = None
    default_tip_percentages: Optional[List[int]] = None
    print_kot_automatically: Optional[bool] = None
    auto_print_receipt: Optional[bool] = None
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    low_stock_alerts: Optional[bool] = None
    business_hours: Optional[Dict] = None


class SettingsResponse(SettingsBase):
    id: str
    updated_at: datetime
    
    @property
    def tax_rate_display(self) -> float:
        return self.tax_rate / 100
    
    @property
    def service_charge_display(self) -> float:
        return self.service_charge / 100
    
    class Config:
        from_attributes = True
