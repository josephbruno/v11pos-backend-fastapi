# Restaurant POS FastAPI - Complete Project Analysis

## 📋 Project Overview

This is a comprehensive **Restaurant Point of Sale (POS) System** built with **FastAPI** and **MySQL**. It's a production-ready backend API that handles all aspects of restaurant operations including orders, inventory, customers, loyalty programs, QR ordering, and analytics.

**Live Production API:** https://apipos.v11tech.com/

---

## 🏗️ Architecture Overview

### Technology Stack
- **Framework:** FastAPI (Python)
- **Database:** MySQL 8.0 with SQLAlchemy ORM
- **Authentication:** JWT (JSON Web Tokens)
- **Validation:** Pydantic schemas
- **Server:** Uvicorn (ASGI)
- **Deployment:** Docker + Docker Compose
- **Web Server:** Nginx (reverse proxy in production)

### Project Structure
```
pos-fastapi/
├── app/
│   ├── models/          # Database models (SQLAlchemy)
│   ├── routes/          # API endpoints (FastAPI routers)
│   ├── schemas/         # Pydantic schemas for validation
│   ├── translations/    # Multi-language support files
│   ├── main.py          # Application entry point
│   ├── database.py      # Database configuration
│   ├── dependencies.py  # Auth & authorization middleware
│   ├── business_logic.py # Business calculations
│   ├── utils.py         # Utility functions
│   ├── enums.py         # Enumerations
│   ├── security.py      # Password hashing & JWT
│   ├── response_formatter.py # Standardized API responses
│   ├── email_service.py # Email notifications
│   └── i18n.py          # Internationalization
├── uploads/             # File storage (images, etc.)
├── migrations/          # Database migrations
├── tests/               # Test files
└── docker-compose.yml   # Docker configuration
```

---

## 📊 DATABASE MODELS

### 1. **User Management Models** (`app/models/user.py`)

#### **User**
Manages system users (admin, managers, staff, cashiers).

**Key Fields:**
- `id` - UUID primary key
- `name` - User's full name
- `email` - Unique email (used for login)
- `phone` - Contact number
- `password` - Hashed password (bcrypt)
- `role` - Enum: admin, manager, staff, cashier
- `status` - Enum: active, inactive, suspended
- `avatar` - Profile picture URL
- `permissions` - JSON array of custom permissions
- `join_date` - When user joined
- `last_login` - Last login timestamp

