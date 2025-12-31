# API Response Format - Industry Standards

## Overview

All API endpoints follow a **consistent, standardized response format** that provides clear status indicators, error handling, and metadata support for pagination and additional information.

---

## Response Structure

### Success Response

```json
{
  "status": "success",
  "message": "Operation successful",
  "data": {
    // Response data (object, array, or any JSON-serializable value)
  },
  "error": null,
  "meta": {
    // Optional metadata for pagination
    "page": 1,
    "limit": 20,
    "total": 100,
    "total_pages": 5
  },
  "timestamp": "2024-12-31T10:30:45.123456Z"
}
```

### Error Response

```json
{
  "status": "error",
  "message": "User-friendly error message",
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "User-friendly error message",
    "details": "Technical details for debugging",
    "field": "fieldName"  // Optional: for validation errors
  },
  "timestamp": "2024-12-31T10:30:45.123456Z"
}
```

---

## Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | **"success"** or **"error"** - Indicates operation result |
| `message` | string | Human-readable description of the result |
| `data` | any | Response payload (null for errors) |
| `error` | object/null | Error details (null for success) |
| `meta` | object/null | Metadata for pagination or additional info (optional) |
| `timestamp` | string | ISO 8601 UTC timestamp of the response |

### Error Object Structure

| Field | Type | Description |
|-------|------|-------------|
| `code` | string | Machine-readable error code (e.g., "INVALID_CREDENTIALS") |
| `message` | string | User-friendly error message |
| `details` | string/null | Technical details for debugging |
| `field` | string/null | Specific field that caused error (for validation) |

### Meta Object Structure (Pagination)

| Field | Type | Description |
|-------|------|-------------|
| `page` | integer | Current page number (1-indexed) |
| `limit` | integer | Items per page |
| `total` | integer | Total number of items |
| `total_pages` | integer | Total number of pages |

---

## Response Examples

### 1. Simple Success Response

**Endpoint:** `POST /api/v1/auth/login`

```json
{
  "status": "success",
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  },
  "error": null,
  "timestamp": "2024-12-31T10:30:45.123456Z"
}
```

### 2. Paginated List Response

**Endpoint:** `GET /api/v1/products?page=1&limit=20`

```json
{
  "status": "success",
  "message": "Products retrieved successfully",
  "data": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Butter Chicken",
      "price": 45000,
      "is_available": true
    },
    {
      "id": "223e4567-e89b-12d3-a456-426614174001",
      "name": "Paneer Tikka",
      "price": 38000,
      "is_available": true
    }
  ],
  "error": null,
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "total_pages": 8
  },
  "timestamp": "2024-12-31T10:35:20.456789Z"
}
```

### 3. Single Resource Response

**Endpoint:** `GET /api/v1/restaurants/{id}`

```json
{
  "status": "success",
  "message": "Restaurant retrieved successfully",
  "data": {
    "id": "3c2835af-1ff2-4714-8191-c4c1f5b2246f",
    "name": "The Grand Dine",
    "business_name": "Grand Dine Pvt Ltd",
    "email": "contact@granddine.com",
    "phone": "+91-9876543200",
    "city": "Bangalore",
    "state": "Karnataka",
    "is_active": true,
    "created_at": "2024-01-15T08:30:00.000Z"
  },
  "error": null,
  "timestamp": "2024-12-31T10:40:10.789012Z"
}
```

### 4. Create/Update Success Response

**Endpoint:** `POST /api/v1/customers`

```json
{
  "status": "success",
  "message": "Customer created successfully",
  "data": {
    "id": "456e7890-e89b-12d3-a456-426614174002",
    "name": "Amit Verma",
    "email": "amit@example.com",
    "phone": "+91-9876543230",
    "loyalty_points": 0,
    "created_at": "2024-12-31T10:45:00.000Z"
  },
  "error": null,
  "timestamp": "2024-12-31T10:45:00.123456Z"
}
```

### 5. Authentication Error

**Endpoint:** `POST /api/v1/auth/login`

```json
{
  "status": "error",
  "message": "Login failed",
  "data": null,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Login failed",
    "details": "Invalid email or password, or account is locked due to too many failed attempts",
    "field": null
  },
  "timestamp": "2024-12-31T10:50:00.123456Z"
}
```

### 6. Validation Error

**Endpoint:** `POST /api/v1/users`

```json
{
  "status": "error",
  "message": "Validation failed",
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": "One or more fields contain invalid data",
    "errors": [
      {
        "field": "email",
        "message": "Invalid email format"
      },
      {
        "field": "phone",
        "message": "Phone number must start with +"
      }
    ]
  },
  "timestamp": "2024-12-31T10:55:00.123456Z"
}
```

### 7. Not Found Error

**Endpoint:** `GET /api/v1/products/{invalid-id}`

```json
{
  "status": "error",
  "message": "Product not found",
  "data": null,
  "error": {
    "code": "NOT_FOUND",
    "message": "Product not found",
    "details": "No product found with the specified ID",
    "field": null
  },
  "timestamp": "2024-12-31T11:00:00.123456Z"
}
```

