from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum


class BusinessType(str, Enum):
    """Restaurant business types"""
    CAFE = "cafe"
    RESTAURANT = "restaurant"
    BAR = "bar"
    FOOD_TRUCK = "food_truck"
    BAKERY = "bakery"
    CLOUD_KITCHEN = "cloud_kitchen"
    QUICK_SERVICE = "quick_service"
    FINE_DINING = "fine_dining"


class SubscriptionPlanType(str, Enum):
    """Subscription plan types"""
    TRIAL = "trial"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    """Subscription status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PAST_DUE = "past_due"


class InvoiceStatus(str, Enum):
    """Invoice status"""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


# Restaurant Schemas

class RestaurantBase(BaseModel):
    """Base restaurant schema"""
    name: str = Field(..., min_length=2, max_length=200)
    business_name: str = Field(..., min_length=2, max_length=200)
    business_type: Optional[BusinessType] = None
    cuisine_type: Optional[List[str]] = None
    description: Optional[str] = None
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    alternate_phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    postal_code: Optional[str] = None
    
    # India-specific
    gstin: Optional[str] = Field(None, max_length=15)
    fssai_license: Optional[str] = Field(None, max_length=14)
    pan_number: Optional[str] = Field(None, max_length=10)
    
    # Settings
    timezone: str = "Asia/Kolkata"
    currency: str = "INR"
    language: str = "en"
    
    # Tax settings
    enable_gst: bool = True
    cgst_rate: Optional[float] = None
    sgst_rate: Optional[float] = None
    igst_rate: Optional[float] = None
    service_charge_percentage: Optional[float] = None
    vat_rate: Optional[float] = None
    sales_tax_rate: Optional[float] = None
    tax_number: Optional[str] = None
    
    # Operating hours
    opening_time: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")  # HH:MM format
    closing_time: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")  # HH:MM format
    is_24_hours: bool = False
    operating_days: Optional[Dict] = None
    holiday_mode: bool = False
    special_hours: Optional[Dict] = None
    
    # Payment methods
    payment_methods_allowed: Optional[List[str]] = None  # ["cash", "card", "upi", "wallet", "online"]
    cash_enabled: bool = True
    card_enabled: bool = True
    upi_enabled: bool = True
    wallet_enabled: bool = False
    online_payment_enabled: bool = False
    payment_gateway: Optional[str] = None
    
    # Order settings
    enable_online_ordering: bool = False
    enable_table_booking: bool = False
    enable_delivery: bool = False
    enable_takeaway: bool = True
    enable_dine_in: bool = True
    
    # Delivery settings
    delivery_radius: Optional[float] = None
    delivery_charge: Optional[float] = None
    minimum_order_value: Optional[float] = None
    free_delivery_above: Optional[float] = None
    
    # Capacity
    total_tables: Optional[int] = None
    total_seats: Optional[int] = None
    max_party_size: Optional[int] = None
    
    # Notifications
    enable_email_notifications: bool = True
    enable_sms_notifications: bool = False
    enable_push_notifications: bool = True
    notification_email: Optional[EmailStr] = None
    notification_phone: Optional[str] = None
    
    # Receipt settings
    receipt_header: Optional[str] = None
    receipt_footer: Optional[str] = None
    invoice_prefix: Optional[str] = None
    enable_auto_print: bool = False
    
    # Social media
    website_url: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    twitter_url: Optional[str] = None
    
    # Additional settings
    allow_tips: bool = True
    default_tip_percentage: Optional[float] = None
    enable_loyalty_program: bool = False
    loyalty_points_per_currency: Optional[float] = None
    
    # Kitchen settings
    enable_kot: bool = True
    enable_kds: bool = False
    auto_accept_orders: bool = False
    preparation_time_buffer: Optional[int] = None


class RestaurantCreate(RestaurantBase):
    """Schema for creating a restaurant"""
    slug: str = Field(..., min_length=3, max_length=200, pattern="^[a-z0-9-]+$")
    
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v):
        if not v.replace('-', '').isalnum():
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v.lower()


class RestaurantUpdate(BaseModel):
    """Schema for updating a restaurant"""
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    business_name: Optional[str] = Field(None, min_length=2, max_length=200)
    business_type: Optional[BusinessType] = None
    cuisine_type: Optional[List[str]] = None
    description: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    alternate_phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    gstin: Optional[str] = None
    fssai_license: Optional[str] = None
    pan_number: Optional[str] = None
    logo: Optional[str] = None
    banner_image: Optional[str] = None
    primary_color: Optional[str] = None
    accent_color: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None
    enable_gst: Optional[bool] = None
    cgst_rate: Optional[float] = None
    sgst_rate: Optional[float] = None
    igst_rate: Optional[float] = None
    service_charge_percentage: Optional[float] = None
    vat_rate: Optional[float] = None
    sales_tax_rate: Optional[float] = None
    tax_number: Optional[str] = None
    
    # Operating hours
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    is_24_hours: Optional[bool] = None
    operating_days: Optional[Dict] = None
    holiday_mode: Optional[bool] = None
    special_hours: Optional[Dict] = None
    
    # Payment methods
    payment_methods_allowed: Optional[List[str]] = None
    cash_enabled: Optional[bool] = None
    card_enabled: Optional[bool] = None
    upi_enabled: Optional[bool] = None
    wallet_enabled: Optional[bool] = None
    online_payment_enabled: Optional[bool] = None
    payment_gateway: Optional[str] = None
    
    # Order settings
    enable_online_ordering: Optional[bool] = None
    enable_table_booking: Optional[bool] = None
    enable_delivery: Optional[bool] = None
    enable_takeaway: Optional[bool] = None
    enable_dine_in: Optional[bool] = None
    
    # Delivery settings
    delivery_radius: Optional[float] = None
    delivery_charge: Optional[float] = None
    minimum_order_value: Optional[float] = None
    free_delivery_above: Optional[float] = None
    
    # Capacity
    total_tables: Optional[int] = None
    total_seats: Optional[int] = None
    max_party_size: Optional[int] = None
    
    # Notifications
    enable_email_notifications: Optional[bool] = None
    enable_sms_notifications: Optional[bool] = None
    enable_push_notifications: Optional[bool] = None
    notification_email: Optional[EmailStr] = None
    notification_phone: Optional[str] = None
    
    # Receipt settings
    receipt_header: Optional[str] = None
    receipt_footer: Optional[str] = None
    invoice_prefix: Optional[str] = None
    enable_auto_print: Optional[bool] = None
    
    # Social media
    website_url: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    twitter_url: Optional[str] = None
    
    # Additional settings
    allow_tips: Optional[bool] = None
    default_tip_percentage: Optional[float] = None
    enable_loyalty_program: Optional[bool] = None
    loyalty_points_per_currency: Optional[float] = None
    
    # Kitchen settings
    enable_kot: Optional[bool] = None
    enable_kds: Optional[bool] = None
    auto_accept_orders: Optional[bool] = None
    preparation_time_buffer: Optional[int] = None


class RestaurantResponse(BaseModel):
    """Schema for restaurant response"""
    id: str
    name: str
    slug: str
    business_name: str
    business_type: Optional[BusinessType]
    cuisine_type: Optional[List[str]]
    description: Optional[str]
    email: str
    phone: str
    alternate_phone: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: str
    postal_code: Optional[str]
    gstin: Optional[str]
    fssai_license: Optional[str]
    pan_number: Optional[str]
    logo: Optional[str]
    banner_image: Optional[str]
    primary_color: str
    accent_color: str
    timezone: str
    currency: str
    language: str
    enable_gst: bool
    cgst_rate: Optional[float]
    sgst_rate: Optional[float]
    igst_rate: Optional[float]
    service_charge_percentage: Optional[float]
    vat_rate: Optional[float]
    sales_tax_rate: Optional[float]
    tax_number: Optional[str]
    
    # Operating hours
    opening_time: Optional[str]
    closing_time: Optional[str]
    is_24_hours: bool
    operating_days: Optional[Dict]
    holiday_mode: bool
    special_hours: Optional[Dict]
    
    # Payment methods
    payment_methods_allowed: Optional[List[str]]
    cash_enabled: bool
    card_enabled: bool
    upi_enabled: bool
    wallet_enabled: bool
    online_payment_enabled: bool
    payment_gateway: Optional[str]
    
    # Order settings
    enable_online_ordering: bool
    enable_table_booking: bool
    enable_delivery: bool
    enable_takeaway: bool
    enable_dine_in: bool
    
    # Delivery settings
    delivery_radius: Optional[float]
    delivery_charge: Optional[float]
    minimum_order_value: Optional[float]
    free_delivery_above: Optional[float]
    
    # Capacity
    total_tables: Optional[int]
    total_seats: Optional[int]
    max_party_size: Optional[int]
    
    # Notifications
    enable_email_notifications: bool
    enable_sms_notifications: bool
    enable_push_notifications: bool
    notification_email: Optional[str]
    notification_phone: Optional[str]
    
    # Receipt settings
    receipt_header: Optional[str]
    receipt_footer: Optional[str]
    invoice_prefix: Optional[str]
    invoice_counter: int
    enable_auto_print: bool
    
    # Social media
    website_url: Optional[str]
    facebook_url: Optional[str]
    instagram_url: Optional[str]
    twitter_url: Optional[str]
    
    # Additional settings
    allow_tips: bool
    default_tip_percentage: Optional[float]
    enable_loyalty_program: bool
    loyalty_points_per_currency: Optional[float]
    
    # Kitchen settings
    enable_kot: bool
    enable_kds: bool
    auto_accept_orders: bool
    preparation_time_buffer: Optional[int]
    
    subscription_plan: SubscriptionPlanType
    subscription_status: SubscriptionStatus
    trial_ends_at: Optional[datetime]
    max_users: int
    max_products: int
    max_orders_per_month: int
    current_users: int
    current_products: int
    current_orders_this_month: int
    features: Optional[List[str]]
    is_active: bool
    is_verified: bool
    is_suspended: bool
    onboarding_completed: bool
    onboarding_step: int
    created_at: datetime
    updated_at: datetime
    last_activity: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


# Subscription Plan Schemas

class SubscriptionPlanBase(BaseModel):
    """Base subscription plan schema"""
    name: str = Field(..., min_length=2, max_length=50)
    display_name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    tagline: Optional[str] = None
    price_monthly: int = 0
    price_yearly: int = 0
    discount_yearly: int = 0
    max_users: int = 5
    max_products: int = 100
    max_orders_per_month: int = 1000
    max_locations: int = 1
    max_storage_gb: int = 1
    features: Optional[List[str]] = None
    trial_days: int = 14


class SubscriptionPlanCreate(SubscriptionPlanBase):
    """Schema for creating a subscription plan"""
    pass


class SubscriptionPlanUpdate(BaseModel):
    """Schema for updating a subscription plan"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    tagline: Optional[str] = None
    price_monthly: Optional[int] = None
    price_yearly: Optional[int] = None
    discount_yearly: Optional[int] = None
    max_users: Optional[int] = None
    max_products: Optional[int] = None
    max_orders_per_month: Optional[int] = None
    max_locations: Optional[int] = None
    max_storage_gb: Optional[int] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    is_featured: Optional[bool] = None
    badge: Optional[str] = None
    trial_days: Optional[int] = None


