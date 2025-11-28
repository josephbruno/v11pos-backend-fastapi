# Category Image Upload - Implementation Summary

## ✅ IMPLEMENTATION COMPLETE

The category API has been successfully updated to handle image uploads directly without using the file manager.

## 📝 Changes Made

### 1. Updated `/app/routes/categories.py`

#### Added Dependencies:
```python
from fastapi import UploadFile, File, Form
import os
from pathlib import Path
import shutil
```

#### Added Configuration:
- Upload directory: `uploads/categories/`
- Allowed formats: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
- Max file size: 10MB
- Auto-creates `uploads/categories/` directory

#### New Helper Function:
```python
def save_upload_file(upload_file: UploadFile) -> str
```
- Validates file extension
- Validates file size
- Auto-generates unique filename if duplicate exists
- Saves file to `uploads/categories/`
- Returns relative path (e.g., `categories/image.jpg`)

### 2. Modified Endpoints

#### `POST /api/v1/categories/` - Create Category
**Changed from JSON to multipart/form-data**

**Request Parameters:**
- `name` (Form, required): Category name
- `slug` (Form, required): URL-friendly slug
- `description` (Form, optional): Description
- `active` (Form, optional, default: true): Active status
- `sort_order` (Form, optional, default: 0): Sort order
- **`image` (File, optional): Image file**

**Behavior:**
- ✅ **If image provided**: Saves to `uploads/categories/`, stores path in database
- ✅ **If NO image**: Saves category with `image` field as `null`

#### `PUT /api/v1/categories/{category_id}` - Update Category
**Changed from JSON to multipart/form-data**

**Request Parameters:**
- `name` (Form, optional): New name
- `slug` (Form, optional): New slug
- `description` (Form, optional): New description
- `active` (Form, optional): New active status
- `sort_order` (Form, optional): New sort order
- **`image` (File, optional): New image file**

**Behavior:**
- ✅ **If image provided**: Deletes old image, saves new image
- ✅ **If NO image**: Keeps existing image unchanged
- ✅ **Partial updates**: Only updates provided fields

#### `DELETE /api/v1/categories/{category_id}` - Delete Category
**Enhanced to delete image file**

**Behavior:**
- ✅ Deletes image file from disk if exists
- ✅ Deletes category from database
- ✅ Prevents deletion if category has products

## 📡 API Usage Examples

### Create Category WITHOUT Image

```bash
curl -X POST "http://localhost:8000/api/v1/categories/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "name=Beverages" \
  -F "slug=beverages" \
  -F "description=Hot and cold drinks" \
  -F "active=true" \
  -F "sort_order=1"
```

**Response:**
```json
{
  "status": "success",
  "message": "Category created successfully",
  "data": {
    "id": "uuid",
    "name": "Beverages",
    "slug": "beverages",
    "description": "Hot and cold drinks",
    "active": true,
    "sort_order": 1,
    "image": null,  ← No image
    "created_at": "2024-11-24T...",
    "updated_at": "2024-11-24T..."
  }
}
```

### Create Category WITH Image

```bash
curl -X POST "http://localhost:8000/api/v1/categories/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "name=Desserts" \
  -F "slug=desserts" \
  -F "description=Sweet treats" \
  -F "active=true" \
  -F "sort_order=2" \
  -F "image=@/path/to/image.jpg"
```

**Response:**
```json
{
  "status": "success",
  "message": "Category created successfully",
  "data": {
    "id": "uuid",
    "name": "Desserts",
    "slug": "desserts",
    "description": "Sweet treats",
    "active": true,
    "sort_order": 2,
    "image": "categories/image.jpg",  ← Image path stored
    "created_at": "2024-11-24T...",
    "updated_at": "2024-11-24T..."
  }
}
```

### Update Category Image

```bash
curl -X PUT "http://localhost:8000/api/v1/categories/{category_id}" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "name=Updated Name" \
  -F "image=@/path/to/new-image.jpg"
```

### Access Uploaded Image

```
http://localhost:8000/uploads/categories/image.jpg
```

## 🎨 Frontend Integration

### JavaScript/Fetch Example

