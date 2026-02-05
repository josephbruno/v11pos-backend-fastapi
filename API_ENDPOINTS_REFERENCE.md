# API Endpoints - Complete Reference

## Authentication Endpoints (`/api/v1/auth`)

### POST /auth/login ✅ FIXED
**Accepts:** JSON or Form-encoded data
**Authentication:** None (public)

**JSON Request:**
```json
{
  "email": "superadmin@restaurant.com",
  "password": "Super@123"
}
```

**Form Request:**
```
email=superadmin@restaurant.com&password=Super@123
```

**Response:**
```json
{
  "success": true,
  "status_code": 200,
  "message": "Login successful",
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer"
  },
  "error": null,
  "timestamp": "2024-01-01T12:00:00.000000Z"
}
```

### POST /auth/refresh
**Accepts:** JSON only
**Authentication:** None (uses refresh token)

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

### POST /auth/forgot-password
**Accepts:** JSON only
**Authentication:** None (public)

**Request:**
```json
{
  "email": "user@example.com"
}
```

### POST /auth/logout
**Accepts:** No body required
**Authentication:** None (client-side token removal)

### GET /auth/login-logs/me
**Authentication:** Required (Bearer token)
**Query Params:** `skip`, `limit`

### GET /auth/login-logs/email/{email}
**Authentication:** Required (Bearer token)
**Query Params:** `skip`, `limit`

### GET /auth/login-logs/suspicious
**Authentication:** Required (Superuser only)
**Query Params:** `skip`, `limit`

---

## User Endpoints (`/api/v1/users`)

