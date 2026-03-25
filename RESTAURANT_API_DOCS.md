# Restaurant API Integration Guide

This document provides detailed integration guidelines for Restaurant Create and Update operations.

## Base URL
`http://localhost:8000/api/v1`

## Authentication
All endpoints require a valid Bearer Token in the Authorization header.
`Authorization: Bearer <access_token>`

---

## 1. Create Restaurant

Create a new restaurant profile.

- **Endpoint:** `/restaurants`
- **Method:** `POST`
- **Content-Type:** `application/json`

### Request Body (JSON)

| Field | Type | Required | Description | Validation / Constraints |
|-------|------|----------|-------------|--------------------------|
| **slug** | string | ✅ Yes | Unique URL identifier | `^[a-z0-9-]+$`. Lowercase, numbers, hyphens only. |
| **name** | string | ✅ Yes | Display name | Min 2, Max 200 chars |
| **business_name** | string | ✅ Yes | Legal entity name | Min 2, Max 200 chars |
| **email** | string | ✅ Yes | Contact email | Valid email format |
| **phone** | string | ✅ Yes | Contact phone | Min 10, Max 20 chars |
| **business_type** | string | ❌ No | Type of business | Enum: `fine_dining`, `casual_dining`, `cafe`, `fast_food`, etc. |
| **cuisine_type** | array[string] | ❌ No | List of cuisines | Array of strings |
| **description** | string | ❌ No | Short bio | |
| **alternate_phone** | string | ❌ No | Backup phone | Max 20 chars |
| **address** | string | ❌ No | Street address | |
| **city** | string | ❌ No | City name | |
| **state** | string | ❌ No | State name | |
| **country** | string | ❌ No | Country name | Default: "India" |
| **postal_code** | string | ❌ No | ZIP/Postal code | |
| **gstin** | string | ❌ No | GST Number | Max 15 chars |
| **fssai_license** | string | ❌ No | FSSAI License | Max 14 chars |
| **pan_number** | string | ❌ No | PAN Number | Max 10 chars |
| **opening_time** | string | ❌ No | Opening time | Format `HH:MM` (24h) |
| **closing_time** | string | ❌ No | Closing time | Format `HH:MM` (24h) |
| **payment_methods_allowed** | array[string] | ❌ No | Allowed payments | `["cash", "card", "upi", "wallet", "online"]` |

*(Note: Other optional settings fields like tax rates, toggles, etc. can also be passed. See Update section for full list of settings)*

### Example Request
```json
{
  "name": "Spicy Delights",
  "business_name": "Spicy Delights Pvt Ltd",
  "slug": "spicy-delights-pune",
  "email": "contact@spicydelights.com",
  "phone": "+919876543210",
  "city": "Pune",
  "business_type": "casual_dining",
  "cuisine_type": ["North Indian", "Chinese"]
}
```

### Success Response (201 Created)
```json
{
  "success": true,
  "status_code": 201,
  "message": "Restaurant created successfully",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "slug": "spicy-delights-pune",
    "name": "Spicy Delights",
    "created_at": "2026-01-01T10:00:00Z",
    ...
  }
}
```

---

## 2. Update Restaurant

Update an existing restaurant's details and settings.

- **Endpoint:** `/restaurants/{restaurant_id}`
- **Method:** `PUT`
- **Content-Type:** `application/json`

### Request Body (JSON)
All fields are optional. Send only the fields you want to update.

#### **Basic Info & Branding**
| Field | Type | Description |
|-------|------|-------------|
| **name** | string | Display name |
| **business_name** | string | Legal name |
| **description** | string | Bio |
| **logo** | string | URL only |
| **banner_image** | string | URL only |
| **primary_color** | string | Hex code (e.g. `#FF5733`) |
| **accent_color** | string | Hex code |

#### **Contact & Location**
| Field | Type | Description |
|-------|------|-------------|
| **email** | string | |
| **phone** | string | |
| **address** | string | |
| **city** | string | |
| **state** | string | |
| **postal_code** | string | |

#### **Legal & Tax**
| Field | Type | Description |
|-------|------|-------------|
| **gstin** | string | GST Number |
| **enable_gst** | boolean | Toggle GST calculation |
| **cgst_rate** | float | CGST % |
| **sgst_rate** | float | SGST % |
| **service_charge_percentage** | float | Service charge % |

#### **Operations & Hours**
| Field | Type | Description |
|-------|------|-------------|
| **opening_time** | string | `HH:MM` |
| **closing_time** | string | `HH:MM` |
| **is_24_hours** | boolean | |
| **holiday_mode** | boolean | Temporarily close restaurant |
| **timezone** | string | e.g. "Asia/Kolkata" |
| **currency** | string | e.g. "INR" |

#### **Ordering & Service**
| Field | Type | Description |
|-------|------|-------------|
| **enable_online_ordering** | boolean | |
| **enable_dine_in** | boolean | |
| **enable_takeaway** | boolean | |
| **enable_delivery** | boolean | |
| **delivery_radius** | float | In kilometers |
| **minimum_order_value** | float | |

#### **Kitchen & Receipt**
| Field | Type | Description |
|-------|------|-------------|
| **enable_kot** | boolean | Enable Kitchen Order Tickets |
| **enable_kds** | boolean | Enable Kitchen Display System |
| **auto_accept_orders** | boolean | |
| **preparation_time_buffer** | int | Minutes |
| **receipt_header** | string | Text on top of bill |
| **receipt_footer** | string | Text on bottom of bill |

### Example Request
```json
{
  "description": "Best food in town",
  "opening_time": "11:00",
  "closing_time": "23:00",
  "enable_online_ordering": true,
  "cgst_rate": 2.5,
  "sgst_rate": 2.5,
  "primary_color": "#E63946"
}
```

### Success Response (200 OK)
```json
{
  "success": true,
  "status_code": 200,
  "message": "Restaurant updated successfully",
  "data": { ...updated_object... }
}
```

## Error Codes

| Code | HTTP Status | Meaning |
|------|-------------|---------|
| `SLUG_EXISTS` | 400 | The slug is already taken by another restaurant. |
| `INTEGRITY_ERROR` | 400 | Email or other unique constraint violation. |
| `NOT_FOUND` | 404 | Restaurant ID does not exist. |
| `VALIDATION_ERROR` | 422 | Invalid data format (e.g. bad email, wrong time format). |
