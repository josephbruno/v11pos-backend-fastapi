from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Text, Enum as SQLEnum, Numeric, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, List
import uuid
import enum
from app.core.database import Base


class OrderType(str, enum.Enum):
    """Order type enumeration"""
    DINE_IN = "dine_in"              # Table service
    TAKEAWAY = "takeaway"            # Customer picks up
    DELIVERY = "delivery"            # Home delivery
    DRIVE_THRU = "drive_thru"        # Drive-through
    OPEN_ORDER = "open_order"        # Open order (no customer assigned)
    CUSTOMER_ORDER = "customer_order" # Registered customer order
    MANUAL_ORDER = "manual_order"    # Manually entered by staff
    ONLINE_ORDER = "online_order"    # From online platform
    PHONE_ORDER = "phone_order"      # Phone order
    KIOSK_ORDER = "kiosk_order"      # Self-service kiosk


class OrderStatus(str, enum.Enum):
    """Order status enumeration"""
    PENDING = "pending"              # Order placed, awaiting confirmation
    CONFIRMED = "confirmed"          # Order confirmed
    PREPARING = "preparing"          # Kitchen preparing
    READY = "ready"                  # Order ready for pickup/delivery
    IN_TRANSIT = "in_transit"        # Out for delivery
    COMPLETED = "completed"          # Order completed
    CANCELLED = "cancelled"          # Order cancelled
    REFUNDED = "refunded"            # Order refunded
    ON_HOLD = "on_hold"              # Order on hold


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    REFUNDED = "refunded"
    FAILED = "failed"


class PaymentMethod(str, enum.Enum):
    """Payment method enumeration"""
    CASH = "cash"
    CARD = "card"
    DIGITAL_WALLET = "digital_wallet"
    UPI = "upi"
    BANK_TRANSFER = "bank_transfer"
    CREDIT = "credit"
    VOUCHER = "voucher"
    SPLIT = "split"                  # Multiple payment methods


class Order(Base):
    """Order database model - Linked to restaurant"""
    
    __tablename__ = "orders"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Order identification
    order_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    invoice_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True, index=True)
    receipt_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    display_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Short number for display (e.g., "A-123")
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)  # External reference
    
    order_type: Mapped[str] = mapped_column(
        SQLEnum(OrderType, native_enum=False, length=20),
        nullable=False,
        index=True
    )
    
    # Customer and table references
    customer_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    table_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("tables.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # User who created the order
    created_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Staff assignments
    assigned_waiter_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    assigned_chef_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    assigned_delivery_person_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    
    # Guest information (for non-registered customers)
    guest_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    guest_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    guest_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    guest_company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Delivery information
    delivery_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    delivery_address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    delivery_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    delivery_state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    delivery_postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    delivery_country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    delivery_latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 8), nullable=True)
    delivery_longitude: Mapped[Optional[float]] = mapped_column(Numeric(11, 8), nullable=True)
    delivery_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    delivery_distance: Mapped[Optional[float]] = mapped_column(nullable=True)  # In kilometers
    
    # Delivery tracking
    delivery_tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    delivery_partner: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Uber Eats, Zomato, etc.
    delivery_partner_order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    estimated_delivery_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    actual_delivery_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Order status and timing
    status: Mapped[str] = mapped_column(
        SQLEnum(OrderStatus, native_enum=False, length=20),
        default=OrderStatus.PENDING,
        nullable=False,
        index=True
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    preparing_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ready_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    dispatched_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Time estimates
    estimated_preparation_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Minutes
    actual_preparation_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Minutes
    
    # Scheduled order
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    is_scheduled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Financial information (all in paise/cents)
    subtotal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tax_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    discount_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    delivery_fee: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    service_charge: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    packaging_fee: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    convenience_fee: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tip_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    adjustment_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Manual adjustments
    rounding_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # For cash rounding
    total_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    
    # Tax breakdown
    tax_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # CGST, SGST, VAT breakdown
    
    # Payment
    payment_status: Mapped[str] = mapped_column(
        SQLEnum(PaymentStatus, native_enum=False, length=20),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True
    )
    payment_method: Mapped[Optional[str]] = mapped_column(
        SQLEnum(PaymentMethod, native_enum=False, length=20),
        nullable=True
    )
    payment_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Transaction IDs, split payment details
    paid_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    refund_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    due_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Payment tracking
    payment_transaction_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    payment_gateway: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Discounts and promotions
    discount_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    discount_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # percentage, fixed, item
    discount_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    promotion_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    loyalty_points_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    loyalty_points_earned: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Customer count and seating
    guest_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    adults_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    children_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Special requests and notes
    special_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    kitchen_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    staff_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    customer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    delivery_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Source tracking
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)  # pos, app, web, phone
    source_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    channel: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # direct, aggregator, website
    device_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Ratings and feedback
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    feedback_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    food_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    service_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    delivery_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Flags and settings
    is_takeaway_ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_priority: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_corporate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_catering: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_group_order: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_cutlery: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_invoice: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_gift: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_test_order: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_pos_order: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Cancellation and refund
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cancelled_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    refund_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    refunded_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Kitchen and preparation
    kitchen_display_sequence: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    preparation_sequence: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estimated_ready_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Packaging and presentation
    packaging_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    packaging_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gift_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Business and accounting
    fiscal_year: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    financial_period: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    cost_center: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    profit_center: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Analytics and reporting
    order_value_category: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # low, medium, high
    customer_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # new, returning, vip
    order_session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Marketing and attribution
    utm_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    utm_medium: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    utm_campaign: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    referrer_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Compliance and legal
    receipt_printed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    invoice_printed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    receipt_emailed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    invoice_emailed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    terms_accepted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    terms_accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Additional metadata
    order_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    custom_fields: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # External integrations
    external_order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    external_system: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sync_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # Soft delete
    
    # Relationships
    items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Order(id={self.id}, order_number={self.order_number}, type={self.order_type}, status={self.status}, total={self.total_amount})>"


