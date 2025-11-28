"""
Analytics and Dashboard Schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class LowStockItem(BaseModel):
    """Low stock item in dashboard"""
    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    current_stock: int = Field(..., description="Current stock quantity")
    min_stock: int = Field(..., description="Minimum stock threshold")
    stock_percentage: float = Field(..., description="Stock percentage of minimum")
    unit: str = Field(..., description="Unit of measurement")

    class Config:
        from_attributes = True


class PeakHour(BaseModel):
    """Peak hour statistics"""
    hour: int = Field(..., description="Hour of day (0-23)")
    orders: int = Field(..., description="Number of orders")
    revenue: float = Field(..., description="Revenue in peak hour")
    time_slot: str = Field(..., description="Time slot display (HH:00 - HH:59)")


class TableOccupancy(BaseModel):
    """Table occupancy information"""
    occupied: int = Field(..., description="Number of occupied tables")
    total: int = Field(..., description="Total tables")
    occupancy_percentage: float = Field(..., description="Occupancy percentage")


class PaymentMethods(BaseModel):
    """Payment method breakdown"""
    cash: float = Field(default=0, description="Cash payments")
    card: float = Field(default=0, description="Card payments")
    online: float = Field(default=0, description="Online payments")
    other: float = Field(default=0, description="Other payments")


class OrderStatus(BaseModel):
    """Order status breakdown"""
    completed: int = Field(default=0, description="Completed orders")
    pending: int = Field(default=0, description="Pending orders")
    cancelled: int = Field(default=0, description="Cancelled orders")


class DashboardOverview(BaseModel):
    """Main dashboard overview metrics"""
    today_revenue: float = Field(..., description="Today's revenue")
    yesterday_revenue: float = Field(..., description="Yesterday's revenue")
    today_orders: int = Field(..., description="Today's order count")
    yesterday_orders: int = Field(..., description="Yesterday's order count")
    revenue_growth: float = Field(..., description="Revenue growth percentage")
    orders_growth: float = Field(..., description="Orders growth percentage")
    avg_order_value: float = Field(..., description="Average order value")
    total_customers: int = Field(..., description="Total unique customers")


class DashboardResponse(BaseModel):
    """Complete dashboard response"""
    overview: DashboardOverview
    peak_hour: PeakHour
    low_stock_items: List[LowStockItem]
    active_staff: int = Field(..., description="Number of active staff")
    total_staff: int = Field(..., description="Total staff count")
    table_occupancy: TableOccupancy
    payment_methods: PaymentMethods
    order_status: OrderStatus


class HourlyRevenue(BaseModel):
    """Hourly revenue breakdown"""
    hour: int = Field(..., description="Hour of day (0-23)")
    revenue: float = Field(..., description="Revenue for this hour")
    orders: int = Field(..., description="Number of orders")
    avg_value: float = Field(..., description="Average order value")


class PaymentMethodStats(BaseModel):
    """Payment method statistics"""
    amount: float = Field(..., description="Total amount")
    count: int = Field(..., description="Number of transactions")
    percentage: float = Field(..., description="Percentage of total")


class OrderTypeStats(BaseModel):
    """Order type statistics"""
    amount: float = Field(..., description="Total revenue")
    count: int = Field(..., description="Number of orders")
    percentage: float = Field(..., description="Percentage of total")


class SalesAnalyticsResponse(BaseModel):
    """Sales analytics response"""
    total_revenue: float = Field(..., description="Total revenue")
    total_orders: int = Field(..., description="Total orders")
    avg_order_value: float = Field(..., description="Average order value")
    by_hour: List[HourlyRevenue] = Field(..., description="Revenue by hour")
    by_payment_method: Dict[str, PaymentMethodStats] = Field(..., description="Revenue by payment method")
    by_order_type: Dict[str, OrderTypeStats] = Field(..., description="Revenue by order type")


class OrderItemModifier(BaseModel):
    """Modifier in order item"""
    id: str
    name: str
    price: float
    quantity: int

    class Config:
        from_attributes = True


class OrderItem(BaseModel):
    """Item in an order"""
    id: str
    product_id: str
    product_name: str
    quantity: int
    price: float
    subtotal: float
    modifiers: List[OrderItemModifier] = []

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Order response for dashboard"""
    id: str
    table_number: Optional[int] = None
    customer_name: str
    status: str = Field(..., description="pending, completed, cancelled")
    items: List[OrderItem]
    subtotal: float
    tax: float
    discount: float = 0
    total: float
    payment_method: str = Field(..., description="cash, card, online")
    payment_status: str = Field(..., description="paid, pending, failed")
    ordered_at: datetime
    completed_at: Optional[datetime] = None
    order_type: str = Field(..., description="dine-in, takeout, delivery")
    notes: str = ""

    class Config:
        from_attributes = True


class Pagination(BaseModel):
    """Pagination metadata"""
    total: int = Field(..., description="Total items")
    page: int = Field(..., description="Current page")
    limit: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total pages")
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")


class OrdersListResponse(BaseModel):
    """Orders list response with pagination"""
    orders: List[OrderResponse]
    pagination: Pagination


class QRTableStatus(BaseModel):
    """Status of a single QR table"""
    table_number: int
    status: str = Field(..., description="available or occupied")
    occupancy: int = Field(default=0, description="Number of people at table")
    order_id: Optional[str] = None


class QRTableOccupancyResponse(BaseModel):
    """QR table occupancy response"""
    occupied: int = Field(..., description="Number of occupied tables")
    available: int = Field(..., description="Number of available tables")
    total: int = Field(..., description="Total tables")
    tables: List[QRTableStatus]