class SubscriptionPlanResponse(BaseModel):
    """Schema for subscription plan response"""
    id: str
    name: str
    display_name: str
    description: Optional[str]
    tagline: Optional[str]
    price_monthly: int
    price_yearly: int
    discount_yearly: int
    max_users: int
    max_products: int
    max_orders_per_month: int
    max_locations: int
    max_storage_gb: int
    features: Optional[List[str]]
    is_active: bool
    is_public: bool
    is_featured: bool
    sort_order: int
    badge: Optional[str]
    trial_days: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Subscription Schemas

class SubscriptionCreate(BaseModel):
    """Schema for creating a subscription"""
    restaurant_id: str
    plan: SubscriptionPlanType
    plan_name: str
    billing_cycle: str = "monthly"
    payment_method: Optional[str] = None


class SubscriptionUpdate(BaseModel):
    """Schema for updating a subscription"""
    status: Optional[SubscriptionStatus] = None
    cancel_at_period_end: Optional[bool] = None
    cancellation_reason: Optional[str] = None


class SubscriptionResponse(BaseModel):
    """Schema for subscription response"""
    id: str
    restaurant_id: str
    plan: SubscriptionPlanType
    plan_name: str
    status: SubscriptionStatus
    price_per_month: int
    price_per_year: int
    billing_cycle: str
    started_at: datetime
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    trial_end: Optional[datetime]
    cancelled_at: Optional[datetime]
    cancel_at_period_end: bool
    cancellation_reason: Optional[str]
    payment_method: Optional[str]
    next_payment_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Invoice Schemas

