# Image Upload Integration Guide

## Overview
Complete guide for handling image uploads in the Restaurant POS system, specifically for category and product images.

**Upload Endpoint:** `POST /api/v1/filemanager/upload`  
**View Endpoint:** `GET /api/v1/filemanager/view/{file_path}`  
**Storage Location:** `uploads/` directory

---

## 📋 Table of Contents
- [Quick Start](#quick-start)
- [Upload API](#upload-api)
- [View/Download Images](#viewdownload-images)
- [Integration with Categories](#integration-with-categories)
- [Frontend Examples](#frontend-examples)
- [Best Practices](#best-practices)

---

## Quick Start

### 1. Upload Image
```bash
curl -X POST "http://localhost:8000/api/v1/filemanager/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/image.jpg" \
  -F "folder=categories"
```

### 2. Use Image Path in Category
```bash
curl -X POST "http://localhost:8000/api/v1/categories/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Beverages",
    "slug": "beverages",
    "image": "categories/image.jpg"
  }'
```

### 3. Access Image
```
http://localhost:8000/api/v1/filemanager/view/categories/image.jpg
```

---

## Upload API

### Endpoint Details

**Method:** `POST`  
**URL:** `/api/v1/filemanager/upload`  
**Authentication:** Required (JWT Bearer Token)  
**Content-Type:** `multipart/form-data`

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | ✅ Yes | Image file to upload |
| `folder` | string | No | Subfolder within uploads/ (e.g., "categories", "products") |

### File Constraints

| Constraint | Value |
|------------|-------|
| **Max File Size** | 10 MB |
| **Allowed Formats** | `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp` |
| **Filename** | No special characters: `< > : " / \ | ? *` |
| **Hidden Files** | Not allowed (files starting with `.`) |

### Success Response (201 Created)

```json
{
  "success": true,
  "message": "File uploaded successfully",
  "file_name": "beverages.jpg",
  "file_path": "categories/beverages.jpg",
  "file_size": 245678,
  "mime_type": "image/jpeg",
  "url": "/api/v1/filemanager/view/categories/beverages.jpg"
}
```

### Error Responses

**File Type Not Allowed (400):**
```json
{
  "detail": "File type '.pdf' not allowed. Allowed types: .jpg, .jpeg, .png, .gif, .webp"
}
```

**File Too Large (413):**
```json
{
  "detail": "File size exceeds maximum allowed size of 10.0MB"
}
```

**Invalid Filename (400):**
```json
{
  "detail": "Invalid filename characters"
}
```

**Unauthorized (401):**
```json
{
  "detail": "Not authenticated"
}
```

---

## View/Download Images

### Get Image File

**Endpoint:** `GET /api/v1/filemanager/view/{file_path}`  
**Authentication:** Required  
**Returns:** Image file with proper MIME type

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/filemanager/view/categories/beverages.jpg" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --output beverages.jpg
```

### Get Image Metadata

**Endpoint:** `GET /api/v1/filemanager/view-metadata/{file_path}`  
**Authentication:** Required  
**Returns:** File information without downloading

**Response:**
```json
{
  "file_name": "beverages.jpg",
  "file_path": "categories/beverages.jpg",
  "file_size": 245678,
  "mime_type": "image/jpeg",
  "created_at": "2024-11-24T10:00:00",
  "modified_at": "2024-11-24T10:00:00",
  "is_image": true
}
```

---

## Integration with Categories

### Complete Workflow

#### Step 1: Upload Image

```javascript
// Upload category image
const uploadImage = async (imageFile) => {
  const formData = new FormData();
  formData.append('file', imageFile);
  formData.append('folder', 'categories');
  
  const response = await fetch('http://localhost:8000/api/v1/filemanager/upload', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });
  
  const result = await response.json();
  return result.file_path; // "categories/beverages.jpg"
};
```

#### Step 2: Create Category with Image

```javascript
// Create category using the uploaded image
const createCategory = async (name, slug, imagePath) => {
  const response = await fetch('http://localhost:8000/api/v1/categories/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name: name,
      slug: slug,
      image: imagePath, // "categories/beverages.jpg"
      active: true,
      sort_order: 1
    })
  });
  
  return await response.json();
};
```

#### Step 3: Display Image

```javascript
// Display the category image
const displayImage = (imagePath, token) => {
  return `http://localhost:8000/api/v1/filemanager/view/${imagePath}`;
};

// Usage in HTML
<img 
  src={`http://localhost:8000/api/v1/filemanager/view/categories/beverages.jpg`}
  alt="Beverages"
  onError={(e) => e.target.src = '/placeholder.jpg'}
/>
```

### Update Category Image

```javascript
// Upload new image and update category
const updateCategoryImage = async (categoryId, newImageFile) => {
  // 1. Upload new image
  const imagePath = await uploadImage(newImageFile);
  
  // 2. Update category
  const response = await fetch(
    `http://localhost:8000/api/v1/categories/${categoryId}`,
    {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        image: imagePath
      })
    }
  );
  
  return await response.json();
};
```

---

## Frontend Examples

### React Component with Image Upload

```typescript
import React, { useState } from 'react';
import axios from 'axios';

