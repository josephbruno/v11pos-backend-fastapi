"""
Multi-tenant Restaurant models for SaaS platform
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Restaurant(Base):
    """
    Core tenant model representing each restaurant business.
    Each restaurant is a separate tenant with isolated data.
    """
    __tablename__ = "restaurants"
    
    # Identity
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False, index=True)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    
    # Business Information
    business_name = Column(String(200), nullable=False)
    business_type = Column(String(50))  # cafe, restaurant, bar, food_truck, bakery
    cuisine_type = Column(JSON)  # ["italian", "mexican", "asian"]
    description = Column(Text)
    
    # Contact Information
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100), default='USA')
    postal_code = Column(String(20))
    latitude = Column(String(20))
    longitude = Column(String(20))
    
    # Branding
    logo = Column(String(500))
    banner_image = Column(String(500))
    primary_color = Column(String(7), default='#00A19D')
    accent_color = Column(String(7), default='#FF6D00')
    
    # Settings
    timezone = Column(String(50), default='UTC')
    currency = Column(String(3), default='USD')
    language = Column(String(5), default='en')
    date_format = Column(String(20), default='MM/DD/YYYY')
    time_format = Column(String(10), default='12h')
    
    # Subscription & Billing
    subscription_plan = Column(String(50), default='trial', index=True)  # trial, basic, pro, enterprise
    subscription_status = Column(String(20), default='active', index=True)  # active, suspended, cancelled, expired
    trial_ends_at = Column(DateTime(timezone=True))
    subscription_started_at = Column(DateTime(timezone=True))
    billing_email = Column(String(255))
    
    # Plan Limits (based on subscription)
    max_users = Column(Integer, default=2)
    max_products = Column(Integer, default=50)
    max_orders_per_month = Column(Integer, default=100)
    max_locations = Column(Integer, default=1)
    
    # Current Usage (for limit enforcement)
    current_users = Column(Integer, default=0)
    current_products = Column(Integer, default=0)
    current_orders_this_month = Column(Integer, default=0)
    
    # Features Enabled (based on plan)
    features = Column(JSON, default=list)  # ["qr_ordering", "analytics", "loyalty", "multi_location"]
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    is_suspended = Column(Boolean, nullable=False, default=False)
    suspension_reason = Column(Text)
    onboarding_completed = Column(Boolean, nullable=False, default=False)
    onboarding_step = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    last_activity = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True))  # Soft delete
    
    # Relationships
    users = relationship("User", back_populates="restaurant", cascade="all, delete-orphan")
    owners = relationship("RestaurantOwner", back_populates="restaurant", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="restaurant", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="restaurant", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="restaurant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="restaurant", cascade="all, delete-orphan")
    qr_tables = relationship("QRTable", back_populates="restaurant", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="restaurant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Restaurant(id={self.id}, name='{self.name}', slug='{self.slug}', plan='{self.subscription_plan}')>"


class RestaurantOwner(Base):
    """
    Links users to restaurants they own or co-own.
    A user can own multiple restaurants.
    """
    __tablename__ = "restaurant_owners"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Role & Permissions
    role = Column(String(20), nullable=False, default='owner')  # owner, co_owner
    permissions = Column(JSON, default=list)  # Custom permissions for this restaurant
    
    # Invitation
    invited_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    invitation_accepted = Column(Boolean, default=True)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Metadata
    joined_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="owners")
    user = relationship("User", foreign_keys=[user_id])
    invited_by_user = relationship("User", foreign_keys=[invited_by])
    
    def __repr__(self):
        return f"<RestaurantOwner(restaurant_id={self.restaurant_id}, user_id={self.user_id}, role='{self.role}')>"


class Subscription(Base):
    """
    Tracks subscription history and billing for each restaurant.
    """
    __tablename__ = "subscriptions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Plan Details
    plan = Column(String(50), nullable=False, index=True)  # trial, basic, pro, enterprise
    plan_name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, index=True)  # active, cancelled, expired, suspended, past_due
    
    # Pricing
    price_per_month = Column(Integer, default=0)  # in cents
    price_per_year = Column(Integer, default=0)  # in cents
    billing_cycle = Column(String(20), default='monthly')  # monthly, yearly
    
    # Dates
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    current_period_start = Column(DateTime(timezone=True))
    current_period_end = Column(DateTime(timezone=True))
    trial_end = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))
    
    # Payment
    payment_method = Column(String(50))  # stripe, paypal, manual
    payment_gateway_customer_id = Column(String(255))
    payment_gateway_subscription_id = Column(String(255), index=True)
    last_payment_date = Column(DateTime(timezone=True))
    next_payment_date = Column(DateTime(timezone=True))
    
    # Cancellation
    cancel_at_period_end = Column(Boolean, default=False)
    cancellation_reason = Column(Text)
    cancelled_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    
    # Metadata
    extra_data = Column(JSON)  # Additional data from payment gateway (renamed from metadata to avoid SQLAlchemy conflict)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    restaurant = relationship("Restaurant", back_populates="subscriptions")
    cancelled_by_user = relationship("User")
    invoices = relationship("Invoice", back_populates="subscription", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Subscription(id={self.id}, restaurant_id={self.restaurant_id}, plan='{self.plan}', status='{self.status}')>"


class SubscriptionPlan(Base):
    """
    Defines available subscription plans and their features.
    """
    __tablename__ = "subscription_plans"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Plan Identity
    name = Column(String(50), unique=True, nullable=False, index=True)  # trial, basic, pro, enterprise
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    tagline = Column(String(200))
    
    # Pricing
    price_monthly = Column(Integer, default=0)  # in cents
    price_yearly = Column(Integer, default=0)  # in cents
    discount_yearly = Column(Integer, default=0)  # percentage discount for yearly
    
    # Limits
    max_users = Column(Integer, default=5)
    max_products = Column(Integer, default=100)
    max_orders_per_month = Column(Integer, default=1000)
    max_locations = Column(Integer, default=1)
    max_storage_gb = Column(Integer, default=1)
    
    # Features (JSON array of feature keys)
    features = Column(JSON, default=list)  # ["qr_ordering", "analytics", "loyalty", "multi_location", "api_access"]
    
    # Display
    is_active = Column(Boolean, nullable=False, default=True)
    is_public = Column(Boolean, nullable=False, default=True)  # Show on pricing page
    is_featured = Column(Boolean, nullable=False, default=False)
    sort_order = Column(Integer, default=0)
    badge = Column(String(50))  # "Most Popular", "Best Value"
    
    # Trial
    trial_days = Column(Integer, default=14)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SubscriptionPlan(name='{self.name}', display_name='{self.display_name}')>"


class Invoice(Base):
    """
    Billing invoices for subscriptions.
    """
    __tablename__ = "invoices"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_id = Column(String(36), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Invoice Details
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    amount = Column(Integer, nullable=False)  # in cents
    tax = Column(Integer, default=0)  # in cents
    total = Column(Integer, nullable=False)  # in cents
    currency = Column(String(3), default='USD')
    
    # Status
    status = Column(String(20), nullable=False, default='pending')  # pending, paid, failed, refunded
    
    # Dates
    invoice_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    due_date = Column(DateTime(timezone=True))
    paid_at = Column(DateTime(timezone=True))
    
    # Payment
    payment_method = Column(String(50))
    payment_gateway_invoice_id = Column(String(255))
    payment_gateway_charge_id = Column(String(255))
    
    # PDF
    pdf_url = Column(String(500))
    
    # Metadata
    description = Column(Text)
    extra_data = Column(JSON)  # Renamed from metadata to avoid SQLAlchemy conflict
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    subscription = relationship("Subscription", back_populates="invoices")
    restaurant = relationship("Restaurant")
    
    def __repr__(self):
        return f"<Invoice(invoice_number='{self.invoice_number}', amount={self.amount}, status='{self.status}')>"


class PlatformAdmin(Base):
    """
    Platform administrators who manage the entire SaaS platform.
    These are super users who can access all restaurants.
    """
    __tablename__ = "platform_admins"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    # Role & Permissions
    role = Column(String(20), nullable=False, default='admin')  # admin, support, billing, developer
    permissions = Column(JSON, default=list)  # Specific platform permissions
    
    # Access Control
    can_access_all_restaurants = Column(Boolean, default=True)
    can_modify_subscriptions = Column(Boolean, default=True)
    can_suspend_restaurants = Column(Boolean, default=True)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    created_by_user = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<PlatformAdmin(user_id={self.user_id}, role='{self.role}', is_active={self.is_active})>"


class RestaurantInvitation(Base):
    """
    Pending invitations to join a restaurant team.
    """
    __tablename__ = "restaurant_invitations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Invitee Information
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(100))
    role = Column(String(20), nullable=False)  # manager, staff, cashier
    
    # Invitation Details
    token = Column(String(100), unique=True, nullable=False, index=True)
    invited_by = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text)
    
    # Status
    status = Column(String(20), nullable=False, default='pending')  # pending, accepted, declined, expired
    accepted_at = Column(DateTime(timezone=True))
    accepted_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    restaurant = relationship("Restaurant")
    invited_by_user = relationship("User", foreign_keys=[invited_by])
    accepted_by_user = relationship("User", foreign_keys=[accepted_by])
    
    def __repr__(self):
        return f"<RestaurantInvitation(email='{self.email}', restaurant_id={self.restaurant_id}, status='{self.status}')>"
