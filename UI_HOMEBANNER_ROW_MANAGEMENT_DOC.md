# UI Implementation Document

This document covers the new `Homebanner` and `Row Management` modules, including:

- API endpoints
- request payloads
- response structure
- UI field mapping guidance

Base API prefix:

```text
/api/v1
```

Authentication:

- All endpoints require authenticated user access.
- Send the existing auth token in the `Authorization` header.

Standard response format used by both modules:

```json
{
  "success": true,
  "status_code": 200,
  "message": "Operation successful",
  "data": {},
  "error": null,
  "timestamp": "2026-04-13T05:00:00.000000+00:00"
}
```

Error format:

```json
{
  "success": false,
  "status_code": 400,
  "message": "Failed to create row management",
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Failed to create row management",
    "details": "video_url is required for ads_video row type",
    "field": null
  },
  "timestamp": "2026-04-13T05:00:00.000000Z"
}
```

---

## 1. Homebanner Module

Module purpose:

- Manage homepage banners
- Support separate mobile and desktop image variants
- Support CTA button and redirect link
- Support active/featured flags and scheduling

### 1.1 UI Fields

Recommended form fields:

- `restaurant_id` - required
- `title` - required
- `subtitle`
- `description`
- `mobile_image` - file upload
- `desktop_image` - file upload
- `redirect_url`
- `button_text`
- `active` - toggle
- `featured` - toggle
- `sort_order` - integer
- `start_at` - datetime
- `end_at` - datetime

Validation notes:

- At least one of `mobile_image` or `desktop_image` is required.
- If both `start_at` and `end_at` are sent, `end_at` must be greater than or equal to `start_at`.

### 1.2 API Endpoints

#### Create Homebanner

```http
POST /api/v1/homebanners
```

Content type:

- `multipart/form-data` for file upload
- `application/json` also supported if image URLs are already available

Example multipart fields:

```text
restaurant_id
title
subtitle
description
mobile_image
desktop_image
redirect_url
button_text
active
featured
sort_order
start_at
end_at
```

Example success response:

```json
{
  "success": true,
  "status_code": 201,
  "message": "Home banner created successfully",
  "data": {
    "title": "Summer Offer",
    "subtitle": "Flat 20% Off",
    "description": "Weekend special promotion",
    "mobile_image": "https://storage.example.com/bucket/homebanners/mobile/file.webp",
    "desktop_image": "https://storage.example.com/bucket/homebanners/desktop/file.webp",
    "redirect_url": "https://example.com/offers",
    "button_text": "Order Now",
    "active": true,
    "featured": true,
    "sort_order": 1,
    "start_at": "2026-04-13T05:00:00+00:00",
    "end_at": "2026-04-20T05:00:00+00:00",
    "id": "banner_uuid",
    "restaurant_id": "restaurant_uuid",
    "created_at": "2026-04-13T05:00:00+00:00",
    "updated_at": "2026-04-13T05:00:00+00:00",
    "deleted_at": null
  },
  "error": null,
  "timestamp": "2026-04-13T05:00:00.000000+00:00"
}
```

#### Get Homebanner List

```http
GET /api/v1/homebanners/restaurant/{restaurant_id}?active_only=false&skip=0&limit=100
```

Query params:

- `active_only` - optional boolean
- `skip` - optional integer
- `limit` - optional integer

Example success response:

```json
{
  "success": true,
  "status_code": 200,
  "message": "Home banners retrieved successfully",
  "data": [
    {
      "title": "Summer Offer",
      "subtitle": "Flat 20% Off",
      "description": "Weekend special promotion",
      "mobile_image": "https://storage.example.com/bucket/homebanners/mobile/file.webp",
      "desktop_image": "https://storage.example.com/bucket/homebanners/desktop/file.webp",
      "redirect_url": "https://example.com/offers",
      "button_text": "Order Now",
      "active": true,
      "featured": true,
      "sort_order": 1,
      "start_at": "2026-04-13T05:00:00+00:00",
      "end_at": "2026-04-20T05:00:00+00:00",
      "id": "banner_uuid",
      "restaurant_id": "restaurant_uuid",
      "created_at": "2026-04-13T05:00:00+00:00",
      "updated_at": "2026-04-13T05:00:00+00:00",
      "deleted_at": null
    }
  ],
  "error": null,
  "timestamp": "2026-04-13T05:00:00.000000+00:00"
}
```