class InvoiceCreate(BaseModel):
    """Schema for creating an invoice"""
    subscription_id: str
    restaurant_id: str
    amount: int
    tax: int = 0
    total: int
    currency: str = "INR"
    cgst_amount: Optional[int] = None
    sgst_amount: Optional[int] = None
    igst_amount: Optional[int] = None
    description: Optional[str] = None


class InvoiceResponse(BaseModel):
    """Schema for invoice response"""
    id: str
    subscription_id: str
    restaurant_id: str
    invoice_number: str
    amount: int
    tax: int
    total: int
    currency: str
    cgst_amount: Optional[int]
    sgst_amount: Optional[int]
    igst_amount: Optional[int]
    status: InvoiceStatus
    invoice_date: datetime
    due_date: Optional[datetime]
    paid_at: Optional[datetime]
    payment_method: Optional[str]
    pdf_url: Optional[str]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Restaurant Invitation Schemas

class RestaurantInvitationCreate(BaseModel):
    """Schema for creating a restaurant invitation"""
    email: EmailStr
    name: Optional[str] = None
    role: str = Field(..., pattern="^(manager|staff|cashier)$")
    message: Optional[str] = None


class RestaurantInvitationResponse(BaseModel):
    """Schema for restaurant invitation response"""
    id: str
    restaurant_id: str
    email: str
    name: Optional[str]
    role: str
    token: str
    invited_by: int
    message: Optional[str]
    status: str
    accepted_at: Optional[datetime]
    expires_at: datetime
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Restaurant Owner Schemas

class RestaurantOwnerResponse(BaseModel):
    """Schema for restaurant owner response"""
    id: str
    restaurant_id: str
    user_id: str
    role: str
    permissions: Optional[List[str]]
    invitation_accepted: bool
    is_active: bool
    joined_at: datetime
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