interface CategoryFormProps {
  token: string;
}

const CategoryForm: React.FC<CategoryFormProps> = ({ token }) => {
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string>('');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string>('');

  const API_BASE = 'http://localhost:8000';

  // Handle image selection
  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      setError('Only JPG, PNG, GIF, and WebP images are allowed');
      return;
    }

    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB');
      return;
    }

    setImage(file);
    setError('');
    
    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  // Upload image
  const uploadImage = async (file: File): Promise<string> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('folder', 'categories');

    try {
      const response = await axios.post(
        `${API_BASE}/api/v1/filemanager/upload`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );
      
      return response.data.file_path;
    } catch (err: any) {
      throw new Error(err.response?.data?.detail || 'Upload failed');
    }
  };

  // Create category
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setUploading(true);
    setError('');

    try {
      // Upload image if provided
      let imagePath = '';
      if (image) {
        imagePath = await uploadImage(image);
      }

      // Create category
      const response = await axios.post(
        `${API_BASE}/api/v1/categories/`,
        {
          name,
          slug,
          image: imagePath,
          active: true,
          sort_order: 0
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      alert('Category created successfully!');
      
      // Reset form
      setName('');
      setSlug('');
      setImage(null);
      setImagePreview('');
      
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to create category');
    } finally {
      setUploading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="category-form">
      <h2>Create Category</h2>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="form-group">
        <label htmlFor="name">Category Name *</label>
        <input
          id="name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          placeholder="e.g., Beverages"
        />
      </div>

      <div className="form-group">
        <label htmlFor="slug">Slug *</label>
        <input
          id="slug"
          type="text"
          value={slug}
          onChange={(e) => setSlug(e.target.value)}
          required
          placeholder="e.g., beverages"
        />
      </div>

      <div className="form-group">
        <label htmlFor="image">Category Image</label>
        <input
          id="image"
          type="file"
          accept="image/jpeg,image/jpg,image/png,image/gif,image/webp"
          onChange={handleImageChange}
        />
        <small>Max size: 10MB. Formats: JPG, PNG, GIF, WebP</small>
      </div>

      {imagePreview && (
        <div className="image-preview">
          <img src={imagePreview} alt="Preview" style={{ maxWidth: '200px' }} />
        </div>
      )}

      <button type="submit" disabled={uploading}>
        {uploading ? 'Creating...' : 'Create Category'}
      </button>
    </form>
  );
};

export default CategoryForm;
```

---

### HTML + JavaScript (Vanilla)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Category Image Upload</title>
    <style>
        .form-group { margin-bottom: 15px; }
        .error { color: red; padding: 10px; background: #fee; }
        .success { color: green; padding: 10px; background: #efe; }
        .preview { max-width: 300px; margin: 10px 0; }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
    </style>
</head>
<body>
    <h1>Create Category with Image</h1>
    
    <div id="message"></div>
    
    <form id="categoryForm">
        <div class="form-group">
            <label>Category Name:</label>
            <input type="text" id="name" required>
        </div>
        
        <div class="form-group">
            <label>Slug:</label>
            <input type="text" id="slug" required>
        </div>
        
        <div class="form-group">
            <label>Category Image:</label>
            <input type="file" id="imageFile" accept="image/*">
            <small>Max 10MB. JPG, PNG, GIF, WebP only</small>
        </div>
        
        <div id="imagePreview"></div>
        
        <button type="submit" id="submitBtn">Create Category</button>
    </form>

    <script>
        const API_BASE = 'http://localhost:8000';
        const token = localStorage.getItem('access_token'); // Your JWT token

        const messageDiv = document.getElementById('message');
        const form = document.getElementById('categoryForm');
        const imageInput = document.getElementById('imageFile');
        const previewDiv = document.getElementById('imagePreview');
        const submitBtn = document.getElementById('submitBtn');

        // Image preview
        imageInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (!file) return;

            // Validate size
            if (file.size > 10 * 1024 * 1024) {
                showMessage('File size must be less than 10MB', 'error');
                imageInput.value = '';
                return;
            }

            // Show preview
            const reader = new FileReader();
            reader.onload = (e) => {
                previewDiv.innerHTML = `<img src="${e.target.result}" class="preview">`;
            };
            reader.readAsDataURL(file);
        });

        // Form submission
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const name = document.getElementById('name').value;
            const slug = document.getElementById('slug').value;
            const imageFile = imageInput.files[0];

            submitBtn.disabled = true;
            submitBtn.textContent = 'Creating...';
            messageDiv.innerHTML = '';

            try {
                let imagePath = '';

                // Upload image if selected
                if (imageFile) {
                    const formData = new FormData();
                    formData.append('file', imageFile);
                    formData.append('folder', 'categories');

                    const uploadResponse = await fetch(
                        `${API_BASE}/api/v1/filemanager/upload`,
                        {
                            method: 'POST',
                            headers: {
                                'Authorization': `Bearer ${token}`
                            },
                            body: formData
                        }
                    );

                    if (!uploadResponse.ok) {
                        const error = await uploadResponse.json();
                        throw new Error(error.detail || 'Upload failed');
                    }

                    const uploadData = await uploadResponse.json();
                    imagePath = uploadData.file_path;
                }

                // Create category
                const categoryResponse = await fetch(
                    `${API_BASE}/api/v1/categories/`,
                    {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            name: name,
                            slug: slug,
                            image: imagePath,
                            active: true,
                            sort_order: 0
                        })
                    }
                );

                if (!categoryResponse.ok) {
                    const error = await categoryResponse.json();
                    throw new Error(error.detail || 'Failed to create category');
                }

                const categoryData = await categoryResponse.json();
                showMessage('Category created successfully!', 'success');
                
                // Reset form
                form.reset();
                previewDiv.innerHTML = '';
                
                console.log('Created category:', categoryData);

            } catch (error) {
                showMessage(`Error: ${error.message}`, 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Create Category';
            }
        });

        function showMessage(text, type) {
            messageDiv.className = type;
            messageDiv.textContent = text;
        }
    </script>
</body>
</html>
```

---

### Vue.js Component

```vue
<template>
  <div class="category-form">
    <h2>Create Category</h2>
    
    <div v-if="message" :class="['message', messageType]">
      {{ message }}
    </div>
    
    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <label for="name">Category Name *</label>
        <input
          id="name"
          v-model="formData.name"
          type="text"
          required
          placeholder="e.g., Beverages"
        />
      </div>

      <div class="form-group">
        <label for="slug">Slug *</label>
        <input
          id="slug"
          v-model="formData.slug"
          type="text"
          required
          placeholder="e.g., beverages"
        />
      </div>

      <div class="form-group">
        <label for="image">Category Image</label>
        <input
          id="image"
          type="file"
          accept="image/jpeg,image/jpg,image/png,image/gif,image/webp"
          @change="handleImageChange"
        />
        <small>Max size: 10MB. Formats: JPG, PNG, GIF, WebP</small>
      </div>

      <div v-if="imagePreview" class="image-preview">
        <img :src="imagePreview" alt="Preview" />
      </div>

      <button type="submit" :disabled="loading">
        {{ loading ? 'Creating...' : 'Create Category' }}
      </button>
    </form>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'CategoryForm',
  props: {
    token: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      formData: {
        name: '',
        slug: ''
      },
      imageFile: null,
      imagePreview: '',
      loading: false,
      message: '',
      messageType: '',
      API_BASE: 'http://localhost:8000'
    };
  },
  methods: {
    handleImageChange(event) {
      const file = event.target.files[0];
      if (!file) return;

      // Validate file type
      const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
      if (!allowedTypes.includes(file.type)) {
        this.showMessage('Only JPG, PNG, GIF, and WebP images are allowed', 'error');
        event.target.value = '';
        return;
      }

      // Validate file size (10MB)
      if (file.size > 10 * 1024 * 1024) {
        this.showMessage('File size must be less than 10MB', 'error');
        event.target.value = '';
        return;
      }

      this.imageFile = file;
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        this.imagePreview = e.target.result;
      };
      reader.readAsDataURL(file);
    },

    async uploadImage(file) {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('folder', 'categories');

      try {
        const response = await axios.post(
          `${this.API_BASE}/api/v1/filemanager/upload`,
          formData,
          {
            headers: {
              'Authorization': `Bearer ${this.token}`,
              'Content-Type': 'multipart/form-data'
            }
          }
        );
        
        return response.data.file_path;
      } catch (error) {
        throw new Error(error.response?.data?.detail || 'Upload failed');
      }
    },

    async handleSubmit() {
      this.loading = true;
      this.message = '';

      try {
        // Upload image if provided
        let imagePath = '';
        if (this.imageFile) {
          imagePath = await this.uploadImage(this.imageFile);
        }

        // Create category
        const response = await axios.post(
          `${this.API_BASE}/api/v1/categories/`,
          {
            name: this.formData.name,
            slug: this.formData.slug,
            image: imagePath,
            active: true,
            sort_order: 0
          },
          {
            headers: {
              'Authorization': `Bearer ${this.token}`,
              'Content-Type': 'application/json'
            }
          }
        );

        this.showMessage('Category created successfully!', 'success');
        
        // Reset form
        this.formData.name = '';
        this.formData.slug = '';
        this.imageFile = null;
        this.imagePreview = '';
        
        this.$emit('category-created', response.data);
        
      } catch (error) {
        this.showMessage(
          error.response?.data?.detail || error.message || 'Failed to create category',
          'error'
        );
      } finally {
        this.loading = false;
      }
    },

    showMessage(text, type) {
      this.message = text;
      this.messageType = type;
      
      // Auto-hide success messages after 3 seconds
      if (type === 'success') {
        setTimeout(() => {
          this.message = '';
        }, 3000);
      }
    }
  }
};
</script>

<style scoped>
.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-group input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.form-group small {
  display: block;
  margin-top: 5px;
  color: #666;
  font-size: 12px;
}

.image-preview {
  margin: 15px 0;
}

.image-preview img {
  max-width: 300px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

button {
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.message {
  padding: 10px;
  margin-bottom: 15px;
  border-radius: 4px;
}

.message.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.message.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}
</style>
```

---

## Best Practices

### 1. Image Organization

**Folder Structure:**
```
uploads/
├── categories/
│   ├── beverages.jpg
│   ├── main-course.jpg
│   └── desserts.jpg
├── products/
│   ├── coffee.jpg
│   ├── burger.jpg
│   └── cake.jpg
└── users/
    └── avatars/
```

**Usage:**
```javascript
// Upload to specific folder
formData.append('folder', 'categories');  // → uploads/categories/
formData.append('folder', 'products');    // → uploads/products/
formData.append('folder', 'users/avatars'); // → uploads/users/avatars/
```

### 2. File Naming

**Auto-Increment on Duplicates:**
- Original: `beverages.jpg`
- If exists: `beverages_1.jpg`
- If exists: `beverages_2.jpg`

**Manual Unique Names:**
```javascript
// Add timestamp to filename
const uniqueFileName = `${Date.now()}_${file.name}`;

// Or use UUID
import { v4 as uuidv4 } from 'uuid';
const uniqueFileName = `${uuidv4()}_${file.name}`;
```

### 3. Image Validation (Client-Side)

```javascript
const validateImage = (file) => {
  const errors = [];
  
  // Check file type
  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
  if (!allowedTypes.includes(file.type)) {
    errors.push('Invalid file type. Use JPG, PNG, GIF, or WebP');
  }
  
  // Check file size (10MB)
  const maxSize = 10 * 1024 * 1024;
  if (file.size > maxSize) {
    errors.push(`File too large. Max size: ${maxSize / 1024 / 1024}MB`);
  }
  
  // Check filename
  const invalidChars = /[<>:"/\\|?*]/;
  if (invalidChars.test(file.name)) {
    errors.push('Filename contains invalid characters');
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
};
```

### 4. Image Compression (Before Upload)

```javascript
const compressImage = (file, maxWidth = 800, quality = 0.8) => {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    
    reader.onload = (e) => {
      const img = new Image();
      img.src = e.target.result;
      
      img.onload = () => {
        const canvas = document.createElement('canvas');
        let width = img.width;
        let height = img.height;
        
        // Resize if too large
        if (width > maxWidth) {
          height = (height * maxWidth) / width;
          width = maxWidth;
        }
        
        canvas.width = width;
        canvas.height = height;
        
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, width, height);
        
        canvas.toBlob((blob) => {
          resolve(new File([blob], file.name, {
            type: 'image/jpeg',
            lastModified: Date.now()
          }));
        }, 'image/jpeg', quality);
      };
    };
  });
};

// Usage
const compressedFile = await compressImage(originalFile, 800, 0.8);
```

### 5. Error Handling

```javascript
const uploadWithRetry = async (file, maxRetries = 3) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await uploadImage(file);
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      
      // Wait before retry (exponential backoff)
      await new Promise(resolve => 
        setTimeout(resolve, Math.pow(2, i) * 1000)
      );
    }
  }
};
```

### 6. Progress Tracking

```javascript
const uploadWithProgress = (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('folder', 'categories');

  return axios.post(
    `${API_BASE}/api/v1/filemanager/upload`,
    formData,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        onProgress(percentCompleted);
      }
    }
  );
};

// Usage
await uploadWithProgress(file, (percent) => {
  console.log(`Upload progress: ${percent}%`);
  // Update progress bar UI
});
```

### 7. Lazy Loading Images

```javascript
// React example with lazy loading
const LazyImage = ({ src, alt, placeholder = '/placeholder.jpg' }) => {
  const [imageSrc, setImageSrc] = useState(placeholder);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const img = new Image();
    img.src = src;
    img.onload = () => {
      setImageSrc(src);
      setLoading(false);
    };
  }, [src]);

  return (
    <img 
      src={imageSrc} 
      alt={alt}
      className={loading ? 'loading' : 'loaded'}
    />
  );
};
```

---

## Common Issues & Solutions

### Issue 1: CORS Error
**Problem:** Browser blocks request due to CORS policy  
**Solution:** Ensure FastAPI has CORS middleware configured:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue 2: 401 Unauthorized
**Problem:** Missing or invalid authentication token  
**Solution:** Include JWT token in Authorization header:
```javascript
headers: {
  'Authorization': `Bearer ${token}`
}
```

### Issue 3: Image Not Displaying
**Problem:** Image path incorrect or file doesn't exist  
**Solution:** 
- Store relative path in database: `"categories/image.jpg"`
- Access via: `/api/v1/filemanager/view/categories/image.jpg`
- Check file exists in `uploads/` directory

### Issue 4: Upload Fails Silently
**Problem:** No error shown but image not uploaded  
**Solution:** Check browser console and network tab for errors

---

## Testing

### cURL Test Upload

```bash
# Upload image
curl -X POST "http://localhost:8000/api/v1/filemanager/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/beverages.jpg" \
  -F "folder=categories"

# Expected response:
# {
#   "success": true,
#   "file_path": "categories/beverages.jpg",
#   ...
# }

# View uploaded image
curl -X GET "http://localhost:8000/api/v1/filemanager/view/categories/beverages.jpg" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --output test-download.jpg

# Create category with image
curl -X POST "http://localhost:8000/api/v1/categories/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Beverages",
    "slug": "beverages",
    "image": "categories/beverages.jpg",
    "active": true
  }'
```

---

## Security Considerations

1. **File Type Validation:** Only allow specific image formats
2. **File Size Limits:** Prevent large file uploads (10MB max)
3. **Path Traversal Protection:** Validate all file paths
4. **Authentication:** Require JWT token for all uploads
5. **Filename Sanitization:** Remove dangerous characters
6. **Virus Scanning:** Consider integrating antivirus (ClamAV) for production

---

## Performance Tips

1. **Compress images** before upload (client-side)
2. **Use CDN** for serving images in production
3. **Implement caching** headers for images
4. **Lazy load** images in frontend
5. **Use WebP format** for better compression
6. **Optimize thumbnails** for listing pages

---

## Related Documentation

- [Category API Integration](./CATEGORY_API_INTEGRATION.md)
- [File Manager API](./FILE_MANAGER_API.md)
- [Authentication Guide](./API_REFERENCE.md#authentication)

---

**Last Updated:** November 24, 2024  
**Author:** Restaurant POS Development Team
