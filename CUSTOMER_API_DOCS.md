# Customer API Integration Guide

This document details the endpoints for managing customers.

## Base URL
`http://localhost:8000/api/v1`

## Authentication
**Required**: Bearer Token in Authorization header.
`Authorization: Bearer <access_token>`

---

## 1. List Customers
Retrieve a paginated list of customers with optional searching and filtering.

- **Endpoint:** `/customers`
- **Method:** `GET`

### Query Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | int | 0 | Pagination offset. |
| `limit` | int | 100 | Items per page (max 100). |
| `search` | string | null | Search by name, email, or phone. |
| `is_active` | bool | null | Filter by status (`true` or `false`). |

### Request Example
`GET /customers?skip=0&limit=10&search=john`

### Success Response (200 OK)
```json
{
  "success": true,
  "status_code": 200,
  "message": "Customers retrieved successfully",
  "data": [
    {
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+1234567890",
      "address": "123 Main St",
      "id": "uuid-string...",
      "is_active": true,
      "created_at": "2026-01-01T10:00:00Z"
      ...
    }
  ],
  "meta": {
    "total": 50,
    "skip": 0,
    "limit": 10
  }
}
```

---

## 2. Create Customer
Create a new customer profile.

- **Endpoint:** `/customers`
- **Method:** `POST`
- **Content-Type:** `application/json`

### Request Body
| Field | Type | Required | constraints |
|-------|------|----------|-------------|
| `name` | string | ✅ Yes | Min 1, Max 255 chars |
| `email` | string | ❌ No | Valid email |
| `phone` | string | ❌ No | Max 50 chars |
| `address` | string | ❌ No | Max 500 chars |
| `city` | string | ❌ No | Max 100 chars |
| `state` | string | ❌ No | Max 100 chars |
| `postal_code` | string | ❌ No | Max 20 chars |
| `country` | string | ❌ No | Max 100 chars |
| `notes` | string | ❌ No | Max 1000 chars |
| `latitude` | float | ❌ No | -90 to 90 |
| `longitude` | float | ❌ No | -180 to 180 |
| `is_active` | bool | ❌ No | Default: true |

### Example Request
```json
{
  "name": "Alice Smith",
  "email": "alice@example.com",
  "phone": "555-0199",
  "city": "New York",
  "notes": "VIP Customer"
}
```

### Success Response (201 Created)
```json
{
  "success": true,
  "status_code": 201,
  "message": "Customer created successfully",
  "data": { ...customer_object... }
}
```

---

## 3. Update Customer
Update an existing customer's details.

- **Endpoint:** `/customers/{customer_id}`
- **Method:** `PUT`
- **Content-Type:** `application/json`

### Request Body
All fields are optional.
- All fields from Create (name, email, phone, etc.)
- `is_active` (boolean): Set to `false` to deactivate.

### Example Request
```json
{
  "phone": "555-9999",
  "is_active": false
}
```

### Success Response (200 OK)
```json
{
  "success": true,
  "status_code": 200,
  "message": "Customer updated successfully",
  "data": { ...updated_object... }
}
```

---

## 4. Get Customer Details
Get a single customer by ID.

- **Endpoint:** `/customers/{customer_id}`
- **Method:** `GET`

### Success Response (200 OK)
```json
{
  "success": true,
  "status_code": 200,
  "message": "Customer retrieved successfully",
  "data": { ...customer_object... }
}
```

---

## 5. Delete Customer
Delete a customer account.

- **Endpoint:** `/customers/{customer_id}`
- **Method:** `DELETE`

### Query Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `permanent` | bool | false | If `true`, hard delete from DB. If `false`, soft delete (mark deleted). |

### Success Response (200 OK)
```json
{
  "success": true,
  "status_code": 200,
  "message": "Customer deleted successfully",
  "data": {
    "id": "uuid-string..."
  }
}
```

---

## 6. Search by Location
Find customers near a specific coordinate (Geospatial search).

- **Endpoint:** `/customers/search/by-location`
- **Method:** `GET`

### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `latitude` | float | ✅ Yes | Center Lat (-90 to 90) |
| `longitude` | float | ✅ Yes | Center Long (-180 to 180) |
| `radius_km` | float | ❌ No | Radius in KM (Default: 10) |
| `limit` | int | ❌ No | Max results (Default: 100) |

### Request Example
`GET /customers/search/by-location?latitude=40.7128&longitude=-74.0060&radius_km=5`

### Success Response (200 OK)
```json
{
  "success": true,
  "status_code": 200,
  "message": "Customers retrieved successfully",
  "data": [
    {
      "name": "Nearby Customer",
      "address": "456 Local Ln",
      "latitude": 40.715,
      "longitude": -74.009,
      ...
    }
  ],
  "meta": {
    "total": 5,
    "center": { "latitude": 40.7128, "longitude": -74.006 },
    "radius_km": 5
  }
}
```