#### Get Homebanner By ID

```http
GET /api/v1/homebanners/{banner_id}
```

#### Update Homebanner

```http
PATCH /api/v1/homebanners/{banner_id}
```

Also supported:

- `POST /api/v1/homebanners/{banner_id}`
- `PUT /api/v1/homebanners/{banner_id}`

Update fields:

- same as create, all optional

Example success response:

```json
{
  "success": true,
  "status_code": 200,
  "message": "Home banner updated successfully",
  "data": {
    "title": "Updated Summer Offer",
    "subtitle": "Flat 25% Off",
    "description": "Updated campaign",
    "mobile_image": "https://storage.example.com/bucket/homebanners/mobile/file.webp",
    "desktop_image": "https://storage.example.com/bucket/homebanners/desktop/file.webp",
    "redirect_url": "https://example.com/offers",
    "button_text": "Shop Now",
    "active": true,
    "featured": false,
    "sort_order": 2,
    "start_at": "2026-04-13T05:00:00+00:00",
    "end_at": "2026-04-21T05:00:00+00:00",
    "id": "banner_uuid",
    "restaurant_id": "restaurant_uuid",
    "created_at": "2026-04-13T05:00:00+00:00",
    "updated_at": "2026-04-13T06:00:00+00:00",
    "deleted_at": null
  },
  "error": null,
  "timestamp": "2026-04-13T06:00:00.000000+00:00"
}
```

#### Delete Homebanner

```http
DELETE /api/v1/homebanners/{banner_id}
```

Example success response:

```json
{
  "success": true,
  "status_code": 200,
  "message": "Home banner deleted successfully",
  "data": {
    "id": "banner_uuid"
  },
  "error": null,
  "timestamp": "2026-04-13T06:00:00.000000+00:00"
}
```

### 1.3 UI Implementation Notes

- Use a dual-image upload section:
  - `Mobile Banner`
  - `Desktop Banner`
- Allow save if at least one image is present.
- Recommended table columns:
  - `Title`
  - `Preview`
  - `Featured`
  - `Active`
  - `Sort Order`
  - `Schedule`
  - `Actions`

---

## 2. Row Management Module

Module purpose:

- Manage homepage rows/sections
- Support content rows and media rows
- Support these row types:
  - `category`
  - `product`
  - `combo_product`
  - `single_banner`
  - `ads_banner`
  - `ads_video`

### 2.1 UI Fields

Common fields:

- `restaurant_id` - required on create
- `name` - required
- `title`
- `subtitle`
- `description`
- `row_type` - required
- `active`
- `show_title`
- `sort_order`
- `layout_style`
- `items_per_view`
- `auto_scroll`
- `redirect_url`
- `button_text`
- `background_color`
- `text_color`
- `start_at`
- `end_at`
- `metadata` - object/json

Content reference fields:

- `category_ids` - for category rows
- `product_ids` - for product rows
- `combo_product_ids` - for combo product rows

Media fields:

- `image`
- `mobile_image`
- `desktop_image`
- `thumbnail_image`
- `video_url`
- `video_file` - multipart upload field

### 2.2 Row Type Based Required Fields

#### Category Row

```json
{
  "row_type": "category",
  "category_ids": ["category_id_1", "category_id_2"]
}
```

Required:

- `category_ids`

#### Product Row

```json
{
  "row_type": "product",
  "product_ids": ["product_id_1", "product_id_2"]
}
```

Required:

- `product_ids`

#### Combo Product Row

```json
{
  "row_type": "combo_product",
  "combo_product_ids": ["combo_id_1", "combo_id_2"]
}
```

Required:

- `combo_product_ids`

#### Single Banner Row

```json
{
  "row_type": "single_banner",
  "image": "banner_url"
}
```

Required:

- at least one of `image`, `mobile_image`, `desktop_image`

#### Ads Banner Row

```json
{
  "row_type": "ads_banner",
  "image": "banner_url"
}
```

Required:

- at least one of `image`, `mobile_image`, `desktop_image`

#### Ads Video Row

```json
{
  "row_type": "ads_video",
  "video_url": "video_url"
}
```

Required:

- `video_url` or `video_file` upload

### 2.3 API Endpoints

#### Create Row Management

