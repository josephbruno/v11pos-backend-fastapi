# Category API Integration Guide

## Overview
Complete API documentation for the Category Management endpoints in the Restaurant POS system with **direct image upload support**.

**Base URL:** `http://localhost:8000`  
**API Prefix:** `/api/v1/categories`  
**Authentication:** Required (JWT Bearer Token)  
**Content Type:** `multipart/form-data` (for create/update with images)

---

## 📋 Table of Contents
- [Endpoints Summary](#endpoints-summary)
- [Data Models](#data-models)
- [API Endpoints](#api-endpoints)
- [Error Handling](#error-handling)
- [Integration Examples](#integration-examples)

---

## Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/categories/` | List all categories with pagination |
| GET | `/api/v1/categories/{category_id}` | Get a specific category by ID |
| POST | `/api/v1/categories/` | Create a new category |
| PUT | `/api/v1/categories/{category_id}` | Update an existing category |
| DELETE | `/api/v1/categories/{category_id}` | Delete a category |

---

## Data Models

### Category Object

```json
{
  "id": "uuid",
  "name": "string",
  "slug": "string",
  "description": "string | null",
  "active": "boolean",
  "sort_order": "integer",
  "image": "string | null",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Auto | Unique identifier (auto-generated) |
| `name` | string | ✅ Yes | Category name (1-100 chars) |
| `slug` | string | ✅ Yes | URL-friendly identifier (1-100 chars, must be unique) |
| `description` | string | No | Category description |
| `active` | boolean | No | Whether category is active (default: `true`) |
| `sort_order` | integer | No | Display order (default: `0`) |
| `image` | string | No | **Full path to uploaded image** (e.g., `/uploads/categories/image.jpg`) or `null` if no image |
| `created_at` | datetime | Auto | Creation timestamp |
| `updated_at` | datetime | Auto | Last update timestamp |

### Image Upload Specifications

| Constraint | Value |
|------------|-------|
| **Max File Size** | 10 MB |
| **Allowed Formats** | `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp` |
| **Storage Location** | `uploads/categories/` (on server) |
| **Stored Path Format** | `/uploads/categories/filename.jpg` (matches products format) |
| **Access URL** | Direct URL - just append to base: `http://localhost:8000${image}` |
| **Behavior** | Optional - if not provided, `image` field will be `null` |

**✨ New Format (v2.0.0+):** Images are now stored with full path `/uploads/categories/filename.jpg` to match the products API format. This means:
- **Direct Usage:** `<img src="http://localhost:8000${category.image}" />` 
- **No String Manipulation:** No need to prepend `/uploads/` - the path is ready to use
- **Consistency:** Same format as products API for uniform frontend handling

---

## API Endpoints

### 1. List Categories

**Endpoint:** `GET /api/v1/categories/`

**Description:** Retrieve a paginated list of categories with optional filtering.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number (minimum: 1) |
| `page_size` | integer | No | 10 | Items per page (1-100) |
| `active` | boolean | No | - | Filter by active status |

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/categories/?page=1&page_size=10&active=true"
```

**Success Response (200 OK):**
```json
{
  "status": "success",
  "message": "Categories retrieved successfully",
  "data": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Beverages",
      "slug": "beverages",
      "description": "Hot and cold drinks",
      "active": true,
      "sort_order": 1,
      "image": "/uploads/categories/beverages.jpg",
      "created_at": "2024-11-20T10:00:00",
      "updated_at": "2024-11-20T10:00:00"
    },
    {
      "id": "223e4567-e89b-12d3-a456-426614174001",
      "name": "Main Course",
      "slug": "main-course",
      "description": "Delicious main dishes",
      "active": true,
      "sort_order": 2,
      "image": "/uploads/categories/main-course.jpg",
      "created_at": "2024-11-20T10:30:00",
      "updated_at": "2024-11-20T10:30:00"
    }
  ],
  "pagination": {
    "total": 25,
    "page": 1,
    "page_size": 10,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

**Use Cases:**
- Display category menu in frontend
- Category selection dropdown
- Admin category management list
- Filter products by active categories

---

### 2. Get Single Category

**Endpoint:** `GET /api/v1/categories/{category_id}`

**Description:** Retrieve details of a specific category by its UUID.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category_id` | UUID | ✅ Yes | Category unique identifier |

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/categories/123e4567-e89b-12d3-a456-426614174000"
```

**Success Response (200 OK):**
```json
{
  "status": "success",
  "message": "Category fetched successfully",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Beverages",
    "slug": "beverages",
    "description": "Hot and cold drinks including coffee, tea, and soft drinks",
    "active": true,
    "sort_order": 1,
    "image": "/uploads/categories/beverages.jpg",
    "created_at": "2024-11-20T10:00:00",
    "updated_at": "2024-11-20T10:00:00"
  }
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Category with id 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

**Use Cases:**
- Category detail page
- Edit category form pre-fill
- Display category information with products

---

### 3. Create Category

**Endpoint:** `POST /api/v1/categories/`

**Description:** Create a new category with optional image upload.

**Content-Type:** `multipart/form-data`

**Authentication:** Required (JWT Bearer Token)

**Form Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ Yes | Category name (1-100 chars) |
| `slug` | string | ✅ Yes | URL-friendly slug (must be unique) |
| `description` | string | No | Category description |
| `active` | boolean | No | Active status (default: `true`) |
| `sort_order` | integer | No | Display order (default: `0`) |
| `image` | file | No | Image file (JPG/PNG/GIF/WebP, max 10MB) |

**Example Request WITHOUT Image:**
```bash
curl -X POST "http://localhost:8000/api/v1/categories/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "name=Appetizers" \
  -F "slug=appetizers" \
  -F "description=Delicious starters and small plates" \
  -F "active=true" \
  -F "sort_order=3"
```

**Example Request WITH Image:**
```bash
curl -X POST "http://localhost:8000/api/v1/categories/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "name=Appetizers" \
  -F "slug=appetizers" \
  -F "description=Delicious starters and small plates" \
  -F "active=true" \
  -F "sort_order=3" \
  -F "image=@/path/to/appetizers.jpg"
```

**Success Response WITHOUT Image (201 Created):**
```json
{
  "status": "success",
  "message": "Category created successfully",
  "data": {
    "id": "323e4567-e89b-12d3-a456-426614174002",
    "name": "Appetizers",
    "slug": "appetizers",
    "description": "Delicious starters and small plates",
    "active": true,
    "sort_order": 3,
    "image": null,
    "created_at": "2024-11-24T14:30:00",
    "updated_at": "2024-11-24T14:30:00"
  }
}
```

**Success Response WITH Image (201 Created):**
```json
{
  "status": "success",
  "message": "Category created successfully",
  "data": {
    "id": "323e4567-e89b-12d3-a456-426614174002",
    "name": "Appetizers",
    "slug": "appetizers",
    "description": "Delicious starters and small plates",
    "active": true,
    "sort_order": 3,
    "image": "/uploads/categories/appetizers.jpg",
    "created_at": "2024-11-24T14:30:00",
    "updated_at": "2024-11-24T14:30:00"
  }
}
```

**Error Response (400 Bad Request - Duplicate Slug):**
```json
{
  "detail": "Category with slug 'appetizers' already exists"
}
```

**Error Response (400 Bad Request - Invalid File Type):**
```json
{
  "detail": "File type '.pdf' not allowed. Allowed types: .jpg, .jpeg, .png, .gif, .webp"
}
```

**Error Response (413 Request Entity Too Large):**
```json
{
  "detail": "File size exceeds maximum allowed size of 10.0MB"
}
```

**Error Response (401 Unauthorized):**
```json
{
  "detail": "Not authenticated"
}
```

**Error Response (422 Unprocessable Entity - Validation Error):**
```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Use Cases:**
- Admin category creation form
- Import categories from external system
- Setup initial category structure

---

### 4. Update Category

**Endpoint:** `PUT /api/v1/categories/{category_id}`

**Description:** Update an existing category with optional new image upload. Only provided fields will be updated.

**Content-Type:** `multipart/form-data`

**Authentication:** Required (JWT Bearer Token)

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category_id` | UUID | ✅ Yes | Category unique identifier |

**Form Fields (all optional):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | No | New category name |
| `slug` | string | No | New URL-friendly slug |
| `description` | string | No | New description |
| `active` | boolean | No | New active status |
| `sort_order` | integer | No | New display order |
| `image` | file | No | New image file (replaces old image) |

**Example Request - Update Name Only:**
```bash
curl -X PUT "http://localhost:8000/api/v1/categories/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "name=Hot & Cold Beverages"
```

**Example Request - Update with New Image:**
```bash
curl -X PUT "http://localhost:8000/api/v1/categories/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "name=Hot & Cold Beverages" \
  -F "description=Comprehensive drink menu including specialty coffees" \
  -F "sort_order=1" \
  -F "image=@/path/to/new-beverages.jpg"
```

**Success Response (200 OK):**
```json
{
  "status": "success",
  "message": "Category updated successfully",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Hot & Cold Beverages",
    "slug": "beverages",
    "description": "Comprehensive drink menu including specialty coffees",
    "active": true,
    "sort_order": 1,
    "image": "/uploads/categories/new-beverages.jpg",
    "created_at": "2024-11-20T10:00:00",
    "updated_at": "2024-11-24T15:00:00"
  }
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Category with id 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

**Error Response (400 Bad Request - Duplicate Slug):**
```json
{
  "detail": "Category with slug 'main-course' already exists"
}
```

**Error Response (400 Bad Request - Invalid File Type):**
```json
{
  "detail": "File type '.txt' not allowed. Allowed types: .jpg, .jpeg, .png, .gif, .webp"
}
```

**Use Cases:**
- Edit category details
- Change category status (active/inactive)
- Update category sort order
- Replace category image with new one
- Update multiple fields at once

**Important Notes:**
- ✅ **Partial updates supported**: Send only fields you want to update
- ✅ **Old image auto-deleted**: When uploading new image, old one is removed from disk
- ✅ **No image field**: Omit `image` to keep existing image unchanged
- ✅ **Slug validation**: Can be updated but must remain unique
- ✅ **Auto timestamp**: `updated_at` automatically updated on any change

---

### 5. Delete Category

**Endpoint:** `DELETE /api/v1/categories/{category_id}`

**Description:** Delete a category and its associated image file. Categories with associated products cannot be deleted.

**Authentication:** Required (JWT Bearer Token)

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category_id` | UUID | ✅ Yes | Category unique identifier |

**Example Request:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/categories/323e4567-e89b-12d3-a456-426614174002" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Success Response (200 OK):**
```json
{
  "status": "success",
  "message": "Category deleted successfully",
  "data": null
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Category with id 323e4567-e89b-12d3-a456-426614174002 not found"
}
```

**Error Response (400 Bad Request - Has Products):**
```json
{
  "detail": "Cannot delete category with existing products"
}
```

**Error Response (401 Unauthorized):**
```json
{
  "detail": "Not authenticated"
}
```

**Use Cases:**
- Remove unused categories
- Clean up test data
- Admin category management

**Important Notes:**
- ⚠️ **Cannot delete categories with products**: Must reassign or delete products first
- ✅ **Auto image cleanup**: Associated image file automatically deleted from disk
- ⚠️ **Permanent deletion**: Cannot be undone
- 💡 **Alternative**: Consider setting `active: false` instead of deleting to preserve data

---

## Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success - Request completed successfully |
| 201 | Created - Category created successfully |
| 400 | Bad Request - Invalid data or duplicate slug |
| 404 | Not Found - Category doesn't exist |
| 422 | Unprocessable Entity - Validation errors |
| 500 | Internal Server Error - Server-side error |

### Common Error Formats

**Validation Error (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

**Business Logic Error (400):**
```json
{
  "detail": "Category with slug 'beverages' already exists"
}
```

**Not Found Error (404):**
```json
{
  "detail": "Category with id 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

---

## Integration Examples

### JavaScript/TypeScript (Fetch API)

```javascript
const API_BASE = 'http://localhost:8000';
const token = 'YOUR_JWT_TOKEN'; // Get from login

// List Categories
async function listCategories(page = 1, pageSize = 10, activeOnly = true) {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString()
  });
  
  if (activeOnly) {
    params.append('active', 'true');
  }
  
  const response = await fetch(
    `${API_BASE}/api/v1/categories/?${params}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
}

// Get Single Category
async function getCategory(categoryId) {
  const response = await fetch(
    `${API_BASE}/api/v1/categories/${categoryId}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Category not found');
    }
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
}

// Create Category WITHOUT Image
async function createCategory(categoryData) {
  const formData = new FormData();
  formData.append('name', categoryData.name);
  formData.append('slug', categoryData.slug);
  if (categoryData.description) formData.append('description', categoryData.description);
  formData.append('active', categoryData.active ?? true);
  formData.append('sort_order', categoryData.sort_order ?? 0);
  
  const response = await fetch(
    `${API_BASE}/api/v1/categories/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
        // Don't set Content-Type for FormData - browser sets it with boundary
      },
      body: formData
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create category');
  }
  
  return await response.json();
}

// Create Category WITH Image
async function createCategoryWithImage(categoryData, imageFile) {
  const formData = new FormData();
  formData.append('name', categoryData.name);
  formData.append('slug', categoryData.slug);
  if (categoryData.description) formData.append('description', categoryData.description);
  formData.append('active', categoryData.active ?? true);
  formData.append('sort_order', categoryData.sort_order ?? 0);
  
  // Add image file
  if (imageFile) {
    formData.append('image', imageFile);
  }
  
  const response = await fetch(
    `${API_BASE}/api/v1/categories/`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create category');
  }
  
  return await response.json();
}

// Update Category
async function updateCategory(categoryId, updateData, newImageFile = null) {
  const formData = new FormData();
  
  // Add only fields that are provided
  if (updateData.name) formData.append('name', updateData.name);
  if (updateData.slug) formData.append('slug', updateData.slug);
  if (updateData.description !== undefined) formData.append('description', updateData.description);
  if (updateData.active !== undefined) formData.append('active', updateData.active);
  if (updateData.sort_order !== undefined) formData.append('sort_order', updateData.sort_order);
  
  // Add new image if provided
  if (newImageFile) {
    formData.append('image', newImageFile);
  }
  
  const response = await fetch(
    `${API_BASE}/api/v1/categories/${categoryId}`,
    {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update category');
  }
  
  return await response.json();
}

// Delete Category
async function deleteCategory(categoryId) {
  const response = await fetch(
    `${API_BASE}/api/v1/categories/${categoryId}`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete category');
  }
  
  return await response.json();
}

// Usage Examples
try {
  // List active categories
  const categories = await listCategories(1, 20, true);
  console.log('Categories:', categories.data);
  console.log('Total pages:', categories.pagination.total_pages);
  
  // Create new category
  const newCategory = await createCategory({
    name: 'Desserts',
    slug: 'desserts',
    description: 'Sweet treats and desserts',
    active: true,
    sort_order: 5,
    image: '/uploads/categories/desserts.jpg'
  });
  console.log('Created:', newCategory.data);
  
  // Update category
  const updated = await updateCategory(newCategory.data.id, {
    description: 'Delicious sweet treats, cakes, and desserts',
    sort_order: 4
  });
  console.log('Updated:', updated.data);
  
  // Delete category
  await deleteCategory(newCategory.data.id);
  console.log('Category deleted');
  
} catch (error) {
  console.error('Error:', error.message);
}
```

---

### Python (Requests Library)

```python
import requests
from typing import Optional, Dict, Any
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1/categories"
TOKEN = "YOUR_JWT_TOKEN"  # Get from login

def list_categories(page: int = 1, page_size: int = 10, active: Optional[bool] = None) -> Dict[str, Any]:
    """List categories with pagination"""
    params = {
        'page': page,
        'page_size': page_size
    }
    
    if active is not None:
        params['active'] = str(active).lower()
    
    response = requests.get(
        BASE_URL + "/",
        params=params,
        headers={'Authorization': f'Bearer {TOKEN}'}
    )
    response.raise_for_status()
    return response.json()

def get_category(category_id: str) -> Dict[str, Any]:
    """Get a single category by ID"""
    response = requests.get(
        f"{BASE_URL}/{category_id}",
        headers={'Authorization': f'Bearer {TOKEN}'}
    )
    response.raise_for_status()
    return response.json()

def create_category(
    name: str,
    slug: str,
    description: Optional[str] = None,
    active: bool = True,
    sort_order: int = 0,
    image_path: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new category with optional image upload"""
    data = {
        'name': name,
        'slug': slug,
        'active': str(active).lower(),
        'sort_order': str(sort_order)
    }
    
    if description:
        data['description'] = description
    
    files = None
    if image_path and Path(image_path).exists():
        files = {'image': open(image_path, 'rb')}
    
    try:
        response = requests.post(
            BASE_URL + "/",
            data=data,
            files=files,
            headers={'Authorization': f'Bearer {TOKEN}'}
        )
        response.raise_for_status()
        return response.json()
    finally:
        if files:
            files['image'].close()

def update_category(
    category_id: str,
    name: Optional[str] = None,
    slug: Optional[str] = None,
    description: Optional[str] = None,
    active: Optional[bool] = None,
    sort_order: Optional[int] = None,
    image_path: Optional[str] = None
) -> Dict[str, Any]:
    """Update an existing category with optional new image"""
    data = {}
    
    if name is not None:
        data['name'] = name
    if slug is not None:
        data['slug'] = slug
    if description is not None:
        data['description'] = description
    if active is not None:
        data['active'] = str(active).lower()
    if sort_order is not None:
        data['sort_order'] = str(sort_order)
    
    files = None
    if image_path and Path(image_path).exists():
        files = {'image': open(image_path, 'rb')}
    
    try:
        response = requests.put(
            f"{BASE_URL}/{category_id}",
            data=data,
            files=files,
            headers={'Authorization': f'Bearer {TOKEN}'}
        )
        response.raise_for_status()
        return response.json()
    finally:
        if files:
            files['image'].close()

def delete_category(category_id: str) -> Dict[str, Any]:
    """Delete a category and its associated image"""
    response = requests.delete(
        f"{BASE_URL}/{category_id}",
        headers={'Authorization': f'Bearer {TOKEN}'}
    )
    response.raise_for_status()
    return response.json()

# Usage Examples
if __name__ == "__main__":
    try:
        # List categories
        result = list_categories(page=1, page_size=20, active=True)
        print(f"Found {result['pagination']['total']} categories")
        for category in result['data']:
            image_info = f" [Image: {category['image']}]" if category['image'] else ""
            print(f"- {category['name']} (Order: {category['sort_order']}){image_info}")
        
        # Create category WITHOUT image
        new_category = create_category(
            name='Salads',
            slug='salads',
            description='Fresh and healthy salads',
            active=True,
            sort_order=3
        )
        print(f"\nCreated category: {new_category['data']['name']}")
        print(f"Image: {new_category['data']['image']}")  # null
        category_id = new_category['data']['id']
        
        # Create category WITH image
        desserts_category = create_category(
            name='Desserts',
            slug='desserts',
            description='Sweet treats',
            active=True,
            sort_order=4,
            image_path='./images/desserts.jpg'  # Local file path
        )
        print(f"\nCreated category with image: {desserts_category['data']['name']}")
        print(f"Image path: {desserts_category['data']['image']}")  # "categories/desserts.jpg"
        print(f"Full URL: http://localhost:8000/uploads/{desserts_category['data']['image']}")
        
        # Update category (name only, image unchanged)
        updated = update_category(
            category_id,
            description='Fresh garden salads and healthy bowls',
            sort_order=2
        )
        print(f"\nUpdated category: {updated['data']['name']}")
        
        # Update category WITH new image (old image auto-deleted)
        updated_with_image = update_category(
            category_id,
            name='Fresh Salads',
            image_path='./images/salads_new.jpg'
        )
        print(f"\nUpdated category with new image: {updated_with_image['data']['name']}")
        print(f"New image: {updated_with_image['data']['image']}")
        
        # Get single category
        category = get_category(category_id)
        print(f"\nCategory details:")
        print(f"  Name: {category['data']['name']}")
        print(f"  Slug: {category['data']['slug']}")
        print(f"  Active: {category['data']['active']}")
        print(f"  Image: {category['data']['image']}")
        
        # Delete category (also deletes image file)
        delete_category(category_id)
        print(f"\nDeleted category: {category_id}")
        
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"Error: {e}")
```

---

### React Component Example

```typescript
import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface Category {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  active: boolean;
  sort_order: number;
  image: string | null;
  created_at: string;
  updated_at: string;
}

interface CategoryResponse {
  status: string;
  message: string;
  data: Category[];
  pagination: {
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

const CategoryManager: React.FC = () => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const API_BASE = 'http://localhost:8000/api/v1/categories';

  // Fetch categories
  const fetchCategories = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get<CategoryResponse>(API_BASE, {
        params: {
          page,
          page_size: 10,
          active: true
        }
      });
      
      setCategories(response.data.data);
      setTotalPages(response.data.pagination.total_pages);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch categories');
    } finally {
      setLoading(false);
    }
  };

  // Create category with optional image
  const createCategory = async (
    categoryData: Partial<Category>,
    imageFile?: File
  ) => {
    try {
      const formData = new FormData();
      formData.append('name', categoryData.name || '');
      formData.append('slug', categoryData.slug || '');
      if (categoryData.description) {
        formData.append('description', categoryData.description);
      }
      formData.append('active', String(categoryData.active ?? true));
      formData.append('sort_order', String(categoryData.sort_order ?? 0));
      
      // Add image if provided
      if (imageFile) {
        formData.append('image', imageFile);
      }
      
      const response = await axios.post(API_BASE + '/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}` // Add your JWT token
        }
      });
      
      console.log('Category created:', response.data);
      fetchCategories(); // Refresh list
      return response.data;
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to create category');
    }
  };

  // Update category with optional new image
  const updateCategory = async (
    id: string,
    updateData: Partial<Category>,
    newImageFile?: File
  ) => {
    try {
      const formData = new FormData();
      
      // Add only fields that are provided
      if (updateData.name) formData.append('name', updateData.name);
      if (updateData.slug) formData.append('slug', updateData.slug);
      if (updateData.description !== undefined) {
        formData.append('description', updateData.description);
      }
      if (updateData.active !== undefined) {
        formData.append('active', String(updateData.active));
      }
      if (updateData.sort_order !== undefined) {
        formData.append('sort_order', String(updateData.sort_order));
      }
      
      // Add new image if provided
      if (newImageFile) {
        formData.append('image', newImageFile);
      }
      
      const response = await axios.put(`${API_BASE}/${id}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}` // Add your JWT token
        }
      });
      
      console.log('Category updated:', response.data);
      fetchCategories(); // Refresh list
      return response.data;
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Failed to update category');
    }
  };

  // Delete category
  const deleteCategory = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this category?')) {
      return;
    }
    
    try {
      await axios.delete(`${API_BASE}/${id}`);
      console.log('Category deleted');
      fetchCategories(); // Refresh list
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete category');
    }
  };

  // Load categories on mount and page change
  useEffect(() => {
    fetchCategories();
  }, [page]);

  // File input handler
  const handleImageUpload = async (
    categoryData: Partial<Category>,
    imageFile: File | null
  ) => {
    try {
      await createCategory(categoryData, imageFile);
      alert('Category created successfully!');
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div className="category-manager">
      <h2>Category Management</h2>
      
      {loading && <p>Loading...</p>}
      {error && <p className="error">{error}</p>}
      
      <div className="category-list">
        {categories.map((category) => (
          <div key={category.id} className="category-item">
            {/* Display category image */}
            {category.image && (
              <img 
                src={`http://localhost:8000${category.image}`}
                alt={category.name}
                style={{ width: '100px', height: '100px', objectFit: 'cover' }}
              />
            )}
            
            <h3>{category.name}</h3>
            <p>{category.description}</p>
            <span>Order: {category.sort_order}</span>
            <span>{category.active ? '✅ Active' : '❌ Inactive'}</span>
            
            <button onClick={() => updateCategory(category.id, {
              active: !category.active
            })}>
              Toggle Status
            </button>
            
            <button onClick={() => deleteCategory(category.id)}>
              Delete
            </button>
          </div>
        ))}
      </div>
      
      <div className="pagination">
        <button 
          disabled={page === 1} 
          onClick={() => setPage(page - 1)}
        >
          Previous
        </button>
        <span>Page {page} of {totalPages}</span>
        <button 
          disabled={page === totalPages} 
          onClick={() => setPage(page + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default CategoryManager;
```

---

## Testing with cURL

### Complete Test Workflow

```bash
# Set variables
TOKEN="YOUR_JWT_TOKEN"  # Get from login endpoint
API_BASE="http://localhost:8000/api/v1/categories"

# 1. List all categories
curl -X GET "${API_BASE}/?page=1&page_size=10" \
  -H "Authorization: Bearer ${TOKEN}"

# 2. List only active categories
curl -X GET "${API_BASE}/?active=true" \
  -H "Authorization: Bearer ${TOKEN}"

# 3. Create category WITHOUT image
curl -X POST "${API_BASE}/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "name=Test Category" \
  -F "slug=test-category" \
  -F "description=This is a test category" \
  -F "active=true" \
  -F "sort_order=99"

# 4. Create category WITH image
curl -X POST "${API_BASE}/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "name=Desserts" \
  -F "slug=desserts" \
  -F "description=Sweet treats and pastries" \
  -F "active=true" \
  -F "sort_order=5" \
  -F "image=@/path/to/desserts.jpg"

# Save the returned ID for next steps
CATEGORY_ID="<returned-uuid-here>"

# 5. Get the created category
curl -X GET "${API_BASE}/${CATEGORY_ID}" \
  -H "Authorization: Bearer ${TOKEN}"

# 6. Update category (name only, image unchanged)
curl -X PUT "${API_BASE}/${CATEGORY_ID}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "name=Updated Test Category" \
  -F "description=Updated description" \
  -F "sort_order=50"

# 7. Update category WITH new image (old image deleted automatically)
curl -X PUT "${API_BASE}/${CATEGORY_ID}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "name=Sweet Desserts" \
  -F "image=@/path/to/new_desserts.jpg"

# 8. Deactivate the category
curl -X PUT "${API_BASE}/${CATEGORY_ID}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "active=false"

# 9. Delete the category (deletes image file too)
curl -X DELETE "${API_BASE}/${CATEGORY_ID}" \
  -H "Authorization: Bearer ${TOKEN}"
  
# 10. Access uploaded image directly
# Images are served at: http://localhost:8000/uploads/{image_path}
# Example: http://localhost:8000/uploads/categories/desserts.jpg
```

---

## Best Practices

### 1. Slug Generation
- Always create URL-friendly slugs (lowercase, hyphens instead of spaces)
- Ensure slugs are unique across all categories
- Example: "Hot Beverages" → "hot-beverages"

### 2. Sort Order
- Use increments of 10 (10, 20, 30) to allow easy reordering
- Lower numbers appear first
- Update sort_order when reordering categories

### 3. Image Handling
- **Format:** Use multipart/form-data for create/update with images
- **Allowed Types:** JPG, JPEG, PNG, GIF, WebP only
- **Max Size:** 10MB per image
- **Storage:** Images saved to `uploads/categories/` directory
- **Path Format:** Relative path stored (e.g., `categories/desserts.jpg`)
- **Access URL:** `http://localhost:8000/uploads/{image_path}`
- **Validation:** Validate file type and size on client-side before upload
- **Auto-Cleanup:** Old images automatically deleted on update/delete
- **Duplicates:** Duplicate filenames auto-renamed (image.jpg → image_1.jpg)
- **Optional:** Image field can be null if no image provided

### 4. Active Status
- Use `active: false` instead of deleting categories
- Inactive categories can be reactivated without losing data
- Filter by `active=true` in production frontend

### 5. Error Handling
- Always check response status codes
- Handle 404 errors gracefully (category might be deleted)
- Display user-friendly error messages
- Log errors for debugging

### 6. Pagination
- Use reasonable page sizes (10-50 items)
- Implement pagination controls in frontend
- Cache category lists when appropriate
- Show total count to users

---

## Common Issues & Solutions

### Issue: "Category with slug 'X' already exists"
**Solution:** Choose a different slug or check if category already exists

### Issue: "Cannot delete category with existing products"
**Solution:** 
1. Reassign products to different category
2. Delete all products in category first
3. Or set `active: false` instead of deleting

### Issue: 422 Validation Error
**Solution:** Check all required fields are provided and meet validation rules

### Issue: Invalid UUID format
**Solution:** Ensure category_id is a valid UUID string

### Issue: "Invalid file type" (400 error)
**Solution:** 
- Only JPG, JPEG, PNG, GIF, and WebP files are allowed
- Check file extension matches actual file type
- Use proper MIME type when uploading

### Issue: "Request Entity Too Large" (413 error)
**Solution:**
- File size exceeds 10MB limit
- Compress image before uploading
- Use image optimization tools
- Consider resizing to reasonable dimensions (e.g., 1024x1024 max)

### Issue: "401 Unauthorized"
**Solution:**
- Ensure JWT token is included in Authorization header
- Token format: `Bearer YOUR_JWT_TOKEN`
- Check if token is expired - login again to get new token
- Verify token has proper permissions

### Issue: Image not displaying after upload
**Solution:**
- Check image path returned in API response
- Construct full URL: `http://localhost:8000/uploads/{image_path}`
- Verify image file exists in `uploads/categories/` directory
- Check file permissions on server
- Ensure static file serving is configured in FastAPI

### Issue: Old image not deleted after update
**Solution:**
- This should happen automatically
- Check server logs for file deletion errors
- Verify write permissions on uploads directory
- Ensure image path is correctly stored in database

---

## API Response Time Guidelines

| Endpoint | Expected Response Time |
|----------|----------------------|
| List Categories | < 200ms |
| Get Category | < 100ms |
| Create Category | < 300ms |
| Update Category | < 200ms |
| Delete Category | < 200ms |

---

## Related Endpoints

- **Products API:** `/api/v1/products/` - Products belong to categories (will also support direct image upload)
- **Authentication API:** `/api/v1/auth/login` - Get JWT token for authenticated requests
- **Static Files:** `/uploads/{path}` - Access uploaded images directly

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-11-24 | Initial API documentation with JSON-based endpoints |
| 2.0.0 | 2024-11-24 | **Breaking Change:** Updated to multipart/form-data for direct image upload support. Added authentication requirements. Changed request format from JSON to Form fields. Added automatic image cleanup on update/delete. |

---

## Support & Contact

For issues or questions:
- Check API logs: `sudo docker logs restaurant_pos_api`
- Review FastAPI docs: `http://localhost:8000/docs`
- Contact: support@bestwaveinnovation.com

---

**Last Updated:** November 24, 2024  
**API Version:** 1.0  
**Author:** Restaurant POS Development Team
