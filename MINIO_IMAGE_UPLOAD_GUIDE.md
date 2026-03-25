# MinIO Image Upload Integration Guide

This document explains how image uploads are integrated into the existing Categories, Products, and Modifiers APIs using MinIO (S3-compatible storage). The APIs still accept JSON payloads exactly as before, and now also accept multipart form uploads for images/icons.

## Overview

- MinIO stores files under the `uploads` bucket.
- Files are stored under folders:
  - `categories/`
  - `products/`
  - `modifiers/`
- Filenames are UUIDs to avoid collisions.
- Only the public URL is stored in the database.
- On update, if a new file is uploaded, the old file is deleted from MinIO (best-effort).

## MinIO Configuration

Environment variables in `.env`:

```
MINIO_ENDPOINT=minio_storage:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=uploads
MINIO_SECURE=false
MINIO_PUBLIC_ENDPOINT=localhost:9000
```

- `MINIO_PUBLIC_ENDPOINT` controls the host used in returned URLs (use `localhost:9000` for local dev).

## Storage Service Responsibilities

The storage service handles:

- Client initialization
- Bucket auto-creation
- Uploads
- Deletes
- Public URL generation
- Extraction of object name from URL for delete-on-update

File: `app/services/storage_service.py`

## API Behavior Changes (No Breaking Changes)

All existing endpoints remain unchanged for JSON. Multipart uploads are additive.

### Categories

**Create**: `POST /products/categories`
- Accepts `image` as a file (optional)
- If present, uploaded to `categories/`
- URL saved to `image` column

**Update**: `PUT /products/categories/{id}`
- If `image` provided:
  - old image deleted from MinIO
  - new image uploaded
  - URL updated
- If no image provided, `image` is unchanged

### Products

**Create**: `POST /products`
- Accepts `image` file (optional)
- Upload to `products/`
- URL saved to `image` column

**Update**: `PUT /products/{id}`
- Same behavior as categories

### Modifiers

**Create**: `POST /products/modifiers`
- Accepts `icon` file (optional)
- Upload to `modifiers/`
- URL saved to `icon_url` column

**Update**: `PUT /products/modifiers/{id}`
- Replaces icon if provided

## Frontend Integration Guide

Use `multipart/form-data` when uploading a file, otherwise continue with JSON.

### Example (FormData)

```js
const formData = new FormData()
formData.append("restaurant_id", "your-restaurant-id")
formData.append("name", "Coffee")
formData.append("slug", "coffee")
formData.append("image", file)

fetch("/products/categories", {
  method: "POST",
  body: formData
})
```

### When No File is Needed

Continue using JSON:

```json
{
  "restaurant_id": "your-restaurant-id",
  "name": "Coffee",
  "slug": "coffee",
  "description": "Hot drinks"
}
```

## Sample Requests and Responses

### Category Create

**Request (multipart/form-data)**
- `restaurant_id`
- `name`
- `slug`
- `description`
- `image`

**Response**
```json
{
  "success": true,
  "status_code": 200,
  "message": "Category created successfully",
  "data": {
    "id": "cat-uuid",
    "restaurant_id": "rest-uuid",
    "name": "Beverages",
    "slug": "beverages",
    "description": "Hot & cold drinks",
    "image": "http://localhost:9000/uploads/categories/7f6f1c...png"
  }
}
```

### Category Update

**Request (multipart/form-data)**
- Optional fields and optional `image`

**Response**
```json
{
  "success": true,
  "status_code": 200,
  "message": "Category updated successfully",
  "data": {
    "id": "cat-uuid",
    "image": "http://localhost:9000/uploads/categories/newuuid.png"
  }
}
```

### Product Create

**Response**
```json
{
  "success": true,
  "status_code": 200,
  "message": "Product created successfully",
  "data": {
    "id": "prod-uuid",
    "name": "Cappuccino",
    "image": "http://localhost:9000/uploads/products/2c13...jpg"
  }
}
```

### Product Update

**Response**
```json
{
  "success": true,
  "status_code": 200,
  "message": "Product updated successfully",
  "data": {
    "id": "prod-uuid",
    "image": "http://localhost:9000/uploads/products/newuuid.jpg"
  }
}
```

### Modifier Create

**Response**
```json
{
  "success": true,
  "status_code": 200,
  "message": "Modifier created successfully",
  "data": {
    "id": "mod-uuid",
    "name": "Milk Options",
    "icon_url": "http://localhost:9000/uploads/modifiers/abcd...png"
  }
}
```

### Modifier Update

**Response**
```json
{
  "success": true,
  "status_code": 200,
  "message": "Modifier updated successfully",
  "data": {
    "id": "mod-uuid",
    "icon_url": "http://localhost:9000/uploads/modifiers/new.png"
  }
}
```

## Error Handling

### Upload Failure

```
{
  "success": false,
  "status_code": 500,
  "message": "Failed to create product",
  "error": {
    "code": "INTERNAL_ERROR",
    "details": "Upload failed"
  }
}
```

### Invalid File

```
{
  "success": false,
  "status_code": 400,
  "message": "Failed to create category",
  "error": {
    "code": "INVALID_FILE",
    "details": "Empty file"
  }
}
```

### MinIO Connection Error

```
{
  "success": false,
  "status_code": 500,
  "message": "Failed to update modifier",
  "error": {
    "code": "INTERNAL_ERROR",
    "details": "<minio error message>"
  }
}
```

## Migration Note

The modifier model now includes `icon_url`. Apply the migration:

```
alembic upgrade head
```

---

If you want this guide extended with curl examples or Postman collection updates, tell me and I will add them.