```http
POST /api/v1/row-management
```

Content type:

- `multipart/form-data` for images/video upload
- `application/json` for already hosted media URLs

Example create request for category row:

```json
{
  "restaurant_id": "restaurant_uuid",
  "name": "Featured Categories",
  "title": "Shop by Category",
  "subtitle": "Top picks for you",
  "description": "Homepage category slider",
  "row_type": "category",
  "category_ids": ["cat_1", "cat_2", "cat_3"],
  "active": true,
  "show_title": true,
  "sort_order": 1,
  "layout_style": "carousel",
  "items_per_view": 6,
  "auto_scroll": false,
  "redirect_url": null,
  "button_text": null,
  "background_color": "#FFFFFF",
  "text_color": "#111111",
  "metadata": {
    "section_key": "featured_categories"
  }
}
```

Example create request for ads banner row:

```text
restaurant_id=restaurant_uuid
name=Top Banner Ads
title=Special Campaign
row_type=ads_banner
image=<file>
mobile_image=<file>
desktop_image=<file>
sort_order=2
active=true
```

Example create request for ads video row:

```text
restaurant_id=restaurant_uuid
name=Video Campaign
title=Watch and Order
row_type=ads_video
video_file=<file>
thumbnail_image=<file>
sort_order=3
active=true
```

Example success response:

```json
{
  "success": true,
  "status_code": 201,
  "message": "Row management created successfully",
  "data": {
    "name": "Featured Categories",
    "title": "Shop by Category",
    "subtitle": "Top picks for you",
    "description": "Homepage category slider",
    "row_type": "category",
    "active": true,
    "show_title": true,
    "sort_order": 1,
    "layout_style": "carousel",
    "items_per_view": 6,
    "auto_scroll": false,
    "category_ids": ["cat_1", "cat_2", "cat_3"],
    "product_ids": null,
    "combo_product_ids": null,
    "image": null,
    "mobile_image": null,
    "desktop_image": null,
    "video_url": null,
    "thumbnail_image": null,
    "redirect_url": null,
    "button_text": null,
    "background_color": "#FFFFFF",
    "text_color": "#111111",
    "start_at": null,
    "end_at": null,
    "metadata": {
      "section_key": "featured_categories"
    },
    "id": "row_uuid",
    "restaurant_id": "restaurant_uuid",
    "created_at": "2026-04-13T05:00:00+00:00",
    "updated_at": "2026-04-13T05:00:00+00:00",
    "deleted_at": null
  },
  "error": null,
  "timestamp": "2026-04-13T05:00:00.000000+00:00"
}
```

#### Get Row Management List

```http
GET /api/v1/row-management/restaurant/{restaurant_id}?row_type=category&active_only=false&skip=0&limit=100
```

Query params:

- `row_type` - optional
- `active_only` - optional boolean
- `skip` - optional integer
- `limit` - optional integer

Example success response:

```json
{
  "success": true,
  "status_code": 200,
  "message": "Row management retrieved successfully",
  "data": [
    {
      "name": "Featured Categories",
      "title": "Shop by Category",
      "subtitle": "Top picks for you",
      "description": "Homepage category slider",
      "row_type": "category",
      "active": true,
      "show_title": true,
      "sort_order": 1,
      "layout_style": "carousel",
      "items_per_view": 6,
      "auto_scroll": false,
      "category_ids": ["cat_1", "cat_2", "cat_3"],
      "product_ids": null,
      "combo_product_ids": null,
      "image": null,
      "mobile_image": null,
      "desktop_image": null,
      "video_url": null,
      "thumbnail_image": null,
      "redirect_url": null,
      "button_text": null,
      "background_color": "#FFFFFF",
      "text_color": "#111111",
      "start_at": null,
      "end_at": null,
      "metadata": {
        "section_key": "featured_categories"
      },
      "id": "row_uuid",
      "restaurant_id": "restaurant_uuid",
      "created_at": "2026-04-13T05:00:00+00:00",
      "updated_at": "2026-04-13T05:00:00+00:00",
      "deleted_at": null
    }
  ],
  "error": null,
  "timestamp": "2026-04-13T05:00:00.000000+00:00"
}
```

#### Get Row Management By ID

```http
GET /api/v1/row-management/{row_id}
```

#### Update Row Management

```http
PATCH /api/v1/row-management/{row_id}
```

