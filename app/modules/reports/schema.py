from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class ReportTypeEnum(str, Enum):
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


class ReportStatusEnum(str, Enum):
    """Report status enumeration"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    SCHEDULED = "scheduled"


class ReportFormatEnum(str, Enum):
    """Report format enumeration"""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"


class ReportFrequencyEnum(str, Enum):
    """Report frequency enumeration"""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


# Sales Report Schemas

class SalesReportBase(BaseModel):
    """Base sales report schema"""
    restaurant_id: Optional[str] = None
    report_name: str = Field(..., min_length=1, max_length=255)
    report_type: ReportTypeEnum
    from_date: datetime
    to_date: datetime
    period_type: Optional[str] = None
    period_value: Optional[str] = None
    fiscal_year: Optional[str] = None
    fiscal_period: Optional[str] = None
    notes: Optional[str] = None
    remarks: Optional[str] = None


class SalesReportCreate(SalesReportBase):
    """Schema for creating sales report"""
    filters_applied: Optional[Dict[str, Any]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class SalesReportUpdate(BaseModel):
    """Schema for updating sales report"""
    report_name: Optional[str] = Field(None, min_length=1, max_length=255)
    notes: Optional[str] = None
    remarks: Optional[str] = None
    report_metadata: Optional[Dict[str, Any]] = None
    tags: Optional[Dict[str, Any]] = None


class SalesReportResponse(SalesReportBase):
    """Schema for sales report response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    report_number: str
    report_date: datetime
    
    # Sales metrics
    total_sales: int
    gross_sales: int
    net_sales: int
    
    # Order statistics
    total_orders: int
    completed_orders: int
    cancelled_orders: int
    void_orders: int
    
    # Order type breakdown
    dine_in_orders: int
    takeaway_orders: int
    delivery_orders: int
    online_orders: int
    
    # Revenue breakdown
    dine_in_revenue: int
    takeaway_revenue: int
    delivery_revenue: int
    online_revenue: int
    
    # Tax information
    total_tax: int
    cgst_amount: int
    sgst_amount: int
    igst_amount: int
    vat_amount: int
    service_tax: int
    
    # Discounts
    total_discount: int
    coupon_discount: int
    loyalty_discount: int
    promotional_discount: int
    staff_discount: int
    
    # Additional charges
    delivery_charges: int
    service_charges: int
    packaging_charges: int
    convenience_fees: int
    
    # Tips and extras
    total_tips: int
    rounding_amount: int
    
    # Payment methods
    cash_payments: int
    card_payments: int
    upi_payments: int
    wallet_payments: int
    online_payments: int
    credit_payments: int
    
    # Refunds
    total_refunds: int
    refund_count: int
    
    # Customer metrics
    total_customers: int
    new_customers: int
    returning_customers: int
    guest_customers: int
    
    # Items sold
    total_items_sold: int
    unique_items_sold: int
    complimentary_items: int
    
    # Average metrics
    average_order_value: int
    average_items_per_order: Optional[float]
    average_customer_spend: int
    
    # Cost and profit
    total_cost: int
    gross_profit: int
    profit_margin: Optional[float]
    
    # Comparison metrics
    sales_growth_percentage: Optional[float]
    order_growth_percentage: Optional[float]
    customer_growth_percentage: Optional[float]
    
    # Peak hours
    peak_hour: Optional[str]
    peak_hour_sales: int
    
    # Breakdowns
    category_wise_sales: Optional[Dict[str, Any]]
    item_wise_sales: Optional[Dict[str, Any]]
    hourly_breakdown: Optional[Dict[str, Any]]
    payment_method_breakdown: Optional[Dict[str, Any]]
    
    # Super admin fields
    is_consolidated: bool
    total_restaurants: Optional[int]
    restaurant_breakdown: Optional[Dict[str, Any]]
    
    # Generation info
    generated_by: Optional[str]
    generation_time: Optional[int]
    
    # Metadata
    report_metadata: Optional[Dict[str, Any]]
    filters_applied: Optional[Dict[str, Any]]
    custom_fields: Optional[Dict[str, Any]]
    tags: Optional[Dict[str, Any]]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]


# Item-wise Sales Report Schemas

class ItemWiseSalesReportBase(BaseModel):
    """Base item-wise sales report schema"""
    restaurant_id: Optional[str] = None
    product_id: str
    category_id: Optional[str] = None
    from_date: datetime
    to_date: datetime


class ItemWiseSalesReportCreate(ItemWiseSalesReportBase):
    """Schema for creating item-wise sales report"""
    sales_report_id: Optional[str] = None


