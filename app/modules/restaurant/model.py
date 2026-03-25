"""
Multi-tenant Restaurant models for SaaS platform
"""
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, List
import uuid
import enum

from app.core.database import Base


class BusinessType(str, enum.Enum):
    """Restaurant business types"""
    CAFE = "cafe"
    RESTAURANT = "restaurant"
    BAR = "bar"
    FOOD_TRUCK = "food_truck"
    BAKERY = "bakery"
    CLOUD_KITCHEN = "cloud_kitchen"
    QUICK_SERVICE = "quick_service"
    FINE_DINING = "fine_dining"


class SubscriptionPlanType(str, enum.Enum):
    """Subscription plan types"""
    TRIAL = "trial"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PAST_DUE = "past_due"


class InvoiceStatus(str, enum.Enum):
    """Invoice status"""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class Restaurant(Base):
    """
    Core tenant model representing each restaurant business.
    Each restaurant is a separate tenant with isolated data.
    """
    __tablename__ = "restaurants"
    
    # Identity
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    
    # Business Information
    business_name: Mapped[str] = mapped_column(String(200), nullable=False)
    business_type: Mapped[Optional[BusinessType]] = mapped_column(SQLEnum(BusinessType), nullable=True)
    cuisine_type: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # ["italian", "mexican", "asian"]
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Contact Information
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    alternate_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default='India', nullable=False)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    latitude: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    longitude: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # India-specific fields
    gstin: Mapped[Optional[str]] = mapped_column(String(15), nullable=True, index=True)  # GST Number
    fssai_license: Mapped[Optional[str]] = mapped_column(String(14), nullable=True)  # FSSAI License
    pan_number: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # PAN Card
    
    # Branding
    logo: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    banner_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    primary_color: Mapped[str] = mapped_column(String(7), default='#00A19D', nullable=False)
    accent_color: Mapped[str] = mapped_column(String(7), default='#FF6D00', nullable=False)
    
    # Settings
    timezone: Mapped[str] = mapped_column(String(50), default='Asia/Kolkata', nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default='INR', nullable=False)
    language: Mapped[str] = mapped_column(String(5), default='en', nullable=False)
    date_format: Mapped[str] = mapped_column(String(20), default='DD/MM/YYYY', nullable=False)
    time_format: Mapped[str] = mapped_column(String(10), default='24h', nullable=False)
    
    # Tax Settings (India-specific)
    enable_gst: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    cgst_rate: Mapped[Optional[float]] = mapped_column(nullable=True)  # Central GST
    sgst_rate: Mapped[Optional[float]] = mapped_column(nullable=True)  # State GST
    igst_rate: Mapped[Optional[float]] = mapped_column(nullable=True)  # Integrated GST
    service_charge_percentage: Mapped[Optional[float]] = mapped_column(nullable=True)
    vat_rate: Mapped[Optional[float]] = mapped_column(nullable=True)  # VAT for other countries
    sales_tax_rate: Mapped[Optional[float]] = mapped_column(nullable=True)  # Sales tax
    tax_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Generic tax ID
    
    # Operating Hours Settings
    opening_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # e.g., "09:00"
    closing_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # e.g., "22:00"
    is_24_hours: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    operating_days: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"monday": {"open": "09:00", "close": "22:00", "is_open": true}, ...}
    holiday_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    special_hours: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Special hours for holidays/events
    
    # Payment Methods Settings
    payment_methods_allowed: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # ["cash", "card", "upi", "wallet", "online"]
    cash_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    card_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    upi_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    wallet_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    online_payment_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Payment Gateway Settings
    payment_gateway: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # "razorpay", "stripe", "paypal"
    payment_gateway_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # API key (encrypted)
    payment_gateway_secret: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # API secret (encrypted)
    
    # Order Settings
    enable_online_ordering: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    enable_table_booking: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    enable_delivery: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    enable_takeaway: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_dine_in: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Delivery Settings
    delivery_radius: Mapped[Optional[float]] = mapped_column(nullable=True)  # in km
    delivery_charge: Mapped[Optional[float]] = mapped_column(nullable=True)  # base delivery charge
    minimum_order_value: Mapped[Optional[float]] = mapped_column(nullable=True)  # minimum order for delivery
    free_delivery_above: Mapped[Optional[float]] = mapped_column(nullable=True)  # free delivery threshold
    
    # Restaurant Capacity Settings
    total_tables: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_seats: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_party_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Notification Settings
    enable_email_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_sms_notifications: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    enable_push_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notification_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notification_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Receipt & Invoice Settings
    receipt_header: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    receipt_footer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    invoice_prefix: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # e.g., "INV-"
    invoice_counter: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    enable_auto_print: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Social Media & Website
    website_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    facebook_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    instagram_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    twitter_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Additional Settings
    allow_tips: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    default_tip_percentage: Mapped[Optional[float]] = mapped_column(nullable=True)
    enable_loyalty_program: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    loyalty_points_per_currency: Mapped[Optional[float]] = mapped_column(nullable=True)  # e.g., 1 point per 100 INR
    
    # Kitchen Settings
    enable_kot: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # Kitchen Order Ticket
    enable_kds: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Kitchen Display System
    auto_accept_orders: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    preparation_time_buffer: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # minutes
    
    # Subscription & Billing
    subscription_plan: Mapped[SubscriptionPlanType] = mapped_column(
        SQLEnum(SubscriptionPlanType),
        default=SubscriptionPlanType.TRIAL,
        nullable=False,
        index=True
    )
    subscription_status: Mapped[SubscriptionStatus] = mapped_column(
        SQLEnum(SubscriptionStatus),
        default=SubscriptionStatus.ACTIVE,
        nullable=False,
        index=True
    )
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    subscription_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    billing_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Plan Limits (based on subscription)
    max_users: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    max_products: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    max_orders_per_month: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    max_locations: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Current Usage (for limit enforcement)
    current_users: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_products: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_orders_this_month: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Features Enabled (based on plan)
    features: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # ["qr_ordering", "analytics", "loyalty"]
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    suspension_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    onboarding_step: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    last_activity: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # Soft delete
    
    # Relationships
    roles: Mapped[List["Role"]] = relationship("Role", back_populates="restaurant")
    staff: Mapped[List["Staff"]] = relationship("Staff", back_populates="restaurant")
    shifts: Mapped[List["Shift"]] = relationship("Shift", back_populates="restaurant")
    attendance_records: Mapped[List["Attendance"]] = relationship("Attendance", back_populates="restaurant")
    leave_applications: Mapped[List["LeaveApplication"]] = relationship("LeaveApplication", back_populates="restaurant")
    
    def __repr__(self):
        return f"<Restaurant(id={self.id}, name='{self.name}', slug='{self.slug}', plan='{self.subscription_plan}')>"


