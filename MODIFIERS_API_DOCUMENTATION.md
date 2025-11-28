# Modifiers API Documentation

Complete API reference for Modifier and Modifier Options management endpoints.

## Base URL
```
http://localhost:8000/api/v1/modifiers
```

## Authentication
All endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

---

## Overview

Modifiers allow customers to customize products with add-ons, size options, or ingredient choices. Each modifier can have multiple options with individual pricing.

### Use Cases
- **Size Selection:** Small, Medium, Large (single choice)
- **Add-ons:** Extra cheese, bacon, avocado (multiple choices)
- **Ingredient Options:** No onions, extra sauce (multiple choices)
- **Temperature:** Hot, Cold, Room temperature (single choice)
- **Cooking Level:** Rare, Medium, Well-done (single choice)

### Modifier Types
- `single` - Customer can select only one option (e.g., size)
- `multiple` - Customer can select multiple options (e.g., toppings)

---

## Endpoints Overview

### Modifiers
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Create a new modifier |
| GET | `/` | List all modifiers with pagination |
| GET | `/{modifier_id}` | Get a specific modifier by ID |
| DELETE | `/{modifier_id}` | Delete a modifier |

### Modifier Options
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/{modifier_id}/options` | Create a new option for a modifier |
| GET | `/{modifier_id}/options` | List all options for a modifier |
| DELETE | `/api/v1/modifier-options/{option_id}` | Delete a modifier option |

---

## Modifiers

### 1. Create Modifier

Create a new modifier group.

#### Endpoint
```http
POST /api/v1/modifiers/
```

#### Headers
```
Authorization: Bearer <token>
Content-Type: application/json
```

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Modifier name (1-100 chars) |
| type | string | Yes | `single` or `multiple` |
| category | string | No | Category name (default: "add-ons") |
| required | boolean | No | Whether selection is required (default: false) |
| min_selections | integer | No | Minimum selections (default: 0) |
| max_selections | integer | No | Maximum selections (null = unlimited) |

#### Example Request
```bash
curl -X POST "http://localhost:8000/api/v1/modifiers/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Size",
    "type": "single",
    "category": "sizes",
    "required": true,
    "min_selections": 1,
    "max_selections": 1
  }'
```

#### Example Request - Multiple Selection
```bash
curl -X POST "http://localhost:8000/api/v1/modifiers/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Extra Toppings",
    "type": "multiple",
    "category": "add-ons",
    "required": false,
    "min_selections": 0,
    "max_selections": 5
  }'
```

#### Success Response (201 Created)
```json
{
  "id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
  "name": "Size",
  "type": "single",
  "category": "sizes",
  "required": true,
  "min_selections": 1,
  "max_selections": 1,
  "options": [],
  "created_at": "2025-11-24T10:30:00Z",
  "updated_at": "2025-11-24T10:30:00Z"
}
```

---

### 2. List All Modifiers

Retrieve all modifiers with pagination and optional filtering.

#### Endpoint
```http
GET /api/v1/modifiers/
```

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | integer | 1 | Page number (≥1) |
| page_size | integer | 10 | Items per page (1-100) |
| category | string | null | Filter by category |

#### Example Request
```bash
# Get all modifiers
curl -X GET "http://localhost:8000/api/v1/modifiers/?page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Filter by category
curl -X GET "http://localhost:8000/api/v1/modifiers/?category=sizes" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Success Response (200 OK)
```json
{
  "success": true,
  "message": "Modifiers retrieved successfully",
  "data": [
    {
      "id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
      "name": "Size",
      "type": "single",
      "category": "sizes",
      "required": true,
      "min_selections": 1,
      "max_selections": 1,
      "options": [
        {
          "id": "opt-001",
          "modifier_id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
          "name": "Small",
          "price": 0,
          "available": true,
          "sort_order": 1,
          "created_at": "2025-11-24T10:31:00Z",
          "updated_at": "2025-11-24T10:31:00Z"
        },
        {
          "id": "opt-002",
          "modifier_id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
          "name": "Medium",
          "price": 200,
          "available": true,
          "sort_order": 2,
          "created_at": "2025-11-24T10:32:00Z",
          "updated_at": "2025-11-24T10:32:00Z"
        },
        {
          "id": "opt-003",
          "modifier_id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
          "name": "Large",
          "price": 400,
          "available": true,
          "sort_order": 3,
          "created_at": "2025-11-24T10:33:00Z",
          "updated_at": "2025-11-24T10:33:00Z"
        }
      ],
      "created_at": "2025-11-24T10:30:00Z",
      "updated_at": "2025-11-24T10:30:00Z"
    },
    {
      "id": "b2c3d4e5-f6a7-4b5c-8d9e-0f1a2b3c4d5e",
      "name": "Extra Toppings",
      "type": "multiple",
      "category": "add-ons",
      "required": false,
      "min_selections": 0,
      "max_selections": 5,
      "options": [],
      "created_at": "2025-11-24T10:35:00Z",
      "updated_at": "2025-11-24T10:35:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_items": 2,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

---

### 3. Get Modifier by ID

Retrieve a specific modifier with all its options.

#### Endpoint
```http
GET /api/v1/modifiers/{modifier_id}
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| modifier_id | string (UUID) | Yes | Modifier unique identifier |

