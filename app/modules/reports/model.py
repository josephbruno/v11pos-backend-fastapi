from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Text, Enum as SQLEnum, JSON, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
import uuid
import enum
from app.core.database import Base


class ReportType(str, enum.Enum):
    """Report type enumeration"""
    DAILY_SALES = "daily_sales"
    MONTHLY_SALES = "monthly_sales"
    ITEM_WISE_SALES = "item_wise_sales"
    CATEGORY_WISE_SALES = "category_wise_sales"
    PAYMENT_MODE = "payment_mode"
    TAX_REPORT = "tax_report"
    DISCOUNT_OFFER = "discount_offer"
    CANCELLED_VOID = "cancelled_void"
    PROFIT_COST = "profit_cost"
    STAFF_PERFORMANCE = "staff_performance"
    CUSTOMER_ANALYTICS = "customer_analytics"
    INVENTORY_REPORT = "inventory_report"
    HOURLY_SALES = "hourly_sales"
    COMPARATIVE_SALES = "comparative_sales"
    CUSTOM = "custom"


class ReportStatus(str, enum.Enum):
    """Report status enumeration"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    SCHEDULED = "scheduled"


class ReportFormat(str, enum.Enum):
    """Report format enumeration"""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"


class ReportFrequency(str, enum.Enum):
    """Report frequency enumeration"""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class SalesReport(Base):
    """Sales report model - Daily/Monthly sales reports"""
    
    __tablename__ = "sales_reports"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Report identification
    report_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    report_type: Mapped[str] = mapped_column(
        SQLEnum(ReportType, native_enum=False, length=30),
        nullable=False,
        index=True
    )
    report_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Date range
    report_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    from_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    to_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    
    # Period information
    period_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # day, week, month, quarter, year
    period_value: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # "2025-12", "Q1-2025"
    fiscal_year: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    fiscal_period: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Sales metrics (all amounts in paise/cents)
    total_sales: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    gross_sales: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    net_sales: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Order statistics
    total_orders: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_orders: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cancelled_orders: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    void_orders: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Order type breakdown
    dine_in_orders: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    takeaway_orders: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    delivery_orders: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    online_orders: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Revenue breakdown
    dine_in_revenue: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    takeaway_revenue: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    delivery_revenue: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    online_revenue: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Tax information
    total_tax: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cgst_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sgst_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    igst_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    vat_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    service_tax: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Discounts and offers
    total_discount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    coupon_discount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    loyalty_discount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    promotional_discount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    staff_discount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Additional charges
    delivery_charges: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    service_charges: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    packaging_charges: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    convenience_fees: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Tips and extras
    total_tips: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rounding_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Payment methods
    cash_payments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    card_payments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    upi_payments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    wallet_payments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    online_payments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    credit_payments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Refunds
    total_refunds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    refund_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Customer metrics
    total_customers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_customers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    returning_customers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    guest_customers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Items sold
    total_items_sold: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unique_items_sold: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    complimentary_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Average metrics
    average_order_value: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_items_per_order: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    average_customer_spend: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Cost and profit
    total_cost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    gross_profit: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    profit_margin: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    
    # Comparison metrics (vs previous period)
    sales_growth_percentage: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    order_growth_percentage: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    customer_growth_percentage: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    
    # Peak hours
    peak_hour: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    peak_hour_sales: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Additional breakdown
    category_wise_sales: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    item_wise_sales: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    hourly_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    payment_method_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Super admin fields (for aggregated reports)
    is_consolidated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    total_restaurants: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    restaurant_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Report generation
    generated_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    generation_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # seconds
    
    # Notes and remarks
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Additional metadata
    report_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    filters_applied: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    custom_fields: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<SalesReport(id={self.id}, report_number={self.report_number}, type={self.report_type}, total_sales={self.total_sales})>"


class ItemWiseSalesReport(Base):
    """Item-wise sales report model"""
    
    __tablename__ = "item_wise_sales_reports"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sales_report_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("sales_reports.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    restaurant_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    product_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    category_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    
    # Date range
    from_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    to_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    
    # Product information (snapshot)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    product_sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    category_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Sales metrics
    quantity_sold: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    total_revenue: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    gross_revenue: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    net_revenue: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Pricing
    average_selling_price: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    min_selling_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_selling_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Cost and profit
    total_cost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_cost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    gross_profit: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    profit_margin: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    
    # Discounts
    total_discount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    discount_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Tax
    total_tax: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Order statistics
    order_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_quantity_per_order: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    
    # Modifiers and customization
    with_modifiers_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    modifier_revenue: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Cancellations and voids
    cancelled_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    void_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    refunded_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Complimentary
    complimentary_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Order type breakdown
    dine_in_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    takeaway_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    delivery_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Performance metrics
    popularity_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    revenue_contribution_percentage: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    
    # Growth metrics
    previous_period_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    growth_percentage: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    
    # Peak times
    peak_hour: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    peak_day: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Additional metrics
    return_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    customer_satisfaction_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)
    
    # Metadata
    hourly_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    daily_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    item_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<ItemWiseSalesReport(id={self.id}, product={self.product_name}, quantity={self.quantity_sold}, revenue={self.total_revenue})>"


class CategoryWiseSalesReport(Base):
    """Category-wise sales report model"""
    
    __tablename__ = "category_wise_sales_reports"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sales_report_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("sales_reports.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    restaurant_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    category_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    # Date range
    from_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    to_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    
    # Category information
    category_name: Mapped[str] = mapped_column(String(100), nullable=False)
    parent_category_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    parent_category_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Sales metrics
    total_items_sold: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unique_items_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_revenue: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    gross_revenue: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    net_revenue: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Cost and profit
    total_cost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    gross_profit: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    profit_margin: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    
    # Discounts and tax
    total_discount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tax: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Order statistics
    order_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_items_per_order: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    
    # Performance metrics
    popularity_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    revenue_contribution_percentage: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    
    # Growth metrics
    previous_period_revenue: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    growth_percentage: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    
    # Top items in category
    top_selling_items: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Metadata
    category_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<CategoryWiseSalesReport(id={self.id}, category={self.category_name}, items_sold={self.total_items_sold}, revenue={self.total_revenue})>"


class ReportSchedule(Base):
    """Report schedule model - Automated report generation"""
    
    __tablename__ = "report_schedules"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Schedule information
    schedule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(
        SQLEnum(ReportType, native_enum=False, length=30),
        nullable=False,
        index=True
    )
    
    # Frequency
    frequency: Mapped[str] = mapped_column(
        SQLEnum(ReportFrequency, native_enum=False, length=20),
        nullable=False
    )
    
    # Schedule time
    scheduled_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # HH:MM
    scheduled_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Day of month or week
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Recipients
    email_recipients: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    notification_channels: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Report format
    output_format: Mapped[str] = mapped_column(
        SQLEnum(ReportFormat, native_enum=False, length=10),
        nullable=False
    )
    
    # Filters
    filters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    
    # Created by
    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    
    # Metadata
    schedule_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<ReportSchedule(id={self.id}, name={self.schedule_name}, type={self.report_type}, frequency={self.frequency})>"


class ReportExport(Base):
    """Report export model - Track exported reports"""
    
    __tablename__ = "report_exports"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sales_report_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    restaurant_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Export information
    export_name: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(String(30), nullable=False)
    
    # File details
    file_format: Mapped[str] = mapped_column(
        SQLEnum(ReportFormat, native_enum=False, length=10),
        nullable=False
    )
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # bytes
    file_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(
        SQLEnum(ReportStatus, native_enum=False, length=20),
        default=ReportStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Processing
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    processing_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # seconds
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Download tracking
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_downloaded_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Expiry
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    
    # Generated by
    generated_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    
    # Metadata
    export_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<ReportExport(id={self.id}, name={self.export_name}, format={self.file_format}, status={self.status})>"
