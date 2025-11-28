# Combo Products API Documentation

Complete API reference for Combo Products (bundled items) and Combo Items management.

## Base URL
```
http://localhost:8000/api/v1/combos
```
Combo items (items inside combos) are under:
```
http://localhost:8000/api/v1/combo-items
```

## Authentication
All endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

---

## Overview

Combo products are pre-defined bundles of existing products sold together at a single price. Each combo contains one or more `ComboItem` entries pointing to existing products with an order/quantity and optional sort order.

Primary business rules observed in the implementation:
- Combos have their own `price` (in cents) independent from contained products.
- Combos can be filtered by `category_id`, `available`, and `featured`.
- Combos support optional validity windows via `valid_from` and `valid_until`.
- Combo items are ordered via `sort_order` and must reference an existing product.
- Duplicate product entries in the same combo are rejected.

---

## Endpoints Overview

### Combo Products
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List combo products (pagination + filters) |
| GET | `/{combo_id}` | Get a specific combo product by ID |
| POST | `/` | Create a new combo product with items |
| PUT | `/{combo_id}` | Update a combo product (partial fields allowed) |
| DELETE | `/{combo_id}` | Delete a combo product |

### Combo Items
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` (on `/api/v1/combo-items`) | List combo items for a combo (pagination) via `combo_id` query or param | 
| POST | `/` (on `/api/v1/combo-items`) | Add an item to a combo |
| DELETE | `/{item_id}` (on `/api/v1/combo-items`) | Remove an item from a combo |

Note: In this implementation `combo items` endpoints are provided under the `items_router` prefix `/api/v1/combo-items` while list is implemented accepting a `combo_id` query parameter.

---

## Data Shapes (from `app/schemas/product.py`)

ComboItemBase / ComboItemCreate fields:
- `product_id: str` (required) — UUID of an existing product
- `quantity: int` default 1
- `required: bool` default True
- `choice_group: Optional[str]` optional grouping
- `choices: Optional[List[str]]` optional
- `sort_order: int` default 0

ComboItemResponse includes above plus:
- `id: str`
- `combo_id: str`
- `created_at: datetime`

ComboProductBase / ComboProductCreate fields:
- `name: str` (1-200 chars)
- `slug: str` (1-200 chars, unique)
- `description: Optional[str]`
- `price: int` (required, >0) — stored in cents
- `category_id: str` (required) — must reference an existing category
- `image: Optional[str]` (stored path/url)
- `available: bool` default True
- `featured: bool` default False
- `tags: List[str]` default []
- `valid_from: Optional[datetime]`
- `valid_until: Optional[datetime]`
- `max_quantity_per_order: int` default 10

ComboProductCreate requires:
- `items: List[ComboItemCreate]` (min_length=1)

ComboProductResponse includes above plus:
- `id: str`
- `created_at` / `updated_at`
- `items: List[ComboItemResponse]`

---

## 1. List Combos

Retrieve combos with pagination and optional filters.

### Endpoint
```
GET /api/v1/combos/?page=1&page_size=10&category_id=<id>&available=true&featured=false
```

### Query Parameters
- `page` integer (default 1)
- `page_size` integer (default 10)
- `category_id` string (optional)
- `available` boolean (optional)
- `featured` boolean (optional)

### Behavior
- Filters by `category_id`, `available`, and `featured` if provided.
- Automatically filters combos by validity window: combos with `valid_from` in the future or `valid_until` in the past are excluded.
- Returns paginated list with metadata.

---

## 2. Get Combo by ID

### Endpoint
```
GET /api/v1/combos/{combo_id}
```

### Success Response (200)
Returns a `ComboProductResponse` with nested `items`.

### Error (404)
```json
{"detail":"Combo product not found"}
```

---

## 3. Create Combo Product

Create a combo along with its items.

### Endpoint
```
POST /api/v1/combos
Content-Type: application/json
Authorization: Bearer <token>
```

### Request Body (example)
```json
{
  "name": "Lunch Combo",
  "slug": "lunch-combo",
  "description": "Burger + Fries + Drink",
  "price": 1999,
  "category_id": "140a0e11-7a3b-4900-96dc-fb252156499a",
  "image": "/uploads/products/lunch-combo.webp",
  "available": true,
  "featured": false,
  "tags": ["meal","lunch"],
  "valid_from": "2025-11-01T00:00:00Z",
  "valid_until": "2025-12-31T23:59:59Z",
  "max_quantity_per_order": 5,
  "items": [
    {"product_id": "prod-id-1", "quantity": 1, "required": true, "sort_order": 1},
    {"product_id": "prod-id-2", "quantity": 1, "required": true, "sort_order": 2},
    {"product_id": "prod-id-3", "quantity": 1, "required": true, "sort_order": 3}
  ]
}
```

### Validation & Business Rules
- `category_id` must exist — otherwise 404 `Category not found` is returned.
- `slug` must be unique — duplicate slug returns 400 `Slug already exists`.
- `valid_from` must be earlier than `valid_until` if both provided — otherwise 400.
- `items` must include at least one item.
- Each item must reference an existing product — if not, creation of items will fail when adding them via separate endpoints (combo creation itself does not validate items individually beyond model parsing in the current implementation; ensure provided product IDs exist).

### Success Response (201)
Returns `ComboProductResponse` including persisted `id` and created `items` (if items are persisted as part of create).

---

## 4. Update Combo

### Endpoint
```
PUT /api/v1/combos/{combo_id}
```

### Behavior
- Partial updates are supported: the `ComboProductUpdate` schema allows any field to be omitted.
- If updating `slug`, uniqueness is enforced (400 on duplicate).
- If updating `category_id`, the new category must exist (404 if not).
- If updating `valid_from`/`valid_until`, the date ordering is validated.

### Success Response (200)
Returns updated `ComboProductResponse`.

---

## 5. Delete Combo

### Endpoint
```
DELETE /api/v1/combos/{combo_id}
```

### Behavior
- Deletes combo record and cascade-deletes related `ComboItem` records (if DB cascade configured).
- Returns 204 No Content on success.

---

## Combo Items

Combo items are managed under the `items_router` prefix `/api/v1/combo-items`.

### 6. List Combo Items

### Endpoint
```
GET /api/v1/combo-items?combo_id=<combo_id>&page=1&page_size=10
```

### Behavior
- Requires `combo_id` (passed as query param) — returns 404 if combo not found.
- Items are ordered by `sort_order`.
- Pagination supported.

---

### 7. Add Combo Item

### Endpoint
```
POST /api/v1/combo-items
Content-Type: application/json
Authorization: Bearer <token>
```

### Request Body (example)
```json
{
  "combo_id": "combo-id-123",
  "product_id": "prod-id-1",
  "quantity": 1,
  "required": true,
  "choice_group": null,
  "choices": null,
  "sort_order": 1
}
```

### Validation & Business Rules
- `combo_id` must reference an existing combo — otherwise 404.
- `product_id` must reference an existing product — otherwise 404.
- Duplicate product in the same combo is rejected with 400 `Product already in combo`.

### Success Response (201)
Returns `ComboItemResponse` including `id`, `combo_id`, and `created_at`.

---

### 8. Remove Combo Item

### Endpoint
```
DELETE /api/v1/combo-items/{item_id}
```

### Behavior
- Removes the item from the combo. Returns 204 No Content on success.
- 404 if item not found.

---

## Example cURL Requests

Create combo (with items):
```bash
curl -X POST "http://localhost:8000/api/v1/combos" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @combo_payload.json
```

Add combo item:
```bash
curl -X POST "http://localhost:8000/api/v1/combo-items" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"combo_id":"combo-id-123","product_id":"prod-id-1","quantity":1}'
```

List combos:
```bash
curl -X GET "http://localhost:8000/api/v1/combos?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Integration Snippets

