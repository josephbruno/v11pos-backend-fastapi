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
    code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, unique=True, index=True)
    station_type: Mapped[str] = mapped_column(
        SQLEnum(StationType, native_enum=False, length=20),
        nullable=False,
        index=True
    )
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Station location
    floor: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    section: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    zone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    physical_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Display configuration
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    color_code: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color for UI
    icon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    background_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    text_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    
    # Department routing - which products go to this station
    departments: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # List of department tags
    printer_tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # List of printer tags
    categories: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Product categories
    product_tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Capacity and timing
    max_concurrent_orders: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_concurrent_items: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    average_prep_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # In minutes
    max_prep_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    buffer_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Buffer between orders
    
    # Queue settings
    queue_mode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # fifo, priority, scheduled
    max_queue_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    auto_route_overflow: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    overflow_station_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Display Settings
    auto_accept_orders: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    alert_on_new_order: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_customer_names: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_table_numbers: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_order_type: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_prep_time: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_modifiers: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_allergens: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_prices: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Alert Settings
    alert_threshold_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    warning_threshold_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    critical_threshold_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    alert_sound_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    alert_volume: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0-100
    
    # Screen and layout
    screen_layout: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # grid, list, kanban
    items_per_screen: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    columns_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    font_size: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # small, medium, large
    
    # Printer configuration
    has_printer: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    printer_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    printer_ip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    printer_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    auto_print: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    print_copies: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Status and monitoring
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_busy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    maintenance_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Performance metrics
    current_load: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Current active orders
    total_orders_today: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    average_completion_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Minutes
    
    # Staff assignment
    assigned_staff: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # List of user IDs
    supervisor_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    team_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Operating hours
    operating_hours: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    break_times: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Integration
    external_system_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    kds_device_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    device_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Notifications
    notification_channels: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # email, sms, webhook
    escalation_rules: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Additional metadata
    station_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    custom_settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    last_online_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # Soft delete
    
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
    display_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Short number like "A-123"
    order_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    table_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    table_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    customer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    guest_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Order source
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # pos, online, phone, app
    channel: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Display status and timing
    status: Mapped[str] = mapped_column(
        SQLEnum(DisplayStatus, native_enum=False, length=20),
        default=DisplayStatus.NEW,
        nullable=False,
        index=True
    )
    
    # Sequence and ordering
    sequence_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    queue_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Timestamps for tracking
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ready_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    picked_up_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Priority and timing
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)  # Higher = more urgent
    priority_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # low, normal, high, urgent
    estimated_prep_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # In minutes
    actual_prep_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Calculated
    remaining_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    due_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)  # Expected completion
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Time thresholds
    warning_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    critical_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Alerts and flags
    is_delayed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_rush: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_priority: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_catering: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_attention: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    alert_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    alert_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Visual indicators
    color_indicator: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    badge_text: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    badge_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    
    # Staff tracking
    acknowledged_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    prepared_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    completed_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    checked_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # Quality check
    
    # Team assignment
    assigned_team: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Special instructions
    special_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    kitchen_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    customer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    allergen_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Item tracking
    total_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pending_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cancelled_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Quality and compliance
    quality_checked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quality_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    temperature_check: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    presentation_check: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Retry and error tracking
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Communication
    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notification_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_notification_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Course tracking (for multi-course meals)
    course_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    course_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_appetizer: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_main_course: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_dessert: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Dependencies
    depends_on_display_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    fire_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # When to start cooking
    hold_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Print tracking
    printed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    print_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_printed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Screen routing
    screen_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    display_zone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Delivery information
    delivery_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    delivery_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    driver_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Performance metrics
    cycle_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Total time in seconds
    idle_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    active_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Cancellation
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cancelled_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Delay tracking
    delay_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    delay_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    delay_notified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Additional metadata
    display_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    custom_fields: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # Soft delete
    
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
    product_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    category_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Modifiers and customization
    modifiers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    customization: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    variant_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    special_requests: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(
        SQLEnum(ItemStatus, native_enum=False, length=20),
        default=ItemStatus.PENDING,
        nullable=False,
        index=True
    )
    previous_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Timing
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    served_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Time tracking
    prep_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Actual time in seconds
    estimated_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cook_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    waiting_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Staff tracking
    prepared_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    served_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    checked_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Display and ordering
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    sequence_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    grouping_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Priority
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_urgent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Flags
    is_complimentary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_substitute: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_extra: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_modified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_void: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_attention: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quality_checked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Visual indicators
    color_code: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    highlight_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Kitchen routing
    station_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    preparation_area: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Dietary and allergen information
    dietary_tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    allergens: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    spice_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    temperature_requirement: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Cooking instructions
    cooking_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cooking_temperature: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    doneness: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # rare, medium, well-done
    plating_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Recipe and ingredients
    recipe_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ingredients_list: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    portions: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Quality control
    quality_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    temperature_check: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    presentation_check: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    taste_check: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Modifications tracking
    modification_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_modified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    modification_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Course tracking
    course_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    course_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    fire_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Bundling
    is_combo_item: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    parent_item_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    bundle_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Dependencies
    depends_on_item_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    blocking_items: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Hold and fire
    is_held: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hold_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hold_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Retry tracking
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    remake_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    original_item_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    
    # Waste tracking
    is_wasted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    waste_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    wasted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Print tracking
    printed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    print_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_printed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Communication
    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    alert_triggered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    alert_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    kitchen_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    chef_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Equipment and tools
    equipment_required: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    utensils_required: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Packaging
    packaging_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    container_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    requires_special_packaging: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Garnish and presentation
    garnish_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    presentation_style: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    serving_vessel: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Performance metrics
    efficiency_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    accuracy_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Additional metadata
    item_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    custom_fields: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # Soft delete
    
    def __repr__(self) -> str:
        return f"<KitchenDisplayItem(id={self.id}, product={self.product_name}, quantity={self.quantity}, status={self.status})>"
