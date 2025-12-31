# Reports & Analytics Module Documentation

## Overview

The Reports & Analytics module provides comprehensive business intelligence for the POS system, supporting both restaurant-level and super admin level reporting with detailed analytics on sales, items, categories, payments, taxes, discounts, and profitability.

## Features

### Report Types

1. **Daily Sales Report** - Daily revenue and transaction analysis
2. **Monthly Sales Report** - Monthly aggregated sales data
3. **Item-wise Sales Report** - Product-level sales analytics
4. **Category-wise Sales Report** - Category performance analysis
5. **Payment Mode Report** - Payment method breakdown
6. **Tax Report (GST)** - Tax analysis with CGST/SGST/IGST breakdown
7. **Discount & Offer Report** - Discount impact analysis
8. **Cancelled/Void Orders Report** - Order cancellation analytics
9. **Profit & Cost Analysis** - Profitability analysis with margins

### Database Tables

#### 1. sales_reports
Main sales report table with comprehensive metrics:
- **Revenue Metrics**: total_sales, gross_sales, net_sales
- **Order Statistics**: completed, cancelled, void orders by type (dine-in, takeaway, delivery)
- **Tax Breakdown**: CGST, SGST, IGST, VAT, service tax
- **Discount Types**: coupon, loyalty, promotional, staff discounts
- **Payment Methods**: cash, card, UPI, wallet, online, credit
- **Customer Metrics**: total, new, returning, guest customers
- **Profit Analysis**: cost, gross profit, profit margin
- **Growth Metrics**: comparison with previous periods
- **Peak Analysis**: peak hours and revenue patterns

**Key Fields** (80+ total):
```sql
- id, restaurant_id, report_number, report_type
- from_date, to_date, period_type, period_value
- total_sales, gross_sales, net_sales
- total_orders, completed_orders, cancelled_orders
- dine_in/takeaway/delivery/online orders and revenue
- total_tax, cgst_amount, sgst_amount, igst_amount
- total_discount, coupon/loyalty/promotional discounts
- cash/card/upi/wallet/online/credit payments
- total_customers, new_customers, returning_customers
- total_items_sold, average_order_value
- total_cost, gross_profit, profit_margin
- sales/order/customer growth percentages
```

#### 2. item_wise_sales_reports
Product-level sales analytics:
- Quantity sold, revenue, cost, profit per item
- Pricing analysis (average, min, max)
- Discount and tax breakdown
- Modifiers and customizations
- Cancellations and refunds
- Order type breakdown
- Popularity ranking
- Growth comparison

**Key Fields** (50+ total):
```sql
- id, sales_report_id, restaurant_id, product_id
- product_name, product_sku, category_id, category_name
- quantity_sold, total_revenue, net_revenue
- average_selling_price, min/max_selling_price
- total_cost, gross_profit, profit_margin
- total_discount, total_tax
- order_count, average_quantity_per_order
- cancelled/void/refunded/complimentary quantities
- popularity_rank, revenue_contribution_percentage
```

#### 3. category_wise_sales_reports
Category performance analytics:
- Total items sold by category
- Revenue and profit per category
- Category ranking
- Growth trends
- Top selling items per category

**Key Fields** (30+ total):
```sql
- id, sales_report_id, restaurant_id, category_id
- category_name, parent_category_id
- total_items_sold, unique_items_count
- total_revenue, net_revenue
- total_cost, gross_profit, profit_margin
- popularity_rank, revenue_contribution_percentage
- top_selling_items (JSON)
```

#### 4. report_schedules
Automated report generation:
- Schedule name and frequency
- Report type configuration
- Email recipients and notifications
- Output format (PDF, Excel, CSV, JSON)
- Filters and customization
- Active status and next run time

**Key Fields** (20+ total):
```sql
- id, restaurant_id, schedule_name, report_type
- frequency (daily, weekly, monthly, quarterly, yearly)
- scheduled_time, scheduled_day, timezone
- email_recipients (JSON), notification_channels (JSON)
- output_format, filters (JSON)
- is_active, last_run_at, next_run_at
```