**Relationships:**
- One-to-Many with `ShiftSchedule` (user's work shifts)
- One-to-One with `StaffPerformance` (performance metrics)
- One-to-Many with `Order` (orders created by this user)

**Purpose:** Authentication, authorization, and staff management.

---

#### **ShiftSchedule**
Tracks employee work schedules.

**Key Fields:**
- `user_id` - Foreign key to User
- `day` - Day of week (monday-sunday)
- `start_time` - Shift start (HH:MM format)
- `end_time` - Shift end (HH:MM format)
- `position` - Job position for this shift
- `is_active` - Whether shift is currently active

**Purpose:** Manage staff scheduling and availability.

---

#### **StaffPerformance**
Tracks employee performance metrics.

**Key Fields:**
- `user_id` - Foreign key to User (unique)
- `orders_handled` - Total orders processed
- `total_revenue` - Total sales generated (in cents)
- `avg_order_value` - Average order value (in cents)
- `customer_rating` - Average customer rating (stored as rating × 100)
- `punctuality_score` - Attendance score (0-100)
- `last_calculated` - When metrics were last updated

**Purpose:** Performance tracking and analytics for staff management.

---

#### **PasswordResetToken**
Manages password reset requests via OTP.

**Key Fields:**
- `user_id` - Foreign key to User
- `email` - Email for reset
- `otp` - 6-digit one-time password
- `is_used` - Whether OTP has been used
- `expires_at` - Expiration timestamp

**Purpose:** Secure password recovery flow.

---

### 2. **Product Catalog Models** (`app/models/product.py`)

#### **Category**
Product categories for organization.

**Key Fields:**
- `id` - UUID primary key
- `name` - Category name (unique)
- `description` - Category description
- `image` - Category image URL
- `display_order` - Sort order for display
- `is_active` - Whether category is visible
- `color` - UI color code (hex)

**Relationships:**
- One-to-Many with `Product`
- One-to-Many with `ComboProduct`

**Purpose:** Organize products into categories (e.g., Beverages, Appetizers, Main Course).

---

#### **Product**
Individual menu items.

**Key Fields:**
- `name` - Product name
- `description` - Product description
- `category_id` - Foreign key to Category
- `price` - Price in cents
- `cost` - Cost price in cents
- `sku` - Stock keeping unit
- `barcode` - Barcode for scanning
- `image` - Product image URL
- `images` - JSON array of multiple images
- `is_available` - Stock availability
- `is_featured` - Featured on menu
- `preparation_time` - Prep time in minutes
- `calories` - Nutritional info
- `allergens` - JSON array of allergens
- `tags` - JSON array of tags (vegetarian, spicy, etc.)

**Relationships:**
- Many-to-One with `Category`
- One-to-Many with `ProductModifier` (available modifiers)
- One-to-Many with `OrderItem` (orders containing this product)

**Purpose:** Core menu items that customers can order.

---

#### **Modifier**
Customization options for products (e.g., size, toppings).

**Key Fields:**
- `name` - Modifier name (e.g., "Size", "Toppings")
- `type` - SINGLE (radio) or MULTIPLE (checkbox)
- `min_selection` - Minimum required selections
- `max_selection` - Maximum allowed selections
- `is_required` - Whether customer must select
- `display_order` - Sort order

**Relationships:**
- One-to-Many with `ModifierOption` (available options)
- One-to-Many with `ProductModifier` (products using this modifier)

**Purpose:** Allow product customization (e.g., Small/Medium/Large, Extra Cheese).

---

#### **ModifierOption**
Individual options within a modifier.

**Key Fields:**
- `modifier_id` - Foreign key to Modifier
- `name` - Option name (e.g., "Large", "Extra Cheese")
- `price_adjustment` - Additional cost in cents
- `is_default` - Default selection
- `is_available` - Currently available

**Purpose:** Specific choices for modifiers.

---

#### **ProductModifier**
Links products to their available modifiers.

**Key Fields:**
- `product_id` - Foreign key to Product
- `modifier_id` - Foreign key to Modifier
- `is_required` - Override modifier's is_required

**Purpose:** Define which modifiers apply to which products.

---

#### **ComboProduct**
Meal combos/bundles.

**Key Fields:**
- `name` - Combo name
- `description` - Combo description
- `category_id` - Foreign key to Category
- `price` - Bundle price in cents
- `original_price` - Sum of individual prices
- `savings` - Discount amount in cents
- `image` - Combo image
- `is_available` - Currently available
- `is_featured` - Featured combo

**Relationships:**
- Many-to-One with `Category`
- One-to-Many with `ComboItem` (products in this combo)

**Purpose:** Bundle multiple products at discounted price.

---

#### **ComboItem**
Products included in a combo.

**Key Fields:**
- `combo_id` - Foreign key to ComboProduct
- `product_id` - Foreign key to Product
- `quantity` - Number of this product in combo
- `is_required` - Must be included
- `is_customizable` - Can customer modify

**Purpose:** Define combo contents.

---

### 3. **Customer & Loyalty Models** (`app/models/customer.py`)

#### **Customer**
Customer profiles and information.

**Key Fields:**
- `name` - Customer name
- `phone` - Unique phone number
- `email` - Email address (unique)
- `address` - Delivery address
- `loyalty_points` - Current points balance
- `total_spent` - Lifetime spending in cents
- `visit_count` - Number of visits
- `last_visit` - Last order date
- `notes` - Staff notes about customer
- `is_blacklisted` - Banned from ordering

**Relationships:**
- One-to-Many with `CustomerTagMapping` (customer tags)
- One-to-Many with `Order` (order history)
- One-to-Many with `LoyaltyTransaction` (points history)
- One-to-Many with `QRSession` (QR ordering sessions)

**Purpose:** Customer relationship management and loyalty tracking.

---

#### **CustomerTag**
Tags for customer segmentation (VIP, Regular, etc.).

**Key Fields:**
- `name` - Tag name (unique)
- `color` - Display color (hex)
- `benefits` - JSON array of benefits
- `discount_percentage` - Automatic discount (stored as percentage × 100)
- `priority` - Display priority

**Relationships:**
- One-to-Many with `CustomerTagMapping`

**Purpose:** Segment customers for targeted marketing and benefits.

---

#### **CustomerTagMapping**
Assigns tags to customers.

**Key Fields:**
- `customer_id` - Foreign key to Customer
- `tag_id` - Foreign key to CustomerTag
- `assigned_at` - When tag was assigned
- `assigned_by` - Foreign key to User (who assigned it)

**Purpose:** Many-to-many relationship between customers and tags.

---

#### **LoyaltyRule**
Configurable loyalty program rules.

**Key Fields:**
- `name` - Rule name
- `earn_rate` - Points earned per dollar (stored as rate × 100)
- `redeem_rate` - Points required per dollar discount
- `min_redeem_points` - Minimum points to redeem
- `max_redeem_percentage` - Max % of order that can be paid with points
- `expiry_days` - Days until points expire
- `active` - Rule is active
- `priority` - Rule priority
- `applicable_tags` - JSON array of customer tags this applies to

**Purpose:** Configure how loyalty points are earned and redeemed.

---

#### **LoyaltyTransaction**
History of loyalty point transactions.

**Key Fields:**
- `customer_id` - Foreign key to Customer
- `order_id` - Foreign key to Order (if applicable)
- `points` - Points added/removed
- `operation` - EARN, REDEEM, ADJUST, or EXPIRE
- `reason` - Transaction description
- `balance_before` - Points before transaction
- `balance_after` - Points after transaction
- `expires_at` - When these points expire
- `created_by` - Foreign key to User

**Purpose:** Audit trail for all loyalty point changes.

---

### 4. **Order Management Models** (`app/models/order.py`)

#### **Order**
Customer orders.

**Key Fields:**
- `order_number` - Unique order number (e.g., ORD-251215-001234)
- `customer_id` - Foreign key to Customer (optional)
- `session_id` - Foreign key to QRSession (for QR orders)
- `order_type` - DINE_IN, TAKEAWAY, DELIVERY, or QR_ORDER
- `status` - CONFIRMED, PREPARING, READY, COMPLETED, CANCELLED
- `payment_status` - PENDING, COMPLETED, FAILED, REFUNDED
- `priority` - LOW, NORMAL, HIGH, URGENT
- `table_number` - Table number (for dine-in)
- `guest_count` - Number of guests
- `subtotal` - Order subtotal in cents
- `tax` - Tax amount in cents
- `service_charge` - Service charge in cents
- `discount` - Discount amount in cents
- `tip` - Tip amount in cents
- `total` - Final total in cents
- `loyalty_points_earned` - Points earned from this order
- `loyalty_points_redeemed` - Points used for discount
- `special_instructions` - Customer notes
- `estimated_prep_time` - Minutes to prepare
- `created_by` - Foreign key to User (staff who created order)

**Relationships:**
- Many-to-One with `Customer`
- Many-to-One with `QRSession`
- Many-to-One with `User` (created_by)
- One-to-Many with `OrderItem` (items in order)
- One-to-Many with `KOTGroup` (kitchen order tickets)
- One-to-Many with `OrderTax` (tax breakdown)
- One-to-Many with `LoyaltyTransaction`
- One-to-Many with `OrderStatusHistory`

**Purpose:** Core order management and tracking.

---

#### **OrderItem**
Individual items within an order.

**Key Fields:**
- `order_id` - Foreign key to Order
- `product_id` - Foreign key to Product
- `combo_id` - Foreign key to ComboProduct (if combo)
- `quantity` - Quantity ordered
- `unit_price` - Price per unit in cents
- `subtotal` - Item subtotal (quantity × unit_price)
- `discount` - Item-level discount
- `tax` - Item-level tax
- `total` - Item total
- `special_instructions` - Item-specific notes
- `preparation_time` - Prep time for this item

**Relationships:**
- Many-to-One with `Order`
- Many-to-One with `Product`
- Many-to-One with `ComboProduct`
- One-to-Many with `OrderItemModifier` (selected modifiers)

**Purpose:** Track individual items in an order.

---

#### **OrderItemModifier**
Modifiers selected for an order item.

**Key Fields:**
- `order_item_id` - Foreign key to OrderItem
- `modifier_id` - Foreign key to Modifier
- `option_id` - Foreign key to ModifierOption
- `price_adjustment` - Additional cost in cents

**Purpose:** Track customizations for order items.

---

#### **KOTGroup**
Kitchen Order Tickets for kitchen management.

**Key Fields:**
- `order_id` - Foreign key to Order
- `kot_number` - KOT number
- `department` - Kitchen department (e.g., "Grill", "Beverages")
- `status` - PENDING, ACKNOWLEDGED, PREPARING, READY, SERVED
- `items` - JSON array of item IDs in this KOT
- `priority` - KOT priority
- `estimated_time` - Estimated prep time
- `acknowledged_at` - When kitchen acknowledged
- `prepared_at` - When preparation completed
- `served_at` - When served to customer

**Purpose:** Organize order items by kitchen station for efficient preparation.

---

#### **OrderTax**
Tax breakdown for orders.

**Key Fields:**
- `order_id` - Foreign key to Order
- `tax_rule_id` - Foreign key to TaxRule
- `tax_name` - Tax name
- `tax_type` - Tax type
- `tax_percentage` - Tax rate (stored as percentage × 100)
- `taxable_amount` - Amount tax applies to
- `tax_amount` - Calculated tax in cents

**Purpose:** Detailed tax reporting and compliance.

---

#### **OrderStatusHistory**
Audit trail of order status changes.

**Key Fields:**
- `order_id` - Foreign key to Order
- `old_status` - Previous status
- `new_status` - New status
- `changed_by` - Foreign key to User
- `reason` - Reason for change
- `timestamp` - When change occurred

**Purpose:** Track order lifecycle for analytics and dispute resolution.

---

### 5. **QR Ordering Models** (`app/models/qr.py`)

#### **QRTable**
Restaurant tables with QR codes.

**Key Fields:**
- `table_number` - Unique table number
- `table_name` - Display name
- `location` - Table location (e.g., "Main Floor", "Patio")
- `capacity` - Number of seats
- `qr_token` - Unique token for QR code
- `qr_code_url` - URL encoded in QR code
- `qr_code_image` - QR code image file
- `is_active` - Table is active
- `is_occupied` - Currently occupied
- `current_session_id` - Active QR session
- `last_used` - Last usage timestamp

**Relationships:**
- One-to-Many with `QRSession`

**Purpose:** Enable contactless ordering via QR codes.

---

#### **QRSession**
Customer QR ordering sessions.

**Key Fields:**
- `table_id` - Foreign key to QRTable
- `customer_id` - Foreign key to Customer (if registered)
- `customer_name` - Guest name
- `customer_phone` - Guest phone
- `guest_count` - Number of guests
- `device_fingerprint` - Device identification
- `status` - ACTIVE, COMPLETED, ABANDONED
- `cart_items` - Number of items in cart
- `cart_total` - Cart total in cents
- `orders_placed` - Number of orders placed
- `total_spent` - Total spent in session
- `start_time` - Session start
- `end_time` - Session end
- `last_activity` - Last interaction
- `ip_address` - Customer IP
- `user_agent` - Browser info

**Relationships:**
- Many-to-One with `QRTable`
- Many-to-One with `Customer`
- One-to-Many with `Order`

**Purpose:** Track QR ordering sessions and customer behavior.

---

#### **QRSettings**
QR ordering system configuration.

**Key Fields:**
- `restaurant_name` - Restaurant name
- `logo` - Logo URL
- `primary_color` - Brand color (hex)
- `accent_color` - Accent color (hex)
- `enable_online_ordering` - Allow online orders
- `enable_payment_at_table` - Allow table payment
- `enable_online_payment` - Accept online payment
- `service_charge_percentage` - Service charge rate
- `auto_confirm_orders` - Auto-confirm without staff approval
- `order_timeout_minutes` - Session timeout
- `max_orders_per_session` - Order limit per session
- `enable_customer_info` - Require customer details
- `enable_special_instructions` - Allow order notes
- `enable_order_tracking` - Show order status
- `welcome_message` - Welcome text
- `terms_and_conditions` - T&C text
- `business_hours` - JSON of operating hours
- `payment_gateways` - JSON of payment options

**Purpose:** Configure QR ordering experience.

---

### 6. **Settings & Tax Models** (`app/models/settings.py`)

#### **TaxRule**
Configurable tax rules.

**Key Fields:**
- `name` - Tax name (e.g., "VAT", "Service Tax")
- `type` - Tax type
- `percentage` - Tax rate (stored as percentage × 100)
- `applicable_on` - ALL, DINE_IN, TAKEAWAY, or DELIVERY
- `categories` - JSON array of category IDs (if category-specific)
- `min_amount` - Minimum order for tax (in cents)
- `max_amount` - Maximum taxable amount
- `is_compounded` - Apply after other taxes
- `priority` - Calculation order
- `active` - Rule is active

**Purpose:** Flexible tax configuration for different scenarios.

---

#### **Settings**
Global restaurant settings.

**Key Fields:**
- `restaurant_name` - Restaurant name
- `address` - Physical address
- `phone` - Contact phone
- `email` - Contact email
- `website` - Website URL
- `logo` - Logo URL
- `currency` - Currency code (USD, EUR, etc.)
- `timezone` - Timezone
- `language` - Default language (en, es, fr, ar)
- `tax_rate` - Default tax rate
- `service_charge` - Default service charge
- `enable_tipping` - Allow tips
- `default_tip_percentages` - JSON array of tip options
- `print_kot_automatically` - Auto-print KOT
- `auto_print_receipt` - Auto-print receipt
- `email_notifications` - Enable email alerts
- `sms_notifications` - Enable SMS alerts
- `low_stock_alerts` - Alert on low stock
- `business_hours` - JSON of operating hours

**Purpose:** Centralized system configuration.

---

### 7. **Translation Model** (`app/models/translation.py`)

#### **Translation**
Multi-language support for all entities.

**Key Fields:**
- `entity_type` - Type of entity (product, category, modifier, etc.)
- `entity_id` - ID of the entity
- `field_name` - Field being translated (name, description, etc.)
- `language_code` - Language (en, es, fr, ar)
- `translation_value` - Translated text

**Indexes:**
- Composite unique index on (entity_type, entity_id, field_name, language_code)
- Index on (entity_type, entity_id) for fast lookups
- Index on language_code

**Purpose:** Support multi-language content for international restaurants.

---

## 🔧 CORE MODULES

### 1. **Enums** (`app/enums.py`)

Defines all enumeration types used throughout the system:

- **UserRole:** admin, manager, staff, cashier
- **UserStatus:** active, inactive, suspended
- **DayOfWeek:** monday through sunday
- **ModifierType:** single (radio), multiple (checkbox)
- **OrderType:** dine_in, takeaway, delivery, qr_order
- **OrderStatus:** confirmed, preparing, ready, completed, cancelled
- **PaymentStatus:** pending, completed, failed, refunded
- **OrderPriority:** low, normal, high, urgent
- **KOTStatus:** pending, acknowledged, preparing, ready, served
- **QRSessionStatus:** active, completed, abandoned
- **LoyaltyOperation:** earn, redeem, adjust, expire
- **TaxApplicableOn:** all, dine_in, takeaway, delivery

**Purpose:** Type-safe status values and consistent state management.

---

### 2. **Database** (`app/database.py`)

Database connection and session management.

**Key Components:**
- **engine:** SQLAlchemy engine with MySQL connection
- **SessionLocal:** Session factory for database operations
- **Base:** Declarative base for all models
- **get_db():** Dependency injection for database sessions
- **create_tables():** Initialize all database tables

**Configuration:**
- Connection pooling with pre-ping
- Pool recycling every 3600 seconds
- URL-encoded password support

**Purpose:** Centralized database configuration and connection management.

---

### 3. **Dependencies** (`app/dependencies.py`)

Authentication and authorization middleware.

**Key Functions:**

**verify_token(credentials):**
- Validates JWT tokens from Authorization header
- Extracts user_id, email, role from token
- Raises 401 if token is invalid/expired

**require_role(*allowed_roles):**
- Decorator to restrict endpoints by user role
- Returns 403 if user lacks required role
- Example: `@require_role("admin", "manager")`

**require_permission(permission):**
- Checks if user has specific permission
- Admins and managers bypass permission checks
- Example: `@require_permission("delete_orders")`

**get_current_user():**
- Returns full user details from token
- Validates user still exists in database

**get_admin_user():**
- Requires admin role

**get_manager_user():**
- Requires admin or manager role

**get_staff_user():**
- Requires any staff role

**Purpose:** Secure API endpoints with role-based access control.

---

### 4. **Business Logic** (`app/business_logic.py`)

Complex business calculations and rules.

#### **OrderCalculator Class:**

**calculate_subtotal(items):**
- Sums up all order items (quantity × unit_price)

**calculate_tax(subtotal, tax_percentage):**
- Applies tax rate to subtotal
- Returns tax amount in cents

**calculate_service_charge(subtotal, service_charge_percentage):**
- Calculates service charge
- Returns amount in cents

**apply_discount(subtotal, discount_amount, discount_percentage):**
- Applies fixed or percentage discount
- Returns (discount_amount, discount_type)

**calculate_total(subtotal, tax, service_charge, discount, tip):**
- Calculates final order total
- Formula: subtotal + tax + service_charge - discount + tip

**calculate_order_totals(items, tax_percentage, service_charge_percentage, ...):**
- Comprehensive calculation returning full breakdown
- Returns dict with subtotal, tax, service_charge, discount, tip, total

#### **LoyaltyCalculator Class:**

**calculate_points_earned(order_amount, earn_rate, customer_multiplier):**
- Calculates loyalty points from order
- Applies VIP multipliers

**calculate_points_value(points, redeem_rate, redemption_value_per_point):**
- Converts points to monetary value
- Returns (value_in_cents, reason)

**apply_expiry(points, current_date):**
- Removes expired points
- Returns (remaining_points, expired_transactions)

**get_loyalty_tier(total_spent):**
- Determines customer tier (Bronze, Silver, Gold, Platinum)
- Based on lifetime spending

#### **KOTGrouper Class:**

**group_by_department(items):**
- Groups order items by kitchen department
- Returns dict of {department: [items]}

**group_by_preparation_time(items):**
- Groups items by prep time for efficient cooking
- Returns dict of {time_bucket: [items]}

**calculate_estimated_prep_time(items):**
- Estimates total preparation time
- Considers parallel cooking

**Purpose:** Centralize complex business logic for consistency and testability.

---

### 5. **Utils** (`app/utils.py`)

Utility functions used throughout the application.

**Pagination:**
- `paginate_query(query, pagination)` - Paginate SQLAlchemy queries
- `create_paginated_response(items, pagination_meta, message)` - Format paginated responses

**ID Generation:**
- `generate_order_number(prefix)` - Generate unique order numbers (ORD-YYMMDD-XXXXXX)
- `generate_qr_token(length)` - Generate secure random tokens

**Currency Conversion:**
- `cents_to_dollars(cents)` - Convert cents to dollars (1999 → 19.99)
- `dollars_to_cents(dollars)` - Convert dollars to cents (19.99 → 1999)

**Percentage Conversion:**
- `percentage_to_int(percentage)` - Convert percentage to storage format (10.50% → 1050)
- `int_to_percentage(value)` - Convert storage format to percentage (1050 → 10.50%)

**Calculations:**
- `calculate_tax(amount, tax_rate)` - Calculate tax amount
- `calculate_discount(amount, discount_percentage)` - Calculate discount
- `calculate_order_total(subtotal, tax_rate, service_charge_rate, discount, tip)` - Full order calculation
- `calculate_loyalty_points(amount, earn_rate)` - Calculate points earned
- `calculate_loyalty_discount(points, redeem_rate)` - Calculate discount from points

**Time & Date:**
- `format_time_24h(time_str)` - Validate 24-hour time format
- `get_business_day(date)` - Get day of week in lowercase
- `is_within_business_hours(business_hours, check_time)` - Check if within operating hours
- `calculate_preparation_time(items)` - Estimate prep time

**String Utilities:**
- `generate_slug(text)` - Create URL-friendly slugs
- `validate_phone_number(phone)` - Basic phone validation
- `mask_phone_number(phone)` - Mask phone for privacy (+1-***-***-1234)

**Purpose:** Reusable helper functions to avoid code duplication.

---

### 6. **Response Formatter** (`app/response_formatter.py`)

Standardizes all API responses.

**Standard Response Format:**
```json
{
  "status": "success" | "error",
  "message": "Description of the result",
  "data": {...} | [...] | null
}
```

**Functions:**

**success_response(data, message, status_code=200):**
- Returns standardized success response
- Used for successful operations

**error_response(message, data, status_code=400):**
- Returns standardized error response
- Returns JSONResponse with error details

**created_response(data, message):**
- Returns 201 response for resource creation

**deleted_response(message):**
- Returns response for successful deletion

**list_response(items, message, total, page, page_size):**
- Returns paginated list response
- Includes pagination metadata

**Purpose:** Consistent API responses across all endpoints for easier client integration.

---

### 7. **Security** (`app/security.py`)

Password hashing and JWT token management.

**Key Functions:**

**hash_password(password):**
- Uses bcrypt to hash passwords
- Salted and secure

**verify_password(plain_password, hashed_password):**
- Verifies password against hash
- Returns True/False

**create_access_token(data, expires_delta):**
- Creates JWT access token
- Includes user_id, email, role
- Default expiry: 30 days

**create_refresh_token(data, expires_delta):**
- Creates JWT refresh token
- Longer expiry for token renewal

**Purpose:** Secure authentication and password management.

---

### 8. **Email Service** (`app/email_service.py`)

Email notifications for password resets and alerts.

**Key Functions:**

**send_password_reset_email(email, otp):**
- Sends OTP for password reset
- HTML formatted email

**send_order_confirmation_email(email, order_details):**
- Sends order confirmation to customer

**Purpose:** Automated email communications.

---

### 9. **i18n (Internationalization)** (`app/i18n.py`)

Multi-language support system.

**Supported Languages:**
- English (en)
- Spanish (es)
- French (fr)
- Arabic (ar)

**Key Functions:**

**get_translation(entity_type, entity_id, field_name, language_code):**
- Fetches translation from database
- Falls back to original if not found

**save_translation(entity_type, entity_id, field_name, language_code, value):**
- Saves translation to database

**get_entity_translations(entity_type, entity_id, language_code):**
- Gets all translations for an entity

**Purpose:** Support multi-language restaurants and international customers.

---

## 🛣️ API ROUTES

### Authentication Routes (`app/routes/auth.py`)
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login/json` - Login with JSON
- `POST /api/v1/auth/login/form` - Login with form data
- `POST /api/v1/auth/forgot-password` - Request password reset
- `POST /api/v1/auth/verify-otp` - Verify OTP code
- `POST /api/v1/auth/reset-password` - Reset password with OTP
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user info

### User Management Routes (`app/routes/users.py`)
- `GET /api/v1/users` - List all users (paginated)
- `POST /api/v1/users` - Create new user
- `GET /api/v1/users/{user_id}` - Get user details
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user
- `GET /api/v1/users/{user_id}/shifts` - Get user shifts
- `POST /api/v1/users/{user_id}/shifts` - Create shift
- `GET /api/v1/users/{user_id}/performance` - Get performance metrics
- `GET /api/v1/roles` - List available roles

### Product Routes (`app/routes/products.py`)
- `GET /api/v1/products` - List products (with filters)
- `POST /api/v1/products` - Create product
- `GET /api/v1/products/{product_id}` - Get product details
- `PUT /api/v1/products/{product_id}` - Update product
- `DELETE /api/v1/products/{product_id}` - Delete product
- `POST /api/v1/products/{product_id}/image` - Upload product image
- `GET /api/v1/products/{product_id}/translations` - Get translations

### Category Routes (`app/routes/categories.py`)
- `GET /api/v1/categories` - List categories
- `POST /api/v1/categories` - Create category
- `GET /api/v1/categories/{category_id}` - Get category
- `PUT /api/v1/categories/{category_id}` - Update category
- `DELETE /api/v1/categories/{category_id}` - Delete category
- `POST /api/v1/categories/{category_id}/image` - Upload image

### Order Routes (`app/routes/orders.py`)
- `GET /api/v1/orders` - List orders (with filters)
- `POST /api/v1/orders` - Create order
- `GET /api/v1/orders/{order_id}` - Get order details
- `PUT /api/v1/orders/{order_id}` - Update order
- `DELETE /api/v1/orders/{order_id}` - Cancel order
- `PUT /api/v1/orders/{order_id}/status` - Update order status
- `GET /api/v1/orders/{order_id}/kot` - Get KOT groups
- `POST /api/v1/orders/{order_id}/payment` - Process payment

### Customer Routes (`app/routes/customers.py`)
- `GET /api/v1/customers` - List customers
- `POST /api/v1/customers` - Create customer
- `GET /api/v1/customers/{customer_id}` - Get customer
- `PUT /api/v1/customers/{customer_id}` - Update customer
- `DELETE /api/v1/customers/{customer_id}` - Delete customer
- `GET /api/v1/customers/{customer_id}/orders` - Get order history
- `GET /api/v1/customers/{customer_id}/loyalty` - Get loyalty info
- `GET /api/v1/customer-tags` - List customer tags
- `POST /api/v1/customer-tags` - Create tag

### QR Ordering Routes (`app/routes/qr.py`)
- `GET /api/v1/qr/tables` - List QR tables
- `POST /api/v1/qr/tables` - Create QR table
- `GET /api/v1/qr/tables/{table_id}` - Get table details
- `GET /api/v1/qr/sessions` - List QR sessions
- `POST /api/v1/qr/sessions` - Start QR session
- `GET /api/v1/qr/sessions/{session_id}` - Get session details
- `PUT /api/v1/qr/sessions/{session_id}/end` - End session
- `GET /api/v1/qr/settings` - Get QR settings
- `PUT /api/v1/qr/settings` - Update QR settings

### Analytics Routes (`app/routes/analytics.py`)
- `GET /api/v1/analytics/sales` - Sales analytics
- `GET /api/v1/analytics/products` - Product performance
- `GET /api/v1/analytics/customers` - Customer analytics
- `GET /api/v1/analytics/staff` - Staff performance
- `GET /api/v1/reports/daily` - Daily report
- `GET /api/v1/reports/monthly` - Monthly report

### Dashboard Routes (`app/routes/dashboard.py`)
- `GET /api/v1/dashboard/overview` - Dashboard overview
- `GET /api/v1/dashboard/recent-orders` - Recent orders
- `GET /api/v1/dashboard/top-products` - Top selling products
- `GET /api/v1/dashboard/revenue` - Revenue statistics

### Other Routes
- Modifiers (`app/routes/modifiers.py`)
- Combos (`app/routes/combos.py`)
- Loyalty (`app/routes/loyalty.py`)
- Tax Settings (`app/routes/tax_settings.py`)
- File Manager (`app/routes/file_manager.py`)
- Translations (`app/routes/translations.py`)

---

## 🔐 AUTHENTICATION & AUTHORIZATION

### Authentication Flow
1. User sends credentials to `/api/v1/auth/login/json`
2. Server validates credentials
3. Server generates JWT access token (30-day expiry)
4. Client stores token
5. Client includes token in Authorization header: `Bearer <token>`
6. Server validates token on each request

### Authorization Levels
- **Admin:** Full system access
- **Manager:** Most operations except system settings
- **Staff:** Order management, customer service
- **Cashier:** Order creation, payment processing

### Token Structure
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "role": "admin",
  "type": "access",
  "exp": 1234567890
}
```

---

## 💾 DATA STORAGE

### Currency Storage
All monetary values stored as **integers in cents**:
- $19.99 → 1999 cents
- Avoids floating-point precision issues
- Use `cents_to_dollars()` and `dollars_to_cents()` for conversion

### Percentage Storage
All percentages stored as **integers (percentage × 100)**:
- 10.50% → 1050
- 4.75% → 475
- Use `percentage_to_int()` and `int_to_percentage()` for conversion

### Time Storage
- All timestamps use **timezone-aware datetime**
- Default timezone configurable in Settings
- Use `func.now()` for server-side timestamps

### Images
- Stored in `/uploads` directory
- Served via `/uploads` static route
- Support for single and multiple images (JSON array)

---

## 🌍 MULTI-LANGUAGE SUPPORT

### Translation System
- Generic `Translation` model for all entities
- Supports: products, categories, modifiers, combos, etc.
- Fields: name, description, and custom fields

### Supported Languages
- English (en) - Default
- Spanish (es)
- French (fr)
- Arabic (ar)

### Usage
```python
# Get translated product name
translation = get_translation(
    entity_type="product",
    entity_id=product_id,
    field_name="name",
    language_code="es"
)
```

---

## 📈 KEY FEATURES

### 1. **Order Management**
- Multiple order types (dine-in, takeaway, delivery, QR)
- Real-time status tracking
- KOT (Kitchen Order Ticket) system
- Order history and analytics

### 2. **Customer Loyalty**
- Points earning and redemption
- Configurable loyalty rules
- Customer segmentation with tags
- Tier-based benefits

### 3. **QR Ordering**
- Contactless table ordering
- Session management
- Real-time cart updates
- Customer self-service

### 4. **Product Catalog**
- Categories and products
- Modifiers and customizations
- Combo meals
- Multi-image support

### 5. **Staff Management**
- Role-based access control
- Shift scheduling
- Performance tracking
- Activity logging

### 6. **Analytics & Reporting**
- Sales analytics
- Product performance
- Customer insights
- Staff performance metrics

### 7. **Tax & Settings**
- Flexible tax rules
- Multiple tax types
- Global configuration
- Business hours management

### 8. **File Management**
- Image uploads
- Multiple image support
- Static file serving

---

## 🚀 DEPLOYMENT

### Docker Setup
```bash
# Start everything
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Production Deployment
- Nginx reverse proxy
- SSL/HTTPS with Let's Encrypt
- Automated deployment script
- Database migrations
- Sample data seeding

### Environment Variables
- `DB_HOST` - Database host
- `DB_PORT` - Database port
- `DB_USER` - Database user
- `DB_PASSWORD` - Database password
- `DB_NAME` - Database name
- `SECRET_KEY` - JWT secret key
- `SMTP_*` - Email configuration

---

## 📝 DEVELOPMENT GUIDELINES

### Adding New Models
1. Create model in `app/models/`
2. Import in `app/models/__init__.py`
3. Create Pydantic schemas in `app/schemas/`
4. Create routes in `app/routes/`
5. Add to `app/main.py`

### Adding New Endpoints
1. Create route function with proper decorators
2. Add authentication dependency if needed
3. Use standard response formatters
4. Add to router with proper prefix and tags
5. Document with docstrings

### Database Migrations
- Use Alembic for migrations (recommended)
- Or use `create_tables()` for simple setups

### Testing
- Test files in `tests/` directory
- Use `pytest` for testing
- Test scripts provided for API testing

---

## 🎯 BUSINESS LOGIC EXAMPLES

### Order Calculation Flow
1. Calculate subtotal from items
2. Apply discounts
3. Calculate tax on discounted subtotal
4. Add service charge
5. Add tip
6. Calculate loyalty points earned
7. Apply loyalty points redemption
8. Calculate final total

### Loyalty Points Flow
1. Customer places order
2. System calculates points earned (based on earn_rate)
3. Points added to customer balance
4. Transaction logged with expiry date
5. Customer can redeem points on future orders
6. Redeemed points deducted from balance
7. Expired points removed automatically

### KOT Management Flow
1. Order created
2. Items grouped by kitchen department
3. KOT generated for each department
4. Kitchen acknowledges KOT
5. Kitchen updates status (preparing → ready)
6. Server marks as served
7. Order status updated

---

## 🔍 SUMMARY

This is a **production-ready, feature-rich Restaurant POS system** with:

✅ **26 Database Models** covering all aspects of restaurant operations
✅ **111+ API Endpoints** for comprehensive functionality
✅ **JWT Authentication** with role-based access control
✅ **Multi-language Support** (en, es, fr, ar)
✅ **Loyalty Program** with configurable rules
✅ **QR Ordering** for contactless service
✅ **KOT Management** for kitchen operations
✅ **Analytics & Reporting** for business insights
✅ **Docker Deployment** for easy setup
✅ **Standard API Responses** for consistent client integration
✅ **Comprehensive Business Logic** for accurate calculations

The system is designed to handle:
- High-volume restaurant operations
- Multiple order types
- Complex product customizations
- Customer loyalty programs
- Staff management
- Multi-location support (via settings)
- International operations (multi-language, multi-currency)

**Live Production API:** https://apipos.v11tech.com/docs