class RestaurantOwner(Base):
    """
    Links users to restaurants they own or co-own.
    A user can own multiple restaurants.
    """
    __tablename__ = "restaurant_owners"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Role & Permissions
    role: Mapped[str] = mapped_column(String(20), default='owner', nullable=False)  # owner, co_owner
    permissions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Invitation
    invited_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    invitation_accepted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Metadata
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<RestaurantOwner(restaurant_id={self.restaurant_id}, user_id={self.user_id}, role='{self.role}')>"


class SubscriptionPlan(Base):
    """
    Defines available subscription plans and their features.
    """
    __tablename__ = "subscription_plans"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Plan Identity
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tagline: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Pricing (in paise for India, cents for others)
    price_monthly: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    price_yearly: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    discount_yearly: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # percentage
    
    # Limits
    max_users: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    max_products: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    max_orders_per_month: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    max_locations: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_storage_gb: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Features
    features: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Display
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    badge: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Trial
    trial_days: Mapped[int] = mapped_column(Integer, default=14, nullable=False)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<SubscriptionPlan(name='{self.name}', display_name='{self.display_name}')>"


class Subscription(Base):
    """
    Tracks subscription history and billing for each restaurant.
    """
    __tablename__ = "subscriptions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Plan Details
    plan: Mapped[SubscriptionPlanType] = mapped_column(
        SQLEnum(SubscriptionPlanType),
        nullable=False,
        index=True
    )
    plan_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(
        SQLEnum(SubscriptionStatus),
        nullable=False,
        index=True
    )
    
    # Pricing (in paise/cents)
    price_per_month: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    price_per_year: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    billing_cycle: Mapped[str] = mapped_column(String(20), default='monthly', nullable=False)
    
    # Dates
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    current_period_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    current_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    trial_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Payment
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    payment_gateway_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    payment_gateway_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    last_payment_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_payment_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Cancellation
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cancelled_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Metadata
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<Subscription(id={self.id}, restaurant_id={self.restaurant_id}, plan='{self.plan}', status='{self.status}')>"


class Invoice(Base):
    """
    Billing invoices for subscriptions.
    """
    __tablename__ = "invoices"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Invoice Details
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # in paise/cents
    tax: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default='INR', nullable=False)
    
    # India-specific tax breakdown
    cgst_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sgst_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    igst_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Status
    status: Mapped[InvoiceStatus] = mapped_column(
        SQLEnum(InvoiceStatus),
        default=InvoiceStatus.PENDING,
        nullable=False
    )
    
    # Dates
    invoice_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Payment
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    payment_gateway_invoice_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    payment_gateway_charge_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # PDF
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<Invoice(invoice_number='{self.invoice_number}', amount={self.amount}, status='{self.status}')>"


class RestaurantInvitation(Base):
    """
    Pending invitations to join a restaurant team.
    """
    __tablename__ = "restaurant_invitations"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Invitee Information
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Invitation Details
    token: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    invited_by: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default='pending', nullable=False)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    accepted_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Expiration
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<RestaurantInvitation(email='{self.email}', restaurant_id={self.restaurant_id}, status='{self.status}')>"