#### 5. report_exports
Report export tracking:
- Export name and format
- File details (path, size, URL)
- Processing status
- Download tracking
- Expiry management

**Key Fields** (20+ total):
```sql
- id, sales_report_id, restaurant_id
- export_name, report_type, file_format
- file_path, file_size, file_url
- status (pending, generating, completed, failed)
- processing_started_at, processing_completed_at
- download_count, last_downloaded_at
- expires_at
```

## API Endpoints

### Base URL
All endpoints are prefixed with: `/api/v1/reports`

### Sales Reports

#### Generate Sales Report
```http
POST /api/v1/reports/sales/generate
Authorization: Bearer <token>

Body:
{
  "report_type": "daily_sales" | "monthly_sales",
  "report_name": "Daily Sales - Jan 15",
  "from_date": "2025-01-15T00:00:00Z",
  "to_date": "2025-01-15T23:59:59Z",
  "restaurant_id": "uuid" | null,  // null for super admin (all restaurants)
  "filters": {},  // Optional filters
  "include_item_breakdown": false,
  "include_category_breakdown": false,
  "export_format": "pdf" | "excel" | "csv" | "json"
}
```

**Permissions**:
- **Super Admin**: Can generate for any restaurant or all restaurants
- **Restaurant User**: Can only generate for their restaurant

#### Get Sales Report
```http
GET /api/v1/reports/sales/{report_id}
Authorization: Bearer <token>
```

#### List Sales Reports
```http
GET /api/v1/reports/sales
Authorization: Bearer <token>

Query Parameters:
- restaurant_id: string (optional)
- report_type: string (optional)
- from_date: datetime (optional)
- to_date: datetime (optional)
- page: integer (default: 1)
- page_size: integer (default: 20, max: 100)
```

#### Update Sales Report
```http
PATCH /api/v1/reports/sales/{report_id}
Authorization: Bearer <token>

Body:
{
  "report_name": "Updated name",
  "notes": "Additional notes",
  "remarks": "Remarks"
}
```

#### Delete Sales Report
```http
DELETE /api/v1/reports/sales/{report_id}
Authorization: Bearer <token>
```

### Item-wise Sales Reports

#### Generate Item-wise Report
```http
POST /api/v1/reports/items/generate
Authorization: Bearer <token>

Query Parameters:
- from_date: datetime (required)
- to_date: datetime (required)
- restaurant_id: string (optional, super admin only)
```

#### List Item-wise Reports
```http
GET /api/v1/reports/items
Authorization: Bearer <token>

Query Parameters:
- restaurant_id: string (optional)
- from_date: datetime (optional)
- to_date: datetime (optional)
- page: integer (default: 1)
- page_size: integer (default: 50, max: 200)
```

### Category-wise Sales Reports

#### Generate Category-wise Report
```http
POST /api/v1/reports/categories/generate
Authorization: Bearer <token>

Query Parameters:
- from_date: datetime (required)
- to_date: datetime (required)
- restaurant_id: string (optional, super admin only)
```

#### List Category-wise Reports
```http
GET /api/v1/reports/categories
Authorization: Bearer <token>

Query Parameters:
- restaurant_id: string (optional)
- from_date: datetime (optional)
- to_date: datetime (optional)
- page: integer (default: 1)
- page_size: integer (default: 50, max: 200)
```

### Specialized Reports

#### Payment Mode Report
```http
GET /api/v1/reports/payment-mode
Authorization: Bearer <token>

Query Parameters:
- from_date: datetime (required)
- to_date: datetime (required)
- restaurant_id: string (optional, super admin only)
```

Returns breakdown by payment methods:
- Cash, Card, UPI, Wallet, Online, Credit
- Transaction counts and amounts
- Percentage distribution

#### Tax (GST) Report
```http
GET /api/v1/reports/tax-gst
Authorization: Bearer <token>

Query Parameters:
- from_date: datetime (required)
- to_date: datetime (required)
- restaurant_id: string (optional, super admin only)
```