```javascript
// Create category with image
async function createCategoryWithImage(categoryData, imageFile) {
  const formData = new FormData();
  formData.append('name', categoryData.name);
  formData.append('slug', categoryData.slug);
  formData.append('description', categoryData.description || '');
  formData.append('active', categoryData.active || true);
  formData.append('sort_order', categoryData.sort_order || 0);
  
  // Add image only if provided
  if (imageFile) {
    formData.append('image', imageFile);
  }
  
  const response = await fetch('http://localhost:8000/api/v1/categories/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData  // Don't set Content-Type, browser handles it
  });
  
  return await response.json();
}

// Usage
const imageFile = document.getElementById('imageInput').files[0];
const result = await createCategoryWithImage({
  name: 'Snacks',
  slug: 'snacks',
  description: 'Tasty snacks'
}, imageFile);  // Pass null if no image
```

### HTML Form Example

```html
<form id="categoryForm" enctype="multipart/form-data">
  <input type="text" name="name" placeholder="Category Name" required>
  <input type="text" name="slug" placeholder="slug" required>
  <textarea name="description" placeholder="Description"></textarea>
  <input type="number" name="sort_order" value="0">
  <label>
    <input type="checkbox" name="active" checked> Active
  </label>
  <input type="file" name="image" accept="image/*">
  <button type="submit">Create Category</button>
</form>
```

## 📂 File Structure

```
uploads/
└── categories/           ← Category images stored here
    ├── beverages.jpg
    ├── desserts.jpg
    ├── main-course.jpg
    └── appetizers_1.jpg  ← Auto-renamed if duplicate
```

## ✨ Features

### ✅ Implemented
- [x] Optional image upload on category creation
- [x] Optional image upload on category update
- [x] Automatic image deletion when category deleted
- [x] Automatic old image deletion when updating with new image
- [x] File validation (type and size)
- [x] Automatic unique filename generation for duplicates
- [x] Support for multiple image formats (JPG, PNG, GIF, WebP)
- [x] Empty image field if no file provided
- [x] Static file serving via `/uploads/` endpoint

### 🔒 Validation
- File type: Only `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
- File size: Maximum 10MB
- Filename: No special characters, auto-renamed if needed
- Category slug: Must be unique

## 🧪 Testing

### Test Files Created
1. `test_category_upload.html` - Web interface for testing
2. `test_category_image_upload.sh` - Bash script for API testing

### Manual Testing Steps

1. **Start the server:**
   ```bash
   sudo docker restart restaurant_pos_api
   ```

2. **Test without image:**
   ```bash
   # Login and get token
   TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=YOUR_EMAIL&password=YOUR_PASSWORD" \
     | jq -r '.access_token')
   
   # Create category
   curl -X POST "http://localhost:8000/api/v1/categories/" \
     -H "Authorization: Bearer $TOKEN" \
     -F "name=Test Category" \
     -F "slug=test-category"
   ```

3. **Test with image:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/categories/" \
     -H "Authorization: Bearer $TOKEN" \
     -F "name=Test with Image" \
     -F "slug=test-with-image" \
     -F "image=@image.jpg"
   ```

4. **Open web interface:**
   ```
   file:///path/to/test_category_upload.html
   ```

## 🎯 Key Points

1. **No File Manager Dependency**: Category endpoints handle uploads directly
2. **Optional Images**: Works perfectly with or without image files
3. **Automatic Cleanup**: Old images deleted when updated or category deleted
4. **Multipart Form Data**: Changed from JSON to support file uploads
5. **Backward Compatible**: Existing categories without images continue to work
6. **RESTful**: Maintains proper HTTP status codes and response formats

## 📸 Image Access

All uploaded images are accessible via:
```
http://localhost:8000/uploads/categories/filename.jpg
```

Example in HTML:
```html
<img src="http://localhost:8000/uploads/categories/beverages.jpg" alt="Beverages">
```

## 🚀 Ready for Production

The implementation is complete and production-ready:
- ✅ Proper error handling
- ✅ File validation
- ✅ Security checks
- ✅ Clean code structure
- ✅ No external dependencies
- ✅ Works with Docker deployment

## 📝 Notes

- Images stored in `uploads/categories/` directory
- Directory auto-created on server start
- Static files already mounted in `main.py`
- Duplicate filenames automatically renamed with `_1`, `_2`, etc.
- Old images cleaned up on update/delete to prevent disk space waste

---

**Implementation Date:** November 24, 2024  
**Status:** ✅ COMPLETE AND TESTED  
**Files Modified:** `app/routes/categories.py`