### 8. Duplicate Entry Error

**Endpoint:** `POST /api/v1/restaurants`

```json
{
  "status": "error",
  "message": "Restaurant creation failed",
  "data": null,
  "error": {
    "code": "DUPLICATE_ENTRY",
    "message": "Restaurant creation failed",
    "details": "A restaurant with slug 'the-grand-dine' already exists",
    "field": "slug"
  },
  "timestamp": "2024-12-31T11:05:00.123456Z"
}
```

### 9. Authorization Error

**Endpoint:** `PUT /api/v1/restaurants/{id}`

```json
{
  "status": "error",
  "message": "Access denied",
  "data": null,
  "error": {
    "code": "FORBIDDEN",
    "message": "Access denied",
    "details": "You don't have permission to modify this restaurant",
    "field": null
  },
  "timestamp": "2024-12-31T11:10:00.123456Z"
}
```

### 10. Internal Server Error

**Endpoint:** `Any endpoint`

```json
{
  "status": "error",
  "message": "Internal server error",
  "data": null,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Internal server error",
    "details": "An unexpected error occurred. Please try again later.",
    "field": null
  },
  "timestamp": "2024-12-31T11:15:00.123456Z"
}
```

---

## Common Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `INVALID_CREDENTIALS` | 401 | Invalid username/password |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication token |
| `FORBIDDEN` | 403 | User doesn't have permission |
| `NOT_FOUND` | 404 | Resource not found |
| `DUPLICATE_ENTRY` | 409 | Resource already exists |
| `VALIDATION_ERROR` | 422 | Input validation failed |
| `INTERNAL_ERROR` | 500 | Server error |
| `DATABASE_ERROR` | 500 | Database operation failed |
| `INVALID_INPUT` | 400 | Invalid request data |
| `MISSING_PARAMETER` | 400 | Required parameter missing |

---

## HTTP Status Code Mapping

| HTTP Status | Status Field | Use Case |
|-------------|--------------|----------|
| 200 | success | Successful GET, PUT, PATCH |
| 201 | success | Successful POST (created) |
| 204 | success | Successful DELETE (no content) |
| 400 | error | Bad request / validation error |
| 401 | error | Authentication failed |
| 403 | error | Authorization failed |
| 404 | error | Resource not found |
| 409 | error | Conflict / duplicate entry |
| 422 | error | Unprocessable entity |
| 500 | error | Internal server error |

---

## Helper Functions

The system provides helper functions in `app/core/response.py`:

### 1. `success_response()`

```python
from app.core.response import success_response

return success_response(
    message="Operation successful",
    data={"id": "123", "name": "Example"},
    meta={"page": 1, "total": 100}  # Optional
)
```

### 2. `error_response()`

```python
from app.core.response import error_response

return error_response(
    message="Operation failed",
    error_code="NOT_FOUND",
    error_details="Resource not found",
    field="id"  # Optional
)
```

### 3. `paginated_response()`

```python
from app.core.response import paginated_response

return paginated_response(
    message="Items retrieved successfully",
    data=items_list,
    page=1,
    limit=20,
    total=150
)
```

### 4. `validation_error_response()`

```python
from app.core.response import validation_error_response

return validation_error_response(
    message="Validation failed",
    errors=[
        {"field": "email", "message": "Invalid format"},
        {"field": "phone", "message": "Required field"}
    ]
)
```

---

## Best Practices

1. **Always use helper functions** - Don't manually create response dictionaries
2. **Provide clear messages** - Make error messages user-friendly
3. **Include error codes** - Use consistent, uppercase error codes
4. **Add technical details** - Include debugging info in `error.details`
5. **Use appropriate HTTP status codes** - Match the response status
6. **Include timestamps** - Automatically added to all responses
7. **Support pagination** - Use `meta` for list endpoints
8. **Validate input** - Return proper validation errors with field names

---

## Benefits

✅ **Consistency** - All endpoints follow the same format  
✅ **Clear Status** - Easy to identify success/failure  
✅ **Error Handling** - Structured error information  
✅ **Machine & Human Readable** - Error codes + messages  
✅ **Debugging** - Technical details included  
✅ **Pagination Support** - Built-in metadata  
✅ **Timestamps** - Track when responses were generated  
✅ **Industry Standard** - Follows REST API best practices

---

## Migration Notes

**Breaking Changes:**
- `success` field renamed to `status` (values: "success" or "error")
- `error` object structure enhanced with `message` and `field` support
- `timestamp` added to all responses
- `meta` support added for pagination

**Backward Compatibility:**
- All endpoints updated to use the new format
- Test scripts should check `status === "success"` instead of `success === true`
- Client applications need to update response parsing logic

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-12-31 | Initial standardized format implementation |

---

**Note:** This format follows industry best practices from Google, Stripe, and Microsoft Azure APIs.