Also supported:

- `POST /api/v1/row-management/{row_id}`
- `PUT /api/v1/row-management/{row_id}`

Update behavior:

- All fields are optional
- File uploads replace old media if new file is uploaded
- Validation still applies to the final row type state

Example success response:

```json
{
  "success": true,
  "status_code": 200,
  "message": "Row management updated successfully",
  "data": {
    "name": "Featured Products",
    "title": "Best Sellers",
    "subtitle": "Most loved items",
    "description": "Updated product row",
    "row_type": "product",
    "active": true,
    "show_title": true,
    "sort_order": 4,
    "layout_style": "grid",
    "items_per_view": 4,
    "auto_scroll": false,
    "category_ids": null,
    "product_ids": ["prod_1", "prod_2"],
    "combo_product_ids": null,
    "image": null,
    "mobile_image": null,
    "desktop_image": null,
    "video_url": null,
    "thumbnail_image": null,
    "redirect_url": "/products",
    "button_text": "View All",
    "background_color": "#F7F7F7",
    "text_color": "#111111",
    "start_at": null,
    "end_at": null,
    "metadata": {
      "section_key": "best_sellers"
    },
    "id": "row_uuid",
    "restaurant_id": "restaurant_uuid",
    "created_at": "2026-04-13T05:00:00+00:00",
    "updated_at": "2026-04-13T06:00:00+00:00",
    "deleted_at": null
  },
  "error": null,
  "timestamp": "2026-04-13T06:00:00.000000+00:00"
}
```

#### Delete Row Management

```http
DELETE /api/v1/row-management/{row_id}
```

Example success response:

```json
{
  "success": true,
  "status_code": 200,
  "message": "Row management deleted successfully",
  "data": {
    "id": "row_uuid"
  },
  "error": null,
  "timestamp": "2026-04-13T06:00:00.000000+00:00"
}
```

### 2.4 UI Screen Recommendation

Recommended list columns:

- `Name`
- `Type`
- `Title`
- `Active`
- `Sort Order`
- `Layout`
- `Schedule`
- `Actions`

Recommended form behavior:

- First choose `row_type`
- Show dynamic fields based on the selected type
- Fetch category/product/combo options from existing catalog APIs
- For banner/video rows, show upload inputs and media preview

Dynamic UI by type:

- `category`
  - multi-select category list
- `product`
  - multi-select product list
- `combo_product`
  - multi-select combo list
- `single_banner`
  - image/mobile image/desktop image upload
- `ads_banner`
  - image/mobile image/desktop image upload
- `ads_video`
  - video upload or hosted video URL
  - thumbnail upload

---

## 3. Frontend Integration Flow

### Homebanner Screen

1. Call `GET /api/v1/homebanners/restaurant/{restaurant_id}` for listing
2. Use `POST /api/v1/homebanners` for create
3. Use `PATCH /api/v1/homebanners/{banner_id}` for edit
4. Use `DELETE /api/v1/homebanners/{banner_id}` for delete

### Row Management Screen

1. Call `GET /api/v1/row-management/restaurant/{restaurant_id}` for listing
2. Filter by `row_type` when needed
3. Use `POST /api/v1/row-management` for create
4. Use `PATCH /api/v1/row-management/{row_id}` for edit
5. Use `DELETE /api/v1/row-management/{row_id}` for delete

---

## 4. Important Notes

- `Homebanner` images are stored as uploaded files and returned as public URLs.
- `Row Management` supports both content-based rows and media-based rows.
- `metadata` in the API response is returned inside the row object as a custom configuration object.
- Datetime fields in responses are returned using the authenticated user timezone conversion already used by the project.
- Delete operations are soft-delete style in backend behavior for these new records.

---

## 5. Source Files

- [Homebanner Route](/home/brunodoss/development/docs/pos/v11pos-backend-fastapi/app/modules/homebanner/route.py)
- [Homebanner Schema](/home/brunodoss/development/docs/pos/v11pos-backend-fastapi/app/modules/homebanner/schema.py)
- [Row Management Route](/home/brunodoss/development/docs/pos/v11pos-backend-fastapi/app/modules/row_management/route.py)
- [Row Management Schema](/home/brunodoss/development/docs/pos/v11pos-backend-fastapi/app/modules/row_management/schema.py)