class OrderItem(Base):
    """Order item database model - Items within an order"""
    
    __tablename__ = "order_items"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    # Item details (snapshot at time of order)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    product_sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    product_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    product_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Quantity and pricing
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)  # In paise/cents
    original_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Before any item-level discount
    
    # Modifiers and customization
    modifiers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Selected modifiers and options
    customization: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Special requests for this item
    variant_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Size, color, etc.
    
    # Pricing breakdown
    modifiers_price: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    discount_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    discount_percentage: Mapped[Optional[float]] = mapped_column(nullable=True)
    tax_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tax_rate: Mapped[Optional[float]] = mapped_column(nullable=True)
    total_price: Mapped[int] = mapped_column(Integer, nullable=False)  # (unit_price + modifiers_price) * quantity - discount + tax
    
    # Line item calculations
    line_subtotal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Before tax and discount
    line_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Final amount
    
    # Preparation tracking
    status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)  # pending, preparing, ready, served
    preparation_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    preparation_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    served_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Time tracking
    preparation_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Minutes
    cook_time_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Kitchen routing
    department: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # kitchen, bar, grill
    kitchen_station: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    printer_tag: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sequence_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Chef and staff tracking
    prepared_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    served_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Flags and special cases
    is_complimentary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_refunded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_void: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_promotional: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_substitute: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_extra: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Refund and cancellation
    refund_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    refund_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Packaging and presentation
    packaging_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    packaging_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    serving_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Dietary and allergen info (snapshot)
    dietary_tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    allergen_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    spice_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Weight and portions
    weight: Mapped[Optional[float]] = mapped_column(nullable=True)
    weight_unit: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    portion_size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Recipe and ingredients tracking
    recipe_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ingredients_snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Quality and feedback
    item_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    item_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quality_check_passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    quality_checked_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Loyalty and rewards
    loyalty_points_earned: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reward_item: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Inventory impact
    stock_deducted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    stock_deduction_quantity: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    kitchen_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    customer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Special handling
    rush_order: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    priority_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Combo and bundle tracking
    is_combo_item: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    combo_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    parent_item_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Course tracking (for multi-course meals)
    course_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    course_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Additional metadata
    item_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    custom_fields: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # External integration
    external_item_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # Soft delete
    
    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    
    def __repr__(self) -> str:
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product={self.product_name}, quantity={self.quantity}, total={self.total_price})>"