#### Example Request
```bash
curl -X GET "http://localhost:8000/api/v1/modifiers/a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Success Response (200 OK)
```json
{
  "id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
  "name": "Size",
  "type": "single",
  "category": "sizes",
  "required": true,
  "min_selections": 1,
  "max_selections": 1,
  "options": [
    {
      "id": "opt-001",
      "modifier_id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
      "name": "Small",
      "price": 0,
      "available": true,
      "sort_order": 1,
      "created_at": "2025-11-24T10:31:00Z",
      "updated_at": "2025-11-24T10:31:00Z"
    },
    {
      "id": "opt-002",
      "modifier_id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
      "name": "Medium",
      "price": 200,
      "available": true,
      "sort_order": 2,
      "created_at": "2025-11-24T10:32:00Z",
      "updated_at": "2025-11-24T10:32:00Z"
    }
  ],
  "created_at": "2025-11-24T10:30:00Z",
  "updated_at": "2025-11-24T10:30:00Z"
}
```

#### Error Response (404 Not Found)
```json
{
  "detail": "Modifier with id a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d not found"
}
```

---

### 4. Delete Modifier

Delete a modifier and all its options (cascade delete).

#### Endpoint
```http
DELETE /api/v1/modifiers/{modifier_id}
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| modifier_id | string (UUID) | Yes | Modifier unique identifier |

#### Example Request
```bash
curl -X DELETE "http://localhost:8000/api/v1/modifiers/a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Success Response (204 No Content)
```
No response body
```

#### Delete Behavior
- Modifier record removed from database
- All associated modifier options automatically deleted (cascade)
- Product associations (ProductModifier) removed

---

## Modifier Options

### 5. Create Modifier Option

Create a new option for an existing modifier.

#### Endpoint
```http
POST /api/v1/modifiers/{modifier_id}/options
```

#### Headers
```
Authorization: Bearer <token>
Content-Type: application/json
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| modifier_id | string (UUID) | Yes | Parent modifier ID |

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Option name (1-100 chars) |
| price | integer | No | Additional price in cents (default: 0) |
| available | boolean | No | Availability status (default: true) |
| sort_order | integer | No | Display order (default: 0) |

**Note:** `modifier_id` field in request body is ignored; path parameter is used instead.

#### Example Request
```bash
curl -X POST "http://localhost:8000/api/v1/modifiers/a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d/options" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Large",
    "price": 400,
    "available": true,
    "sort_order": 3
  }'
```