class ItemWiseSalesReportResponse(ItemWiseSalesReportBase):
    """Schema for item-wise sales report response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    sales_report_id: Optional[str]
    
    # Product information
    product_name: str
    product_sku: Optional[str]
    category_name: Optional[str]
    
    # Sales metrics
    quantity_sold: int
    total_revenue: int
    gross_revenue: int
    net_revenue: int
    
    # Pricing
    average_selling_price: int
    min_selling_price: Optional[int]
    max_selling_price: Optional[int]
    
    # Cost and profit
    total_cost: int
    average_cost: int
    gross_profit: int
    profit_margin: Optional[float]
    
    # Discounts and tax
    total_discount: int
    discount_count: int
    total_tax: int
    
    # Order statistics
    order_count: int
    average_quantity_per_order: Optional[float]
    
    # Modifiers
    with_modifiers_count: int
    modifier_revenue: int
    
    # Cancellations
    cancelled_quantity: int
    void_quantity: int
    refunded_quantity: int
    complimentary_quantity: int
    
    # Order type breakdown
    dine_in_quantity: int
    takeaway_quantity: int
    delivery_quantity: int
    
    # Performance metrics
    popularity_rank: Optional[int]
    revenue_contribution_percentage: Optional[float]
    
    # Growth metrics
    previous_period_quantity: Optional[int]
    growth_percentage: Optional[float]
    
    # Peak times
    peak_hour: Optional[str]
    peak_day: Optional[str]
    
    # Additional metrics
    return_rate: Optional[float]
    customer_satisfaction_score: Optional[float]
    
    # Metadata
    hourly_breakdown: Optional[Dict[str, Any]]
    daily_breakdown: Optional[Dict[str, Any]]
    item_metadata: Optional[Dict[str, Any]]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime


# Category-wise Sales Report Schemas

class CategoryWiseSalesReportBase(BaseModel):
    """Base category-wise sales report schema"""
    restaurant_id: Optional[str] = None
    category_id: str
    from_date: datetime
    to_date: datetime


class CategoryWiseSalesReportCreate(CategoryWiseSalesReportBase):
    """Schema for creating category-wise sales report"""
    sales_report_id: Optional[str] = None


class CategoryWiseSalesReportResponse(CategoryWiseSalesReportBase):
    """Schema for category-wise sales report response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    sales_report_id: Optional[str]
    
    # Category information
    category_name: str
    parent_category_id: Optional[str]
    parent_category_name: Optional[str]
    
    # Sales metrics
    total_items_sold: int
    unique_items_count: int
    total_revenue: int
    gross_revenue: int
    net_revenue: int
    
    # Cost and profit
    total_cost: int
    gross_profit: int
    profit_margin: Optional[float]
    
    # Discounts and tax
    total_discount: int
    total_tax: int
    
    # Order statistics
    order_count: int
    average_items_per_order: Optional[float]
    
    # Performance metrics
    popularity_rank: Optional[int]
    revenue_contribution_percentage: Optional[float]
    
    # Growth metrics
    previous_period_revenue: Optional[int]
    growth_percentage: Optional[float]
    
    # Top items
    top_selling_items: Optional[Dict[str, Any]]
    
    # Metadata
    category_metadata: Optional[Dict[str, Any]]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime


# Report Schedule Schemas