Returns tax breakdown:
- CGST, SGST, IGST amounts
- VAT and Service Tax
- Tax slab breakdown
- Total taxable amount

#### Discount & Offers Report
```http
GET /api/v1/reports/discounts-offers
Authorization: Bearer <token>

Query Parameters:
- from_date: datetime (required)
- to_date: datetime (required)
- restaurant_id: string (optional, super admin only)
```

Returns discount analysis:
- Coupon, Loyalty, Promotional, Staff discounts
- Discount counts and amounts
- Revenue impact
- Discount percentage

#### Cancelled/Void Orders Report
```http
GET /api/v1/reports/cancelled-void
Authorization: Bearer <token>

Query Parameters:
- from_date: datetime (required)
- to_date: datetime (required)
- restaurant_id: string (optional, super admin only)
```

Returns cancellation analytics:
- Cancelled and void order counts
- Revenue lost
- Refund statistics
- Cancellation rate
- Reason breakdown

#### Profit & Cost Analysis
```http
GET /api/v1/reports/profit-cost
Authorization: Bearer <token>

Query Parameters:
- from_date: datetime (required)
- to_date: datetime (required)
- restaurant_id: string (optional, super admin only)
```

Returns profitability analysis:
- Gross and net revenue
- Food, labor, overhead costs
- Gross and net profit
- Profit margins
- Category and item-wise breakdown

### Dashboard Endpoints

#### Super Admin Dashboard
```http
GET /api/v1/reports/dashboard/super-admin
Authorization: Bearer <token>

Query Parameters:
- from_date: datetime (optional, defaults to 30 days ago)
- to_date: datetime (optional, defaults to now)
```

**Super Admin Only** - Aggregated analytics across all restaurants.

#### Restaurant Dashboard
```http
GET /api/v1/reports/dashboard/restaurant
Authorization: Bearer <token>

Query Parameters:
- restaurant_id: string (optional, defaults to user's restaurant)
- from_date: datetime (optional, defaults to 30 days ago)
- to_date: datetime (optional, defaults to now)
```

Restaurant-specific analytics dashboard.

## Access Control

### Role-Based Permissions

#### Super Admin
- Can generate reports for any restaurant or all restaurants combined
- Can view all reports across all restaurants
- Can access super admin dashboard
- Can schedule reports for any restaurant
- Full CRUD operations on all reports

#### Restaurant User
- Can only generate reports for their assigned restaurant
- Can only view reports for their restaurant
- Can access restaurant-level dashboard
- Can schedule reports for their restaurant
- CRUD operations limited to their restaurant's reports

## Migration

The module includes migration `caff3b24ffed` which creates all 5 report tables with proper indexes:

```bash
# Apply migration
alembic upgrade head

# Current migration
alembic current
# Output: caff3b24ffed (head)
```

## Usage Examples

### Generate Daily Sales Report

```python
# For restaurant user
POST /api/v1/reports/sales/generate
{
  "report_type": "daily_sales",
  "report_name": "Daily Sales - Jan 15, 2025",
  "from_date": "2025-01-15T00:00:00Z",
  "to_date": "2025-01-15T23:59:59Z",
  "include_item_breakdown": true,
  "include_category_breakdown": true
}

# For super admin (all restaurants)
POST /api/v1/reports/sales/generate
{
  "report_type": "daily_sales",
  "report_name": "Daily Sales - All Restaurants",
  "from_date": "2025-01-15T00:00:00Z",
  "to_date": "2025-01-15T23:59:59Z",
  "restaurant_id": null,  // null = all restaurants
  "include_item_breakdown": true
}
```

### Generate Monthly Sales Report

```python
POST /api/v1/reports/sales/generate
{
  "report_type": "monthly_sales",
  "report_name": "Monthly Sales - January 2025",
  "from_date": "2025-01-01T00:00:00Z",
  "to_date": "2025-01-31T23:59:59Z",
  "include_category_breakdown": true
}
```