#### Example Request - Free Option
```bash
curl -X POST "http://localhost:8000/api/v1/modifiers/a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d/options" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "No Ice",
    "price": 0,
    "available": true,
    "sort_order": 1
  }'
```

#### Success Response (201 Created)
```json
{
  "id": "opt-003",
  "modifier_id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
  "name": "Large",
  "price": 400,
  "available": true,
  "sort_order": 3,
  "created_at": "2025-11-24T10:33:00Z",
  "updated_at": "2025-11-24T10:33:00Z"
}
```

#### Error Response (404 Not Found)
```json
{
  "detail": "Modifier with id a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d not found"
}
```

---

### 6. List Modifier Options

Retrieve all options for a specific modifier with pagination.

#### Endpoint
```http
GET /api/v1/modifiers/{modifier_id}/options
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| modifier_id | string (UUID) | Yes | Parent modifier ID |

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | integer | 1 | Page number (≥1) |
| page_size | integer | 10 | Items per page (1-100) |

#### Example Request
```bash
curl -X GET "http://localhost:8000/api/v1/modifiers/a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d/options?page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Success Response (200 OK)
```json
{
  "success": true,
  "message": "Modifier options retrieved successfully",
  "data": [
    {
      "id": "opt-001",
      "modifier_id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
      "name": "Small",
      "price": 0,
      "available": true,
      "sort_order": 1,
      "created_at": "2025-11-24T10:31:00Z",
      "updated_at": "2025-11-24T10:31:00Z"
    },
    {
      "id": "opt-002",
      "modifier_id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
      "name": "Medium",
      "price": 200,
      "available": true,
      "sort_order": 2,
      "created_at": "2025-11-24T10:32:00Z",
      "updated_at": "2025-11-24T10:32:00Z"
    },
    {
      "id": "opt-003",
      "modifier_id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
      "name": "Large",
      "price": 400,
      "available": true,
      "sort_order": 3,
      "created_at": "2025-11-24T10:33:00Z",
      "updated_at": "2025-11-24T10:33:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_items": 3,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

#### Notes
- Options are automatically sorted by `sort_order` field
- Use `sort_order` to control display sequence in UI

---

### 7. Delete Modifier Option

Delete a specific modifier option.

#### Endpoint
```http
DELETE /api/v1/modifier-options/{option_id}
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| option_id | string (UUID) | Yes | Option unique identifier |

#### Example Request
```bash
curl -X DELETE "http://localhost:8000/api/v1/modifier-options/opt-003" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Success Response (204 No Content)
```
No response body
```

#### Error Response (404 Not Found)
```json
{
  "detail": "Modifier option with id opt-003 not found"
}
```

---

## Common Use Cases

### 1. Size Selection (Single Choice, Required)

**Create Modifier:**
```bash
curl -X POST "http://localhost:8000/api/v1/modifiers/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Size",
    "type": "single",
    "category": "sizes",
    "required": true,
    "min_selections": 1,
    "max_selections": 1
  }'
```

**Add Options:**
```bash
# Small (base price, no extra charge)
curl -X POST "http://localhost:8000/api/v1/modifiers/$MODIFIER_ID/options" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Small", "price": 0, "sort_order": 1}'

# Medium (+$2.00)
curl -X POST "http://localhost:8000/api/v1/modifiers/$MODIFIER_ID/options" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Medium", "price": 200, "sort_order": 2}'

# Large (+$4.00)
curl -X POST "http://localhost:8000/api/v1/modifiers/$MODIFIER_ID/options" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Large", "price": 400, "sort_order": 3}'
```

---

### 2. Extra Toppings (Multiple Choice, Optional)

**Create Modifier:**
```bash
curl -X POST "http://localhost:8000/api/v1/modifiers/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Extra Toppings",
    "type": "multiple",
    "category": "add-ons",
    "required": false,
    "min_selections": 0,
    "max_selections": 5
  }'
```

**Add Options:**
```bash
# Each topping costs $1.50
curl -X POST "http://localhost:8000/api/v1/modifiers/$MODIFIER_ID/options" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Extra Cheese", "price": 150, "sort_order": 1}'

