# Response Structure Improvement

## Update Description
Refactored the **Customer List** and **Customer Search** endpoints to provide a cleaner JSON structure.

## Before
The `data` field contained a nested object `{"customers": [], "total": ...}` for list endpoints.

## After
The `data` field now contains the **List** directly.
Pagination and search metadata are moved to the `meta` field.

### New Format Example
```json
{
  "success": true,
  "status_code": 200,
  "message": "Customers retrieved successfully",
  "data": [
      { "id": "1", "name": "Customer A", ... },
      { "id": "2", "name": "Customer B", ... }
  ],
  "meta": {
      "total": 50,
      "skip": 0,
      "limit": 10
  }
}
```

This applies to:
- `GET /api/v1/customers`
- `GET /api/v1/customers/search/by-location`