### Get Item-wise Sales

```python
POST /api/v1/reports/items/generate?from_date=2025-01-01T00:00:00Z&to_date=2025-01-31T23:59:59Z

# List top selling items
GET /api/v1/reports/items?from_date=2025-01-01T00:00:00Z&page=1&page_size=50
```

### Get Category Performance

```python
POST /api/v1/reports/categories/generate?from_date=2025-01-01T00:00:00Z&to_date=2025-01-31T23:59:59Z

# List category reports
GET /api/v1/reports/categories?from_date=2025-01-01T00:00:00Z&page=1&page_size=20
```

## Response Format

All endpoints follow the standard response format:

```json
{
  "success": true,
  "message": "Sales report generated successfully",
  "data": {
    "id": "uuid",
    "report_number": "SR-20250115120000-abc123",
    "report_type": "daily_sales",
    "report_name": "Daily Sales - Jan 15",
    "from_date": "2025-01-15T00:00:00Z",
    "to_date": "2025-01-15T23:59:59Z",
    "total_sales": 150000,  // in paise (₹1,500.00)
    "total_orders": 45,
    "completed_orders": 42,
    "cancelled_orders": 3,
    "average_order_value": 3333,  // ₹33.33
    "total_tax": 15000,  // ₹150.00
    "total_discount": 5000,  // ₹50.00
    "gross_profit": 50000,  // ₹500.00
    "profit_margin": 33.33,
    // ... more fields
    "created_at": "2025-01-15T12:00:00Z"
  }
}
```

## Key Features

### 1. Multi-level Reporting
- **Restaurant Level**: Individual restaurant performance
- **Super Admin Level**: Aggregated cross-restaurant analytics

### 2. Comprehensive Metrics
- Sales and revenue (gross, net, total)
- Order statistics (completed, cancelled, void)
- Payment method breakdown
- Tax analysis (GST compliant)
- Discount impact
- Customer analytics
- Profit and cost analysis

### 3. Flexible Date Ranges
- Daily reports
- Monthly reports
- Custom date ranges
- Period comparisons

### 4. Growth Analysis
- Compare with previous periods
- Growth percentages
- Trend analysis

### 5. Detailed Breakdowns
- Item-wise sales
- Category-wise sales
- Hourly breakdown
- Payment method distribution

### 6. Future Enhancements (TODO)
- Report scheduling service
- Export to PDF/Excel/CSV
- Email delivery
- Dashboard widgets
- Comparative analysis charts
- Forecasting and predictions

## Database Indexes

All tables include proper indexes for optimal query performance:
- Primary keys on `id`
- Foreign keys on `restaurant_id`, `sales_report_id`, etc.
- Indexes on frequently queried fields: `from_date`, `to_date`, `report_type`, `status`

## Integration

The reports module integrates with:
- **Order Module**: Source data for sales reports
- **Product Module**: Product and category information
- **Restaurant Module**: Restaurant filtering and aggregation
- **User Module**: Access control and permissions

## Testing

The module can be tested using:
1. FastAPI Swagger UI at `/docs`
2. Postman collection (to be created)
3. Unit tests (to be implemented)

## Deployment

The module is production-ready with:
- ✅ Database migration applied
- ✅ Router registered in main app
- ✅ Role-based access control
- ✅ Pagination support
- ✅ Error handling
- ✅ Git committed and pushed

## Maintenance

Regular maintenance tasks:
1. Archive old reports (>6 months)
2. Clean up expired exports
3. Monitor report generation performance
4. Update indexes based on query patterns
5. Implement caching for frequently accessed reports

## Support

For issues or questions:
- Check API documentation at `/docs`
- Review migration files in `migrations/versions/`
- Examine service logic in `app/modules/reports/service.py`
- Check route definitions in `app/modules/reports/route.py`

---

**Module Version**: 1.0.0  
**Migration**: caff3b24ffed  
**Commit**: be76175  
**Date**: January 2025