curl -X POST "http://localhost:8000/api/v1/modifiers/$MODIFIER_ID/options" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Bacon", "price": 150, "sort_order": 2}'

curl -X POST "http://localhost:8000/api/v1/modifiers/$MODIFIER_ID/options" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Avocado", "price": 150, "sort_order": 3}'
```

---

### 3. Ingredient Customization (Multiple Choice, Free)

**Create Modifier:**
```bash
curl -X POST "http://localhost:8000/api/v1/modifiers/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Customize",
    "type": "multiple",
    "category": "customization",
    "required": false,
    "min_selections": 0,
    "max_selections": null
  }'
```

**Add Options:**
```bash
# Free customizations
curl -X POST "http://localhost:8000/api/v1/modifiers/$MODIFIER_ID/options" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "No Onions", "price": 0, "sort_order": 1}'

curl -X POST "http://localhost:8000/api/v1/modifiers/$MODIFIER_ID/options" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Extra Sauce", "price": 0, "sort_order": 2}'

curl -X POST "http://localhost:8000/api/v1/modifiers/$MODIFIER_ID/options" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "No Pickles", "price": 0, "sort_order": 3}'
```

---

### 4. Temperature Selection (Single Choice, Required)

**Create Modifier:**
```bash
curl -X POST "http://localhost:8000/api/v1/modifiers/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Temperature",
    "type": "single",
    "category": "preferences",
    "required": true,
    "min_selections": 1,
    "max_selections": 1
  }'
```

**Add Options:**
```bash
curl -X POST "http://localhost:8000/api/v1/modifiers/$MODIFIER_ID/options" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Hot", "price": 0, "sort_order": 1}'

curl -X POST "http://localhost:8000/api/v1/modifiers/$MODIFIER_ID/options" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Cold", "price": 0, "sort_order": 2}'

