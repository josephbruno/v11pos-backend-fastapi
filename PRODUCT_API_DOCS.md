# Product & Category API Integration Guide

This document details the endpoints for managing the product catalog, including Categories and Products.

## Base URL
`http://localhost:8000/api/v1/products`

## Authentication
**Required**: Bearer Token in Authorization header.
`Authorization: Bearer <access_token>`

---

# Part 1: Product Categories

## 1. Create Category
Create a new product category.

- **Endpoint:** `/products/categories`
- **Method:** `POST`
- **Content-Type:** `application/json`

### Request Body (JSON) - All Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| **Basic Info** | | | |
| `name` | string | ✅ Yes | Category name (1-100 chars) |
| `slug` | string | ✅ Yes | URL-friendly identifier |
| `restaurant_id` | string | ✅ Yes | Restaurant UUID |
| `parent_id` | string | ❌ No | ID of parent category (for subcategories) |
| `description` | string | ❌ No | detailed description |
| **Display & Styling** | | | |
| `active` | bool | ❌ No | Default: `true` |
| `sort_order` | int | ❌ No | Display order (0 = top) |
| `is_featured` | bool | ❌ No | Show in featured collection |
| `image` | string | ❌ No | Main image URL |
| `icon` | string | ❌ No | Icon URL or identifier |
| `banner_image` | string | ❌ No | Banner image URL |
| `thumbnail` | string | ❌ No | Thumbnail image URL |
| `display_type` | string | ❌ No | e.g., 'grid', 'list', 'carousel' |
| `items_per_row` | int | ❌ No | Items to show per row |
| `color` | string | ❌ No | Hex code (e.g., #FF0000) |
| `background_color` | string | ❌ No | Hex code |
| `text_color` | string | ❌ No | Hex code |
| **Visibility** | | | |
| `show_in_menu` | bool | ❌ No | Show in main menu |
| `show_in_homepage` | bool | ❌ No | Show on homepage |
| `show_in_pos` | bool | ❌ No | Show in Point of Sale |
| **Availability** | | | |
| `available_for_delivery` | bool | ❌ No | Default: `true` |
| `available_for_takeaway` | bool | ❌ No | Default: `true` |
| `available_for_dine_in` | bool | ❌ No | Default: `true` |
| `available_from_time` | string | ❌ No | HH:MM format |
| `available_to_time` | string | ❌ No | HH:MM format |
| `available_days` | dict | ❌ No | `{"monday": true, ...}` |
| **SEO & Meta** | | | |
| `seo_title` | string | ❌ No | Meta Title |
| `seo_description` | string | ❌ No | Meta Description |
| `seo_keywords` | string | ❌ No | Comma-separated keywords |


### Example Request
```json
{
  "name": "Beverages",
  "slug": "beverages",
  "restaurant_id": "<YOUR_RESTAURANT_ID>",
  "active": true,
  "sort_order": 1,
  "display_type": "grid",
  "items_per_row": 4
}
```

### Success Response
```json
{
  "success": true,
  "status_code": 201,
  "message": "Category created successfully",
  "data": {
    "id": "05bf94e4-...",
    "name": "Beverages",
    "restaurant_id": "<YOUR_RESTAURANT_ID>",
    "restaurant_name": "Pizza Palace Restaurant",
    "active": true,
    "slug": "beverages"
  }
}
```

## 2. List Categories
- **Endpoint:** `/products/categories/restaurant/{restaurant_id}?skip=0&limit=100&active_only=true`
- **Method:** `GET`

## 3. Update Category
- **Endpoint:** `/products/categories/{category_id}`
- **Method:** `PUT`
- **Body:** Same as Create (all fields optional).

## 4. Delete Category
- **Endpoint:** `/products/categories/{category_id}`
- **Method:** `DELETE`

---

# Part 2: Products

## 1. Create Product
Create a new product item.

- **Endpoint:** `/products`
- **Method:** `POST`
- **Content-Type:** `application/json`

### Request Body (JSON) - All Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| **Core Identifiers** | | | |
| `name` | string | ✅ Yes | Product Name (1-200 chars) |
| `slug` | string | ✅ Yes | URL-friendly identifier |
| `restaurant_id` | string | ✅ Yes | Restaurant UUID |
| `category_id` | string | ✅ Yes | Category UUID |
| `subcategory_id` | string | ❌ No | Subcategory UUID |
| `sku` | string | ❌ No | Stock Keeping Unit |
| `barcode` | string | ❌ No | UPC/EAN Barcode |
| **Pricing** | | | |
| `price` | int | ✅ Yes | Price in CENTS/PAISE (e.g. 1000 = 10.00) |
| `cost` | int | ❌ No | Cost price (for profit calc) |
| `compare_at_price` | int | ❌ No | Original price (shows strike-through) |
| `min_price` | int | ❌ No | Min price for variable products |
| `max_price` | int | ❌ No | Max price for variable products |
| `price_varies` | bool | ❌ No | Does price vary by option? |
| `tax_rate` | float | ❌ No | Percentage (e.g., 5.0) |
| `tax_inclusive` | bool | ❌ No | Is tax included in price? |
| **Inventory** | | | |
| `stock` | int | ❌ No | Quantity on hand (Default: 0) |
| `min_stock` | int | ❌ No | Low stock alert level (Default: 5) |
| `track_inventory` | bool | ❌ No | Enable stock tracking (Default: true) |
| `allow_backorder` | bool | ❌ No | Allow sales when out of stock |
| `stock_unit` | string | ❌ No | e.g., 'kg', 'pcs', 'ltr' |
| `reorder_point` | int | ❌ No | Auto-reorder trigger level |
| `reorder_quantity` | int | ❌ No | Qty to reorder |
| **Descriptions & Media** | | | |
| `description` | string | ❌ No | HTML allowed |
| `short_description` | string | ❌ No | For card views |
| `image` | string | ❌ No | Main image URL |
| `thumbnail` | string | ❌ No | Thumbnail URL |
| `images` | dict | ❌ No | Additional images |
| `video_url` | string | ❌ No | YouTube/Vimeo link |
| **Kitchen & Details** | | | |
| `department` | string | ❌ No | Default: 'kitchen' |
| `kitchen_station` | string | ❌ No | e.g. 'grill', 'bar' |
| `preparation_time` | int | ❌ No | Minutes (Default: 15) |
| `is_veg` | bool | ❌ No | (Via dietary tags usually) |
| `calories` | int | ❌ No | Kcal count |
| `spice_level` | string | ❌ No | 'mild', 'medium', 'hot' |
| `ingredients` | string | ❌ No | Text list of ingredients |
| **Availability & Status** | | | |
| `available` | bool | ❌ No | In stock/Sold out (Default: true) |
| `is_published` | bool | ❌ No | Visible on site (Default: true) |
| `featured` | bool | ❌ No | Show on home/featured (Default: false) |
| `available_for_delivery` | bool | ❌ No | Default: `true` |
| `available_for_takeaway` | bool | ❌ No | Default: `true` |
| `available_for_dine_in` | bool | ❌ No | Default: `true` |
| `available_from_time` | string | ❌ No | HH:MM |
| `available_to_time` | string | ❌ No | HH:MM |
| **Variants & Add-ons** | | | |
| `has_variants` | bool | ❌ No | Has size/color options |
| `variant_options` | dict | ❌ No | `{"Size": ["S", "M"]}` |
| `requires_customization`| bool | ❌ No | Force user to choose options |
| **Badging** | | | |
| `badge_text` | string | ❌ No | e.g. "New", "Hot" |
| `badge_color` | string | ❌ No | Hex code |

### Example Request
```json
{
  "name": "Spicy Chicken Burger",
  "slug": "spicy-chicken-burger",
  "price": 1599,
  "category_id": "cat_123...",
  "restaurant_id": "<YOUR_RESTAURANT_ID>",
  "description": "Double patty with jalapenos",
  "spice_level": "hot",
  "is_published": true,
  "stock": 100,
  "track_inventory": true,
  "badge_text": "Hot Seller",
  "badge_color": "#FF0000"
}
```

## 2. List Products
- **Endpoint:** `/products/restaurant/{restaurant_id}`
- **Method:** `GET`
- **Query Params:**
  - `category_id`: string
  - `available_only`: bool
  - `search`: string
  - `skip`: int
  - `limit`: int

## 3. Update Product
- **Endpoint:** `/products/{product_id}`
- **Method:** `PUT`
- **Body:** JSON object with any fields from Create.

## 4. Delete Product
- **Endpoint:** `/products/{product_id}`
- **Method:** `DELETE`

## 5. Get Product Details
- **Endpoint:** `/products/{product_id}`
- **Method:** `GET`
