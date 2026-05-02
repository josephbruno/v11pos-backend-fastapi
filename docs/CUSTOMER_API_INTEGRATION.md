# Customer API — integration guide

This document describes the **customer-facing** HTTP API: email OTP login, JWT usage, profile and saved addresses, viewing orders, and the **shopping cart** (same `/carts` routes accept the customer access token or a staff token). Staff-only customer management under `/api/v1/customers` is out of scope here.

**API prefix:** `/api/v1`  
**Customer module prefix:** `/api/v1/customer-auth`  
**Cart prefix:** `/api/v1/carts`

Interactive schemas: run the app and open **`/docs`** (Swagger UI) or **`/redoc`**.

---

## 1. Conventions

### 1.1 Base URL

Use your deployment host, for example:

`https://<host>/api/v1/customer-auth/...`

### 1.2 Response envelope (success)

Most routes return a JSON envelope:

| Field | Type | Description |
|--------|------|-------------|
| `success` | boolean | `true` |
| `status_code` | number | Mirrors HTTP status (often `200`) |
| `message` | string | Human-readable summary |
| `data` | object \| array \| null | Payload |
| `error` | null | — |
| `timestamp` | string | ISO-8601 timestamp |

### 1.3 Response envelope (application errors)

Routes that use `error_response` return:

| Field | Type | Description |
|--------|------|-------------|
| `success` | boolean | `false` |
| `status_code` | number | HTTP status |
| `message` | string | User-facing message |
| `data` | any | Usually `null` |
| `error` | object | `code`, `message`, `details`, `field` |
| `timestamp` | string | ISO-8601 |

### 1.4 Validation errors (422)

FastAPI/Pydantic validation failures use the standard **`{"detail": [...]}`** shape (not always the envelope above).

### 1.5 HTTPException (401 / 404 on some routes)

Some authenticated routes raise **`HTTPException`**: body is typically **`{"detail": "<message>"}`** (e.g. wrong token role, address not found, order not found). Treat any non-2xx response as failure and parse `detail` when present.

### 1.6 Content type

Requests with a body: **`Content-Type: application/json`**.

### 1.7 Money and order totals

Order monetary fields (`subtotal`, `tax_amount`, `total_amount`, line `unit_price`, `total_price`, etc.) are stored as **integers in the smallest currency unit** (e.g. paise / cents). Display requires dividing by 100 (or your configured factor).

---

## 2. Authentication flow

### 2.1 Overview

1. **Request OTP** — `POST .../send-otp` (or alias `.../email/request-otp`) with `email` + `restaurant_id`.
2. **Verify OTP** — `POST .../verify-otp` (or alias `.../email/verify-otp`) with `email`, `restaurant_id`, `otp`.
3. Store **`access_token`** and **`refresh_token`** from the verify response.
4. Call protected routes with **`Authorization: Bearer <access_token>`**.
5. When the access token expires, call **`POST .../refresh`** with the refresh token to obtain a new **`access_token`**.

**Prerequisites**

- The customer must exist for that restaurant, or the server **creates a minimal customer** on first OTP request for that `email` + `restaurant_id`.
- `restaurant_id` is a **36-character** UUID string.

### 2.2 JWT contents (access token)

Payload includes at least:

- `sub` — customer id  
- `role` — `"customer"`  
- `type` — `"access"`  
- `restaurant_id` — optional; present when the customer has a restaurant

Protected routes validate **`role == "customer"`** and **`type == "access"`**, load the customer by `sub`, and reject if inactive or if token `restaurant_id` does not match the customer’s `restaurant_id` when both are set.

### 2.3 Refresh token

Payload is a **refresh** token (`type == "refresh"`). Successful refresh returns a new **`access_token`** (and `token_type: "bearer"`). It does **not** return a new refresh token in the current implementation—keep the same refresh token until you add rotation.

---

## 3. Endpoints

### 3.1 Request OTP

**`POST /api/v1/customer-auth/send-otp`**  
Alias: **`POST /api/v1/customer-auth/email/request-otp`**

**Body**

```json
{
  "email": "user@example.com",
  "restaurant_id": "<36-char-uuid>"
}
```

**Success `data` (typical)**