curl -X POST "http://localhost:8000/api/v1/modifiers/$MODIFIER_ID/options" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Room Temperature", "price": 0, "sort_order": 3}'
```

---

## Pricing Examples

### Price Calculation
Prices are stored in **cents** (integer).

| Display Price | API Value (cents) |
|---------------|-------------------|
| Free | 0 |
| $0.50 | 50 |
| $1.00 | 100 |
| $1.50 | 150 |
| $2.00 | 200 |
| $5.00 | 500 |
| $10.00 | 1000 |

### Example Order Calculation

**Base Product:** Burger - $12.99 (1299 cents)

**Selected Modifiers:**
- Size: Large (+$4.00 = 400 cents)
- Extra Toppings: Cheese (+$1.50 = 150 cents), Bacon (+$1.50 = 150 cents)

**Total Calculation:**
```
Base Price:     1299 cents ($12.99)
Size (Large):   + 400 cents ($4.00)
Cheese:         + 150 cents ($1.50)
Bacon:          + 150 cents ($1.50)
------------------------------------
Total:          1999 cents ($19.99)
```

---

## Validation Rules

### Modifier Validation

| Field | Rule | Error |
|-------|------|-------|
| name | 1-100 characters | String too short/long |
| type | Must be "single" or "multiple" | Invalid type |
| min_selections | ≥ 0 | Must be non-negative |
| max_selections | ≥ min_selections or null | Invalid range |
| required=true | Must have min_selections ≥ 1 | Logic error |

### Option Validation

| Field | Rule | Error |
|-------|------|-------|
| name | 1-100 characters | String too short/long |
| price | ≥ 0 | Must be non-negative |
| sort_order | Integer | Invalid type |
| modifier_id | Must exist | Foreign key constraint |

### Business Logic Rules

1. **Single Selection Required:**
   - `type = "single"`
   - `required = true`
   - `min_selections = 1`
   - `max_selections = 1`

2. **Multiple Selection Optional:**
   - `type = "multiple"`
   - `required = false`
   - `min_selections = 0`
   - `max_selections = null` (unlimited) or specific number

3. **Multiple Selection Required:**
   - `type = "multiple"`
   - `required = true`
   - `min_selections ≥ 1`
   - `max_selections ≥ min_selections`

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid modifier type. Must be 'single' or 'multiple'"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 404 Not Found
```json
{
  "detail": "Modifier with id a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    },
    {
      "loc": ["body", "type"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Best Practices

### Modifier Design

✅ **DO:**
- Use descriptive, customer-friendly names
- Set appropriate min/max selections
- Order options logically with sort_order
- Use categories to group related modifiers
- Set required=true for mandatory choices
- Provide at least one free option for required modifiers

❌ **DON'T:**
- Create overly complex modifier combinations
- Set max_selections lower than min_selections
- Use technical names customers won't understand
- Forget to set availability status
- Create duplicate modifier names
- Leave required modifiers without options

### Option Design

✅ **DO:**
- Use clear, concise option names
- Set prices in cents (multiply by 100)
- Use sort_order for logical sequencing
- Mark unavailable options instead of deleting
- Provide free base options when possible
- Group similar options in same modifier

❌ **DON'T:**
- Use decimal prices (use cents)
- Create too many options (>10 per modifier)
- Forget to update availability
- Delete options that have order history
- Use negative prices
- Create duplicate option names in same modifier

### Category Usage

Common category examples:
- `sizes` - Size selections
- `add-ons` - Extra ingredients/toppings
- `customization` - Ingredient modifications
- `preferences` - Temperature, spice level
- `cooking` - Doneness, preparation style
- `dietary` - Dietary restrictions/preferences

---

## Integration Examples

### React/TypeScript
```typescript
interface Modifier {
  id: string;
  name: string;
  type: 'single' | 'multiple';
  category: string;
  required: boolean;
  min_selections: number;
  max_selections: number | null;
  options: ModifierOption[];
}

interface ModifierOption {
  id: string;
  modifier_id: string;
  name: string;
  price: number;
  available: boolean;
  sort_order: number;
}

async function createModifier(data: {
  name: string;
  type: 'single' | 'multiple';
  category?: string;
  required?: boolean;
  min_selections?: number;
  max_selections?: number | null;
}): Promise<Modifier> {
  const response = await fetch('http://localhost:8000/api/v1/modifiers/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  });
  
  return response.json();
}

async function addOption(
  modifierId: string,
  data: {
    name: string;
    price?: number;
    available?: boolean;
    sort_order?: number;
  }
): Promise<ModifierOption> {
  const response = await fetch(
    `http://localhost:8000/api/v1/modifiers/${modifierId}/options`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    }
  );
  
  return response.json();
}
```

### Python
```python
import requests

class ModifierAPI:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def create_modifier(self, name: str, modifier_type: str, **kwargs):
        """Create a new modifier."""
        data = {
            'name': name,
            'type': modifier_type,
            **kwargs
        }
        response = requests.post(
            f'{self.base_url}/api/v1/modifiers/',
            headers=self.headers,
            json=data
        )
        return response.json()
    
    def add_option(self, modifier_id: str, name: str, price: int = 0, **kwargs):
        """Add an option to a modifier."""
        data = {
            'name': name,
            'price': price,
            **kwargs
        }
        response = requests.post(
            f'{self.base_url}/api/v1/modifiers/{modifier_id}/options',
            headers=self.headers,
            json=data
        )
        return response.json()
    
    def get_modifiers(self, page: int = 1, page_size: int = 10, category: str = None):
        """Get all modifiers with pagination."""
        params = {'page': page, 'page_size': page_size}
        if category:
            params['category'] = category
        
        response = requests.get(
            f'{self.base_url}/api/v1/modifiers/',
            headers=self.headers,
            params=params
        )
        return response.json()

# Usage
api = ModifierAPI('http://localhost:8000', 'your_token')

# Create size modifier
modifier = api.create_modifier(
    name='Size',
    modifier_type='single',
    category='sizes',
    required=True,
    min_selections=1,
    max_selections=1
)

# Add size options
api.add_option(modifier['id'], 'Small', price=0, sort_order=1)
api.add_option(modifier['id'], 'Medium', price=200, sort_order=2)
api.add_option(modifier['id'], 'Large', price=400, sort_order=3)
```

---

## Testing Examples

### Complete Modifier Setup Test
```bash
#!/bin/bash

TOKEN="your_token_here"
BASE_URL="http://localhost:8000/api/v1"

# Create Size Modifier
echo "Creating Size modifier..."
MODIFIER_RESPONSE=$(curl -s -X POST "$BASE_URL/modifiers/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Size",
    "type": "single",
    "category": "sizes",
    "required": true,
    "min_selections": 1,
    "max_selections": 1
  }')

MODIFIER_ID=$(echo $MODIFIER_RESPONSE | jq -r '.id')
echo "Modifier ID: $MODIFIER_ID"

# Add Size Options
echo "Adding size options..."
curl -s -X POST "$BASE_URL/modifiers/$MODIFIER_ID/options" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Small", "price": 0, "sort_order": 1}' | jq

curl -s -X POST "$BASE_URL/modifiers/$MODIFIER_ID/options" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Medium", "price": 200, "sort_order": 2}' | jq

curl -s -X POST "$BASE_URL/modifiers/$MODIFIER_ID/options" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Large", "price": 400, "sort_order": 3}' | jq

# Get Complete Modifier
echo "Fetching complete modifier..."
curl -s -X GET "$BASE_URL/modifiers/$MODIFIER_ID" \
  -H "Authorization: Bearer $TOKEN" | jq

echo "Test complete!"
```

---

## FAQ

### Q: Can I update a modifier after creation?
**A:** Currently, the API doesn't have an UPDATE endpoint for modifiers. You need to delete and recreate, or manually update via database.

### Q: What happens when I delete a modifier with options?
**A:** All associated options are automatically deleted (cascade delete). Product associations are also removed.

### Q: Can options have negative prices (discounts)?
**A:** No, the price field must be ≥ 0. For discounts, handle at the order level.

### Q: How do I reorder options?
**A:** Update the `sort_order` field. Lower numbers appear first.

### Q: Can one option belong to multiple modifiers?
**A:** No, each option belongs to exactly one modifier (foreign key relationship).

### Q: What's the maximum number of options per modifier?
**A:** No hard limit, but keep it reasonable (≤20) for better UX.

### Q: Can I make an option temporarily unavailable?
**A:** Yes, set `available: false`. The option remains but won't be selectable.

### Q: How do I handle seasonal or limited-time options?
**A:** Use the `available` field to toggle options on/off without deleting them.

### Q: Can modifiers be reused across multiple products?
**A:** Yes! Create the modifier once, then associate it with multiple products using the ProductModifier relationship.

---

## Related Endpoints

### Product-Modifier Association
See Products API documentation for:
- Assigning modifiers to products
- Retrieving products with modifiers
- Order item modifier selections

### Order Item Modifiers
See Orders API documentation for:
- Including modifiers in order items
- Calculating order totals with modifiers
- Modifier selection validation

---

## Changelog

### v1.0.0 (2025-11-24)
- ✅ Initial modifiers API implementation
- ✅ CRUD operations for modifiers
- ✅ CRUD operations for modifier options
- ✅ Pagination support
- ✅ Category filtering
- ✅ Cascade delete functionality
- ✅ Sort order support

---

## Support

For issues or questions:
- Verify modifier_id exists before adding options
- Check min/max selection constraints
- Ensure prices are in cents (integer)
- Use sort_order for proper option sequencing
- Test with single and multiple selection types

**API Version:** 1.0.0  
**Last Updated:** November 24, 2025  
**Status:** ✅ Production Ready
