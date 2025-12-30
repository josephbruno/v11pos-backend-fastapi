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
    
    # Guest information (for non-registered customers)
    guest_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    guest_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    guest_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Delivery information
    delivery_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    delivery_latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 8), nullable=True)
    delivery_longitude: Mapped[Optional[float]] = mapped_column(Numeric(11, 8), nullable=True)
    delivery_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
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
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Scheduled order
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    
    # Financial information (all in paise/cents)
    subtotal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tax_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    discount_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    delivery_fee: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    service_charge: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tip_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
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
    
    # Discounts and promotions
    discount_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    discount_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # percentage, fixed, item
    
    # Customer count
    guest_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Special requests and notes
    special_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    kitchen_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    staff_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Source tracking
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # pos, app, web, phone
    source_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Ratings and feedback
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Flags
    is_takeaway_ready: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_priority: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_cutlery: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
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
    product_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[int] = mapped_column(Integer, nullable=False)  # In paise/cents
    
    # Modifiers and customization
    modifiers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Selected modifiers and options
    customization: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Special requests for this item
    
    # Pricing
    modifiers_price: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    discount_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tax_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_price: Mapped[int] = mapped_column(Integer, nullable=False)  # (unit_price + modifiers_price) * quantity - discount + tax
    
    # Preparation tracking
    status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # pending, preparing, ready, served
    preparation_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    preparation_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Kitchen routing
    department: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # kitchen, bar, grill
    printer_tag: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Flags
    is_complimentary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_refunded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    refund_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    
    def __repr__(self) -> str:
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product={self.product_name}, quantity={self.quantity}, total={self.total_price})>"