| Field | Type | Description |
|--------|------|-------------|
| `otp_sent` | boolean | Code stored server-side |
| `email_sent` | boolean | SMTP accepted (false if email disabled / no SMTP) |
| `expires_in_seconds` | number | OTP validity window |
| `customer_id` | string | Customer id |
| `development_otp` | string \| null | Plain OTP in dev only; omit in production clients |

**Error codes (examples)**  
`INVALID_RESTAURANT` (404), `OTP_RATE_LIMITED` (429), `INTERNAL_ERROR` (500).

---

### 3.2 Verify OTP

**`POST /api/v1/customer-auth/verify-otp`**  
Alias: **`POST /api/v1/customer-auth/email/verify-otp`**

**Body**

```json
{
  "email": "user@example.com",
  "restaurant_id": "<36-char-uuid>",
  "otp": "123456"
}
```

**Success `data`**

| Field | Type |
|--------|------|
| `customer` | object — full profile (see §4) |
| `access_token` | string |
| `refresh_token` | string |
| `token_type` | string — `"bearer"` |

**Error codes (examples)**  
`OTP_NOT_FOUND` (400), `OTP_INVALID` (400), `OTP_LOCKED` (429), `CUSTOMER_NOT_FOUND` (401), `RESTAURANT_MISMATCH` (401), `INTERNAL_ERROR` (500).

---

### 3.3 Refresh access token

**`POST /api/v1/customer-auth/refresh`**

**Body**

```json
{
  "refresh_token": "<jwt>"
}
```

**Success `data`**

| Field | Type |
|--------|------|
| `access_token` | string |
| `token_type` | string |

**Error codes (examples)**  
`INVALID_REFRESH_TOKEN`, `INVALID_TOKEN_TYPE`, `INVALID_TOKEN_ROLE`, `INVALID_TOKEN_PAYLOAD`, `CUSTOMER_NOT_FOUND` (all typically 401).

---

### 3.4 Get current profile

**`GET /api/v1/customer-auth/me`**  
**Header:** `Authorization: Bearer <access_token>`

**Success `data`:** `CustomerResponse` (§4).

---

### 3.5 Update profile (details + legacy address on customer row)

**`PATCH /api/v1/customer-auth/me`**  
**Header:** `Authorization: Bearer <access_token>`

**Body** — all fields optional; send only what changes:

| Field | Type | Max / rules |
|--------|------|-------------|
| `name` | string | 1–255 chars |
| `phone` | string | 50 |
| `address` | string | 500 |
| `city` | string | 100 |
| `state` | string | 100 |
| `postal_code` | string | 20 |
| `country` | string | 100 |
| `latitude` | number | -90 … 90 |
| `longitude` | number | -180 … 180 |
| `notes` | string | 1000 |

**Email is not accepted here** (login identity stays tied to the verified email).

**Success `data`:** updated `CustomerResponse`.

**Errors:** `DUPLICATE_EMAIL` (409) if server-side rules reject an email change path (self-update does not send email; rare). `404` if customer missing (`{"detail":"..."}`).

---

### 3.6 Saved addresses (CRUD)