class ReportScheduleBase(BaseModel):
    """Base report schedule schema"""
    restaurant_id: Optional[str] = None
    schedule_name: str = Field(..., min_length=1, max_length=255)
    report_type: ReportTypeEnum
    frequency: ReportFrequencyEnum
    scheduled_time: Optional[str] = Field(None, pattern=r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$')
    scheduled_day: Optional[int] = Field(None, ge=1, le=31)
    timezone: Optional[str] = None
    email_recipients: Optional[Dict[str, Any]] = None
    notification_channels: Optional[Dict[str, Any]] = None
    output_format: ReportFormatEnum
    filters: Optional[Dict[str, Any]] = None


class ReportScheduleCreate(ReportScheduleBase):
    """Schema for creating report schedule"""
    pass


class ReportScheduleUpdate(BaseModel):
    """Schema for updating report schedule"""
    schedule_name: Optional[str] = Field(None, min_length=1, max_length=255)
    frequency: Optional[ReportFrequencyEnum] = None
    scheduled_time: Optional[str] = Field(None, pattern=r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$')
    scheduled_day: Optional[int] = Field(None, ge=1, le=31)
    timezone: Optional[str] = None
    email_recipients: Optional[Dict[str, Any]] = None
    notification_channels: Optional[Dict[str, Any]] = None
    output_format: Optional[ReportFormatEnum] = None
    filters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ReportScheduleResponse(ReportScheduleBase):
    """Schema for report schedule response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    is_active: bool
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    created_by: Optional[str]
    schedule_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]


# Report Export Schemas

class ReportExportBase(BaseModel):
    """Base report export schema"""
    export_name: str = Field(..., min_length=1, max_length=255)
    report_type: str
    file_format: ReportFormatEnum


class ReportExportCreate(ReportExportBase):
    """Schema for creating report export"""
    sales_report_id: Optional[str] = None
    restaurant_id: Optional[str] = None
    export_metadata: Optional[Dict[str, Any]] = None


class ReportExportResponse(ReportExportBase):
    """Schema for report export response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    sales_report_id: Optional[str]
    restaurant_id: Optional[str]
    file_path: Optional[str]
    file_size: Optional[int]
    file_url: Optional[str]
    status: ReportStatusEnum
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
    processing_time: Optional[int]
    error_message: Optional[str]
    retry_count: int
    download_count: int
    last_downloaded_at: Optional[datetime]
    expires_at: Optional[datetime]
    generated_by: Optional[str]
    export_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]


# Report Request Schemas (for API)

class ReportGenerateRequest(BaseModel):
    """Schema for generating a report"""
    report_type: ReportTypeEnum
    report_name: str = Field(..., min_length=1, max_length=255)
    from_date: datetime
    to_date: datetime
    restaurant_id: Optional[str] = Field(None, description="For super admin: specify restaurant, or None for all")
    filters: Optional[Dict[str, Any]] = None
    include_item_breakdown: bool = False
    include_category_breakdown: bool = False
    export_format: Optional[ReportFormatEnum] = None


class PaymentModeReportResponse(BaseModel):
    """Schema for payment mode report"""
    model_config = ConfigDict(from_attributes=True)
    
    from_date: datetime
    to_date: datetime
    restaurant_id: Optional[str]
    
    # Payment breakdown
    cash_payments: int
    cash_count: int
    card_payments: int
    card_count: int
    upi_payments: int
    upi_count: int
    wallet_payments: int
    wallet_count: int
    online_payments: int
    online_count: int
    credit_payments: int
    credit_count: int
    
    # Totals
    total_payments: int
    total_transactions: int
    
    # Percentages
    payment_method_breakdown: Dict[str, Any]


class TaxReportResponse(BaseModel):
    """Schema for tax (GST) report"""
    model_config = ConfigDict(from_attributes=True)
    
    from_date: datetime
    to_date: datetime
    restaurant_id: Optional[str]
    
    # GST breakdown
    cgst_amount: int
    sgst_amount: int
    igst_amount: int
    total_gst: int
    
    # Other taxes
    vat_amount: int
    service_tax: int
    
    # Totals
    total_tax: int
    taxable_amount: int
    
    # Tax slabs breakdown
    tax_slab_breakdown: Optional[Dict[str, Any]]


class DiscountOfferReportResponse(BaseModel):
    """Schema for discount & offer report"""
    model_config = ConfigDict(from_attributes=True)
    
    from_date: datetime
    to_date: datetime
    restaurant_id: Optional[str]
    
    # Discount breakdown
    coupon_discount: int
    coupon_count: int
    loyalty_discount: int
    loyalty_count: int
    promotional_discount: int
    promotional_count: int
    staff_discount: int
    staff_count: int
    
    # Totals
    total_discount: int
    total_discount_count: int
    
    # Impact
    revenue_without_discount: int
    discount_percentage: Optional[float]
    
    # Breakdown
    discount_breakdown: Dict[str, Any]


class CancelledVoidReportResponse(BaseModel):
    """Schema for cancelled/void orders report"""
    model_config = ConfigDict(from_attributes=True)
    
    from_date: datetime
    to_date: datetime
    restaurant_id: Optional[str]
    
    # Cancelled orders
    cancelled_orders: int
    cancelled_revenue_lost: int
    
    # Void orders
    void_orders: int
    void_revenue_lost: int
    
    # Refunds
    refund_count: int
    total_refunds: int
    
    # Totals
    total_lost_revenue: int
    cancellation_rate: Optional[float]
    
    # Reasons breakdown
    cancellation_reasons: Optional[Dict[str, Any]]
    void_reasons: Optional[Dict[str, Any]]


class ProfitCostAnalysisResponse(BaseModel):
    """Schema for profit & cost analysis report"""
    model_config = ConfigDict(from_attributes=True)
    
    from_date: datetime
    to_date: datetime
    restaurant_id: Optional[str]
    
    # Revenue
    gross_revenue: int
    net_revenue: int
    
    # Costs
    total_cost: int
    food_cost: int
    labor_cost: Optional[int]
    overhead_cost: Optional[int]
    
    # Profit
    gross_profit: int
    net_profit: Optional[int]
    profit_margin: Optional[float]
    
    # Breakdown
    category_wise_profit: Optional[Dict[str, Any]]
    item_wise_profit: Optional[Dict[str, Any]]
    
    # Metrics
    cost_percentage: Optional[float]
    revenue_per_order: int
    profit_per_order: int


# List responses

class SalesReportListResponse(BaseModel):
    """Schema for paginated sales report list"""
    total: int
    page: int
    page_size: int
    data: List[SalesReportResponse]


class ItemWiseSalesReportListResponse(BaseModel):
    """Schema for paginated item-wise sales report list"""
    total: int
    page: int
    page_size: int
    data: List[ItemWiseSalesReportResponse]


class CategoryWiseSalesReportListResponse(BaseModel):
    """Schema for paginated category-wise sales report list"""
    total: int
    page: int
    page_size: int
    data: List[CategoryWiseSalesReportResponse]


class ReportScheduleListResponse(BaseModel):
    """Schema for paginated report schedule list"""
    total: int
    page: int
    page_size: int
    data: List[ReportScheduleResponse]


class ReportExportListResponse(BaseModel):
    """Schema for paginated report export list"""
    total: int
    page: int
    page_size: int
    data: List[ReportExportResponse]
