from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
import uuid
import enum
from app.core.database import Base


class StationType(str, enum.Enum):
    """Kitchen station type enumeration"""
    MAIN_KITCHEN = "main_kitchen"
    GRILL = "grill"
    FRYER = "fryer"
    SALAD = "salad"
    BAR = "bar"
    DESSERT = "dessert"
    BAKERY = "bakery"
    PIZZA = "pizza"
    SUSHI = "sushi"
    WOK = "wok"
    EXPEDITOR = "expeditor"  # Final check before serving


class DisplayStatus(str, enum.Enum):
    """Kitchen display status enumeration"""
    NEW = "new"              # Just received
    ACKNOWLEDGED = "acknowledged"  # Kitchen has seen it
    IN_PROGRESS = "in_progress"   # Being prepared
    READY = "ready"          # Ready to serve/deliver
    COMPLETED = "completed"  # Served/picked up
    DELAYED = "delayed"      # Taking longer than expected
    CANCELLED = "cancelled"  # Order cancelled


class ItemStatus(str, enum.Enum):
    """Kitchen display item status enumeration"""
    PENDING = "pending"
    PREPARING = "preparing"
    READY = "ready"
    SERVED = "served"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class KitchenStation(Base):
    """Kitchen station model - Different stations in the kitchen"""
    
    __tablename__ = "kitchen_stations"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Station information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    station_type: Mapped[str] = mapped_column(
        SQLEnum(StationType, native_enum=False, length=20),
        nullable=False,
        index=True
    )
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Station location
    floor: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    section: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Display configuration
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    color_code: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color for UI
    
    # Department routing - which products go to this station
    departments: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # List of department tags
    printer_tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # List of printer tags
    
    # Capacity and timing
    max_concurrent_orders: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    average_prep_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # In minutes
    
    # Settings
    auto_accept_orders: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    alert_on_new_order: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_customer_names: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_table_numbers: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Staff assignment
    assigned_staff: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # List of user IDs
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<KitchenStation(id={self.id}, name={self.name}, type={self.station_type}, restaurant_id={self.restaurant_id})>"


class KitchenDisplay(Base):
    """Kitchen display model - Orders shown on kitchen displays"""
    
    __tablename__ = "kitchen_displays"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    station_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("kitchen_stations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    order_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Order information (snapshot for display)
    order_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    order_type: Mapped[str] = mapped_column(String(20), nullable=False)
    table_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    customer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Display status and timing
    status: Mapped[str] = mapped_column(
        SQLEnum(DisplayStatus, native_enum=False, length=20),
        default=DisplayStatus.NEW,
        nullable=False,
        index=True
    )
    
    # Timestamps for tracking
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ready_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Priority and timing
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)  # Higher = more urgent
    estimated_prep_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # In minutes
    actual_prep_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Calculated
    due_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)  # Expected completion
    
    # Alerts and flags
    is_delayed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_rush: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    alert_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Staff tracking
    acknowledged_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    prepared_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Special instructions
    special_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    kitchen_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Item count
    total_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<KitchenDisplay(id={self.id}, order_number={self.order_number}, station_id={self.station_id}, status={self.status})>"


class KitchenDisplayItem(Base):
    """Kitchen display item model - Individual items on kitchen displays"""
    
    __tablename__ = "kitchen_display_items"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    display_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("kitchen_displays.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    order_item_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("order_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Item information (snapshot)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Modifiers and customization
    modifiers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    customization: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(
        SQLEnum(ItemStatus, native_enum=False, length=20),
        default=ItemStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    prep_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Actual time in seconds
    
    # Prepared by
    prepared_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Display order (for multiple items)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Flags
    is_complimentary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_attention: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
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
    
    def __repr__(self) -> str:
        return f"<KitchenDisplayItem(id={self.id}, product={self.product_name}, quantity={self.quantity}, status={self.status})>"