All require **`Authorization: Bearer <access_token>`**.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/customer-auth/me/addresses` | List addresses |
| `POST` | `/api/v1/customer-auth/me/addresses` | Add address |
| `PUT` | `/api/v1/customer-auth/me/addresses/{address_id}` | Update address |
| `DELETE` | `/api/v1/customer-auth/me/addresses/{address_id}` | Delete address |

**Query (`GET` only)**

| Parameter | Type | Default |
|-----------|------|---------|
| `include_inactive` | boolean | `false` |

**`POST` body (`CustomerAddressCreate`)** — optional label/address/geo fields +:

| Field | Type | Default |
|--------|------|---------|
| `is_default` | boolean | `false` |
| `is_active` | boolean | `true` |

**`PUT` body (`CustomerAddressUpdate`)** — all optional: label, address, city, state, postal_code, country, latitude, longitude, `is_default`, `is_active`.

**Success:** envelope with `data` = one address object or a list (for `GET`).

**Not found:** `404` with `{"detail":"Address not found"}`.

---

### 3.7 List my orders

**`GET /api/v1/customer-auth/me/orders`**  
**Header:** `Authorization: Bearer <access_token>`

**Query**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | int | 0 | Offset |
| `limit` | int | 50 | Page size (1–100) |
| `order_status` | enum | omitted | Filter by status |

**Order status values** (string enum, same as backend):  
`pending`, `confirmed`, `preparing`, `ready`, `in_transit`, `completed`, `cancelled`, `refunded`, `on_hold`

**Success `data`**

```json
{
  "orders": [ /* OrderResponse + items */ ],
  "total": 0,
  "skip": 0,
  "limit": 50
}
```

**Visibility rules**

- Only orders with **`customer_id`** equal to the logged-in customer **and** **`restaurant_id`** equal to the customer’s restaurant are returned.
- If the customer has **no `restaurant_id`**, the list is **empty**.
- POS orders must be created with **`customer_id` set** for the customer to see them here.

---

### 3.8 Get one order

**`GET /api/v1/customer-auth/me/orders/{order_id}`**  
**Header:** `Authorization: Bearer <access_token>`

**Success `data`:** single `OrderResponse` including **`items`**.

**404:** order does not exist or does not belong to this customer/restaurant (`{"detail":"Order not found"}`).

---

### 3.9 Shopping cart (customer **or** staff JWT)

All **`/api/v1/carts`** routes accept:

- **`Authorization: Bearer <customer_access_token>`** — customer may only touch carts where **`customer_id`** is their own id and **`restaurant_id`** matches their account’s restaurant.
- **`Authorization: Bearer <staff_access_token>`** — same URLs as before; no extra path checks (staff POS behavior).

**Customer requirements**

- The customer record must have a **`restaurant_id`**. If it is missing, cart calls return **`403`** with *"Customer must belong to a restaurant to use the cart"*.
- Path/body **`customer_id`** must equal the logged-in customer’s **`id`**; otherwise **`403`** (*"Cannot access another customer's cart"*).
- Path/body **`restaurant_id`** must equal the customer’s **`restaurant_id`**; otherwise **`403`** (*"Restaurant does not match your account"*).

Use **`id`** and **`restaurant_id`** from **`GET /customer-auth/me`** (or the verify-otp payload) when calling cart APIs.

#### `GET /api/v1/carts/restaurant/{restaurant_id}/customer/{customer_id}`

Returns the active cart (creates one if needed).  
**Auth:** Bearer (customer or staff).

#### `POST /api/v1/carts/items`

**Auth:** Bearer (customer or staff).

**Body (`CartItemAddRequest`)**

| Field | Type | Notes |
|--------|------|--------|
| `restaurant_id` | string | Must match customer’s restaurant (customer token) |
| `customer_id` | string | Must be the caller’s customer id (customer token) |
| `item_type` | string | `product` or `combo_product` (see `/docs` enum) |
| `product_id` | string \| null | Required if `item_type` is `product` |
| `combo_product_id` | string \| null | Required if `item_type` is `combo_product` |
| `quantity` | int | ≥ 1 |
| `modifier_option_ids` | string[] | Optional; validated per restaurant |
| `notes` | string \| null | Optional |

**Success:** envelope with full cart in **`data`** (items, subtotal, etc.). Monetary fields are smallest currency units.

#### `PATCH /api/v1/carts/items/{item_id}`

**Body:** `{ "quantity": <int ≥ 1> }`  
**Auth:** Bearer. For customers, the line item must belong to **their** cart; otherwise **`403`**.

#### `DELETE /api/v1/carts/items/{item_id}`

**Query:** `quantity` (optional int ≥ 1) — if set, decrements by that amount; otherwise removes the line.  
**Auth:** Bearer; same ownership rules as PATCH.

#### `DELETE /api/v1/carts/restaurant/{restaurant_id}/customer/{customer_id}`

Clears the active cart for that customer.  
**Auth:** Bearer; customer token must match `restaurant_id` / `customer_id` as above.

**Errors**

- Validation / bad product: envelope with `error_code` such as **`VALIDATION_ERROR`** (HTTP **400**).
- **`401`:** missing/invalid token (`{"detail": "..."}` from auth dependency).
- **`403`:** customer scope violation (messages above).
- **`404`:** cart item not found (PATCH/DELETE) or cart not found (clear), via envelope where applicable.

---

## 4. Data shapes (reference)

### 4.1 `CustomerResponse` (`data.customer` or `GET/PATCH /me`)

| Field | Type | Notes |
|--------|------|--------|
| `id` | string | UUID |
| `restaurant_id` | string \| null | |
| `name` | string | |
| `email` | string \| null | |
| `phone` | string \| null | |
| `address`, `city`, `state`, `postal_code`, `country` | string \| null | Legacy line on customer |
| `latitude`, `longitude` | number \| null | |
| `notes` | string \| null | |
| `is_active` | boolean | |
| `created_at`, `updated_at` | string (ISO) | |
| `addresses` | array | `CustomerAddressResponse` |

### 4.2 `CustomerAddressResponse`

| Field | Type |
|--------|------|
| `id`, `customer_id` | string |
| `label`, `address`, `city`, `state`, `postal_code`, `country` | string \| null |
| `latitude`, `longitude` | number \| null |
| `is_default`, `is_active` | boolean |
| `created_at`, `updated_at` | string (ISO) |

### 4.3 Order summary (`OrderResponse`)

Includes identifiers (`id`, `order_number`, `restaurant_id`), `order_type`, `status`, payment fields, totals, timestamps, delivery/guest fields as applicable, and **`items`**: array of line items (`product_name`, `quantity`, `unit_price`, `total_price`, modifiers, etc.). See **`/docs`** for the full model.

---

## 5. Client integration checklist

1. **Persist** `restaurant_id` in the app config or deep link before login.
2. **OTP UX:** show `expires_in_seconds`; handle `OTP_RATE_LIMITED` with a countdown (`OTP_RESEND_MIN_SECONDS` is 60 on the server).
3. **Store tokens** securely (mobile: Keychain / EncryptedSharedPreferences; web: httpOnly cookie if you add a BFF, else memory + refresh flow).
4. **401 on protected routes:** try `POST /refresh`; if that fails, restart OTP flow.
5. **Orders:** ensure checkout/POS sets **`customer_id`** (and restaurant) on the order, or the customer portal will show no history.
6. **Cart:** after login, use **`me.restaurant_id`** and **`me.id`** as **`restaurant_id`** / **`customer_id`** on all cart requests; do not let the client override them with another user’s ids.
7. **CORS:** configure the server for your web origin if calling from a browser.

---

## 6. Related APIs (staff token only)

- **Staff customer CRUD:** `/api/v1/customers/...` — requires **staff** user JWT (not customer token).
- **Staff orders:** `/api/v1/orders/...` — requires staff user JWT.

---

## 7. Quick reference table

| Action | Method | Path | Auth |
|--------|--------|------|------|
| Send OTP | POST | `/customer-auth/send-otp` | No |
| Verify OTP | POST | `/customer-auth/verify-otp` | No |
| Refresh | POST | `/customer-auth/refresh` | No (body has refresh JWT) |
| Profile | GET | `/customer-auth/me` | Bearer access |
| Update profile | PATCH | `/customer-auth/me` | Bearer access |
| List addresses | GET | `/customer-auth/me/addresses` | Bearer access |
| Add address | POST | `/customer-auth/me/addresses` | Bearer access |
| Update address | PUT | `/customer-auth/me/addresses/{id}` | Bearer access |
| Delete address | DELETE | `/customer-auth/me/addresses/{id}` | Bearer access |
| List orders | GET | `/customer-auth/me/orders` | Bearer access |
| Get order | GET | `/customer-auth/me/orders/{order_id}` | Bearer access |
| Get cart | GET | `/carts/restaurant/{restaurant_id}/customer/{customer_id}` | Bearer (customer or staff) |
| Add cart line | POST | `/carts/items` | Bearer (customer or staff) |
| Update cart line qty | PATCH | `/carts/items/{item_id}` | Bearer (customer or staff) |
| Remove cart line | DELETE | `/carts/items/{item_id}` | Bearer (customer or staff) |
| Clear cart | DELETE | `/carts/restaurant/{restaurant_id}/customer/{customer_id}` | Bearer (customer or staff) |

Paths in the **Path** column are under **`/api/v1`** (e.g. `/api/v1/carts/items`).