### Python (requests)
```python
import requests

BASE = 'http://localhost:8000'
HEADERS = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}

# Create combo
with open('combo_payload.json') as f:
    payload = f.read()
resp = requests.post(f'{BASE}/api/v1/combos', headers=HEADERS, data=payload)
print(resp.status_code, resp.json())

# Add item
resp = requests.post(f'{BASE}/api/v1/combo-items', headers=HEADERS, json={
    'combo_id': 'combo-id-123', 'product_id': 'prod-id-1', 'quantity': 1
})
print(resp.status_code, resp.json())
```

### Frontend (fetch)
```javascript
async function addComboItem(token, comboId, productId) {
  const res = await fetch('/api/v1/combo-items', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ combo_id: comboId, product_id: productId, quantity: 1 })
  });
  return res.json();
}
```

---

## Validation Errors

- 400 Bad Request — slug conflict, invalid date range, duplicate combo item
- 401 Unauthorized — missing/invalid JWT
- 404 Not Found — combo, category, or product not found
- 422 Unprocessable Entity — missing required fields or type errors

---

## Testing / Quick Checks

1. Create a category and at least two products.
2. POST a combo referencing existing product IDs in `items`.
3. Verify GET `/api/v1/combos/{id}` returns items.
4. Try adding the same product again via `/api/v1/combo-items` — expect 400.
5. Test validity window by setting `valid_from`/`valid_until` and calling list endpoint.

---

## Notes & Implementation Details

- The code enforces uniqueness of `slug` at create/update.
- Date validity checks are performed when creating/updating combos.
- Combo items are ordered by `sort_order` in responses.
- When adding items via `/api/v1/combo-items`, the server ensures the combo and product exist and prevents duplicates.

---

## Changelog

v1.0.0 — 2025-11-25
- Initial Combo Products documentation based on current implementation in `app/routes/combos.py` and schemas in `app/schemas/product.py`.

---

## Support

If anything in the documentation doesn't match the API behavior, please paste the relevant route file or an example request/response and I'll adjust the docs or suggest code fixes.