### POST /users
**Accepts:** JSON only
**Authentication:** None (public registration)

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe",
  "phone": "+1234567890"
}
```

### GET /users
**Authentication:** Required
**Query Params:** `skip`, `limit`, `restaurant_id`

### GET /users/restaurant/{restaurant_id}
**Authentication:** Required
**Query Params:** `skip`, `limit`

### GET /users/me
**Authentication:** Required

### GET /users/{user_id}
**Authentication:** Required

### PUT /users/{user_id}
**Accepts:** JSON only
**Authentication:** Required

### DELETE /users/{user_id}
**Authentication:** Required (Superuser only)

---

## Restaurant Endpoints (`/api/v1/restaurants`)

### POST /restaurants
**Accepts:** JSON only
**Authentication:** Required

**Request:**
```json
{
  "name": "My Restaurant",
  "address": "123 Main St",
  "phone": "+1234567890",
  "email": "contact@restaurant.com",
  "timezone": "America/New_York"
}
```

### GET /restaurants
**Authentication:** Required
**Query Params:** `skip`, `limit`

### GET /restaurants/{restaurant_id}
**Authentication:** Required

### PUT /restaurants/{restaurant_id}
**Accepts:** JSON only
**Authentication:** Required

### DELETE /restaurants/{restaurant_id}
**Authentication:** Required (Superuser only)

### POST /restaurants/subscription-plans
**Accepts:** JSON only
**Authentication:** Required (Superuser only)

### POST /restaurants/{restaurant_id}/subscriptions
**Accepts:** JSON only
**Authentication:** Required

### POST /restaurants/subscriptions/{subscription_id}/cancel
**Authentication:** Required

### POST /restaurants/{restaurant_id}/invitations
**Accepts:** JSON only
**Authentication:** Required

### POST /restaurants/invitations/{token}/accept
**Authentication:** Required

---

## Product Endpoints (`/api/v1/products`)

### POST /products/categories
**Accepts:** JSON only
**Authentication:** Required

**Request:**
```json
{
  "name": "Beverages",
  "description": "All drinks",
  "restaurant_id": "uuid",
  "is_active": true
}
```

### GET /products/categories
**Authentication:** Required
**Query Params:** `restaurant_id`, `skip`, `limit`

### POST /products
**Accepts:** JSON only
**Authentication:** Required

**Request:**
```json
{
  "name": "Coffee",
  "description": "Hot coffee",
  "price": 3.50,
  "category_id": "uuid",
  "restaurant_id": "uuid",
  "is_available": true
}
```

### GET /products
**Authentication:** Required
**Query Params:** `restaurant_id`, `category_id`, `skip`, `limit`

### POST /products/inventory/adjust
**Accepts:** JSON only
**Authentication:** Required

### POST /products/modifiers
**Accepts:** JSON only
**Authentication:** Required

### POST /products/modifiers/options
**Accepts:** JSON only
**Authentication:** Required

### POST /products/combos
**Accepts:** JSON only
**Authentication:** Required

---

## Customer Endpoints (`/api/v1/customers`)

### POST /customers
**Accepts:** JSON only
**Authentication:** Required

### GET /customers
**Authentication:** Required
**Query Params:** `restaurant_id`, `skip`, `limit`

---

## Table Endpoints (`/api/v1/tables`)

### POST /tables
**Accepts:** JSON only
**Authentication:** Required

**Request:**
```json
{
  "table_number": "T1",
  "capacity": 4,
  "restaurant_id": "uuid",
  "status": "available"
}
```

### GET /tables
**Authentication:** Required
**Query Params:** `restaurant_id`, `status`, `skip`, `limit`

### POST /tables/bulk/status
**Accepts:** JSON only
**Authentication:** Required

---

## Order Endpoints (`/api/v1/orders`)

### POST /orders
**Accepts:** JSON only
**Authentication:** Required

**Request:**
```json
{
  "restaurant_id": "uuid",
  "table_id": "uuid",
  "customer_id": "uuid",
  "items": [
    {
      "product_id": "uuid",
      "quantity": 2,
      "price": 3.50
    }
  ],
  "order_type": "dine_in"
}
```

### GET /orders
**Authentication:** Required
**Query Params:** `restaurant_id`, `status`, `skip`, `limit`

### POST /orders/{order_id}/items
**Accepts:** JSON only
**Authentication:** Required

### POST /orders/{order_id}/cancel
**Authentication:** Required

---

## KDS Endpoints (`/api/v1/kds`)

### POST /kds/stations
**Accepts:** JSON only
**Authentication:** Required

### GET /kds/stations
**Authentication:** Required
**Query Params:** `restaurant_id`

### POST /kds/displays/route/{order_id}
**Accepts:** JSON only
**Authentication:** Required

### POST /kds/displays/{display_id}/acknowledge
**Authentication:** Required

### POST /kds/displays/{display_id}/start
**Authentication:** Required

### POST /kds/displays/{display_id}/complete
**Authentication:** Required

### POST /kds/displays/{display_id}/bump
**Authentication:** Required

### POST /kds/items/bulk/status
**Accepts:** JSON only
**Authentication:** Required

### POST /kds/displays/{display_id}/kot/print
**Authentication:** Required

---

## Inventory Endpoints (`/api/v1/inventory`)

### POST /inventory/ingredients
**Accepts:** JSON only
**Authentication:** Required

### GET /inventory/ingredients
**Authentication:** Required
**Query Params:** `restaurant_id`, `skip`, `limit`

### POST /inventory/recipes
**Accepts:** JSON only
**Authentication:** Required

### POST /inventory/stock/transactions
**Accepts:** JSON only
**Authentication:** Required

### POST /inventory/stock/adjustment
**Accepts:** JSON only
**Authentication:** Required

### POST /inventory/stock/wastage
**Accepts:** JSON only
**Authentication:** Required

### POST /inventory/stock/damage
**Accepts:** JSON only
**Authentication:** Required

### POST /inventory/suppliers
**Accepts:** JSON only
**Authentication:** Required

### POST /inventory/purchase-orders
**Accepts:** JSON only
**Authentication:** Required

### POST /inventory/purchase-orders/{po_id}/receive
**Accepts:** JSON only
**Authentication:** Required

### POST /inventory/alerts/low-stock/{alert_id}/resolve
**Authentication:** Required

### POST /inventory/stock/auto-deduct
**Accepts:** JSON only
**Authentication:** Required

---

## Staff Endpoints (`/api/v1/staff`)

### POST /staff/roles
**Accepts:** JSON only
**Authentication:** Required

### POST /staff/members
**Accepts:** JSON only
**Authentication:** Required

### POST /staff/shifts
**Accepts:** JSON only
**Authentication:** Required

### POST /staff/attendance/check-in
**Accepts:** JSON only
**Authentication:** Required

### POST /staff/attendance/{attendance_id}/check-out
**Authentication:** Required

### POST /staff/attendance/manual
**Accepts:** JSON only
**Authentication:** Required

### POST /staff/leave-applications
**Accepts:** JSON only
**Authentication:** Required

### POST /staff/leave-applications/{leave_id}/approve
**Authentication:** Required

---

## Reports Endpoints (`/api/v1/reports`)

### POST /reports/sales/generate
**Accepts:** JSON only
**Authentication:** Required

**Request:**
```json
{
  "restaurant_id": "uuid",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "group_by": "day"
}
```

### POST /reports/items/generate
**Accepts:** JSON only
**Authentication:** Required

### POST /reports/categories/generate
**Accepts:** JSON only
**Authentication:** Required

---

## Data Import Endpoints (`/api/v1/data-import`)

### POST /data-import/upload
**Accepts:** Multipart form data (file upload)
**Authentication:** Required

### POST /data-import/generate-sample
**Accepts:** JSON only
**Authentication:** Required

---

## Data Copy Endpoints (`/api/v1/data-copy`)

### POST /data-copy/...
**Accepts:** JSON only
**Authentication:** Required

---

## Standard Response Format

All endpoints return responses in this standardized format:

### Success Response
```json
{
  "success": true,
  "status_code": 200,
  "message": "Operation successful",
  "data": {
    // Response data
  },
  "error": null,
  "timestamp": "2024-01-01T12:00:00.000000Z"
}
```

### Error Response
```json
{
  "success": false,
  "status_code": 400,
  "message": "Error message",
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message",
    "details": "Detailed error information",
    "field": "fieldName"
  },
  "timestamp": "2024-01-01T12:00:00.000000Z"
}
```

### Paginated Response
```json
{
  "success": true,
  "status_code": 200,
  "message": "Data retrieved successfully",
  "data": [
    // Array of items
  ],
  "error": null,
  "meta": {
    "page": 1,
    "limit": 50,
    "total": 100,
    "total_pages": 2
  },
  "timestamp": "2024-01-01T12:00:00.000000Z"
}
```

---

## Authentication

Most endpoints require authentication using JWT Bearer tokens:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

To obtain a token, use the `/api/v1/auth/login` endpoint.

---

## Common HTTP Status Codes

- **200 OK** - Successful GET, PUT, DELETE, or POST operation
- **201 Created** - Successful POST operation that created a resource
- **400 Bad Request** - Invalid request data
- **401 Unauthorized** - Missing or invalid authentication token
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Resource not found
- **422 Unprocessable Entity** - Validation error
- **500 Internal Server Error** - Server error

---

## Notes

1. **Content-Type**: Most endpoints expect `application/json` (except file uploads which use `multipart/form-data`)
2. **Login endpoint** is the only endpoint that accepts both JSON and form-encoded data
3. All datetime fields are in ISO 8601 format with UTC timezone
4. UUIDs are used for all resource IDs
5. Pagination uses `skip` and `limit` query parameters
6. All responses follow the standardized format shown above
