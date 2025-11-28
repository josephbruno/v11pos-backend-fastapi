# Product API Documentation

Complete API reference for Product management endpoints with automatic image processing.

## Base URL
```
http://localhost:8000/api/v1/products
```

## Authentication
All endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

---

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Create a new product with optional image |
| GET | `/` | Get all products with pagination |
| GET | `/{product_id}` | Get a specific product by ID |
| PUT | `/{product_id}` | Update a product with optional image |
| DELETE | `/{product_id}` | Delete a product |

---

## Image Specifications

### Automatic Processing
- **Target Dimensions:** 800x800 pixels (square)
- **Output Format:** WebP
- **Maximum File Size:** 200 KB (automatically enforced)
- **Storage Location:** `/uploads/products/`
- **Quality:** Adaptive (85 → 50) to meet size requirement
- **Resampling:** High-quality LANCZOS algorithm

### Supported Input Formats
- JPG/JPEG
- PNG
- GIF
- WebP
- BMP

### Processing Features
✅ Automatic resizing to 800x800px  
✅ WebP conversion for optimal compression  
✅ Quality adjustment to stay under 200KB  
✅ Center-padding for smaller images  
✅ Transparency handling (white background)  
✅ Old image auto-deletion on update/delete  

---

## 1. Create Product

Create a new product with optional image upload.

### Endpoint
```http
POST /api/v1/products/
```

### Headers
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

### Request Body (Form Data)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Product name |
| slug | string | Yes | URL-friendly identifier (unique) |
| category_id | string (UUID) | Yes | Category UUID |
| price | number | Yes | Product price |
| description | string | No | Product description |
| sku | string | No | Stock Keeping Unit |
| stock | integer | No | Available quantity (default: 0) |
| is_available | boolean | No | Availability status (default: true) |
| image | file | No | Product image (auto-resized to 800x800px, <200KB WebP) |

### Example Request (cURL)
```bash
curl -X POST "http://localhost:8000/api/v1/products/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "name=Buffalo Wings" \
  -F "slug=buffalo-wings" \
  -F "category_id=140a0e11-7a3b-4900-96dc-fb252156499a" \
  -F "price=1299" \
  -F "description=Crispy chicken wings with buffalo sauce" \
  -F "sku=WINGS-001" \
  -F "stock=50" \
  -F "is_available=true" \
  -F "image=@/path/to/wings.jpg"
```

### Example Request (Python)
```python
import requests

url = "http://localhost:8000/api/v1/products/"
headers = {"Authorization": "Bearer YOUR_TOKEN"}

data = {
    "name": "Buffalo Wings",
    "slug": "buffalo-wings",
    "category_id": "140a0e11-7a3b-4900-96dc-fb252156499a",
    "price": 1299,
    "description": "Crispy chicken wings with buffalo sauce",
    "sku": "WINGS-001",
    "stock": 50,
    "is_available": True
}

files = {
    "image": open("wings.jpg", "rb")
}

response = requests.post(url, headers=headers, data=data, files=files)
print(response.json())
```

### Success Response (201 Created)
```json
{
  "id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
  "name": "Buffalo Wings",
  "slug": "buffalo-wings",
  "description": "Crispy chicken wings with buffalo sauce",
  "price": 1299,
  "category_id": "140a0e11-7a3b-4900-96dc-fb252156499a",
  "sku": "WINGS-001",
  "stock": 50,
  "is_available": true,
  "image_url": "/uploads/products/wings.webp",
  "created_at": "2025-11-24T10:30:00Z",
  "updated_at": "2025-11-24T10:30:00Z"
}
```

### Image Processing Result
```
Original:  wings.jpg (450 KB, 2000x1500px)
Processed: wings.webp (145 KB, 800x800px)
Reduction: 67.8%
Quality:   75 (auto-adjusted)
```

---

## 2. Get All Products

Retrieve all products with pagination support.

### Endpoint
```http
GET /api/v1/products/
```

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| skip | integer | 0 | Number of records to skip |
| limit | integer | 100 | Maximum records to return |

### Example Request
```bash
curl -X GET "http://localhost:8000/api/v1/products/?skip=0&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Success Response (200 OK)
```json
[
  {
    "id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
    "name": "Buffalo Wings",
    "slug": "buffalo-wings",
    "description": "Crispy chicken wings with buffalo sauce",
    "price": 1299,
    "category_id": "140a0e11-7a3b-4900-96dc-fb252156499a",
    "sku": "WINGS-001",
    "stock": 50,
    "is_available": true,
    "image_url": "/uploads/products/wings.webp",
    "created_at": "2025-11-24T10:30:00Z",
    "updated_at": "2025-11-24T10:30:00Z"
  },
  {
    "id": "b2c3d4e5-f6a7-4b5c-8d9e-0f1a2b3c4d5e",
    "name": "Caesar Salad",
    "slug": "caesar-salad",
    "description": "Fresh romaine lettuce with Caesar dressing",
    "price": 899,
    "category_id": "140a0e11-7a3b-4900-96dc-fb252156499a",
    "sku": "SALAD-001",
    "stock": 30,
    "is_available": true,
    "image_url": "/uploads/products/caesar-salad.webp",
    "created_at": "2025-11-24T10:35:00Z",
    "updated_at": "2025-11-24T10:35:00Z"
  }
]
```

---

## 3. Get Product by ID

Retrieve a specific product by its UUID.

### Endpoint
```http
GET /api/v1/products/{product_id}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| product_id | string (UUID) | Yes | Product unique identifier |

### Example Request
```bash
curl -X GET "http://localhost:8000/api/v1/products/a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Success Response (200 OK)
```json
{
  "id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
  "name": "Buffalo Wings",
  "slug": "buffalo-wings",
  "description": "Crispy chicken wings with buffalo sauce",
  "price": 1299,
  "category_id": "140a0e11-7a3b-4900-96dc-fb252156499a",
  "sku": "WINGS-001",
  "stock": 50,
  "is_available": true,
  "image_url": "/uploads/products/wings.webp",
  "created_at": "2025-11-24T10:30:00Z",
  "updated_at": "2025-11-24T10:30:00Z"
}
```

### Error Response (404 Not Found)
```json
{
  "detail": "Product with id a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d not found"
}
```

---

## 4. Update Product

Update an existing product. All fields are optional. Providing a new image will automatically delete the old one.

### Endpoint
```http
PUT /api/v1/products/{product_id}
```

### Headers
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| product_id | string (UUID) | Yes | Product unique identifier |

### Request Body (Form Data)

All fields are optional. Only include fields you want to update.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | No | Product name |
| slug | string | No | URL-friendly identifier |
| category_id | string (UUID) | No | Category UUID |
| price | number | No | Product price |
| description | string | No | Product description |
| sku | string | No | Stock Keeping Unit |
| stock | integer | No | Available quantity |
| is_available | boolean | No | Availability status |
| image | file | No | New product image (replaces old image) |

### Example Request - Update Price and Stock
```bash
curl -X PUT "http://localhost:8000/api/v1/products/a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "price=1499" \
  -F "stock=75"
```

### Example Request - Update Image
```bash
curl -X PUT "http://localhost:8000/api/v1/products/a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "image=@/path/to/new-wings.jpg"
```

### Example Request - Update Multiple Fields
```bash
curl -X PUT "http://localhost:8000/api/v1/products/a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "name=Spicy Buffalo Wings" \
  -F "description=Extra spicy chicken wings" \
  -F "price=1499" \
  -F "stock=75" \
  -F "image=@/path/to/spicy-wings.jpg"
```

### Success Response (200 OK)
```json
{
  "id": "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
  "name": "Spicy Buffalo Wings",
  "slug": "buffalo-wings",
  "description": "Extra spicy chicken wings",
  "price": 1499,
  "category_id": "140a0e11-7a3b-4900-96dc-fb252156499a",
  "sku": "WINGS-001",
  "stock": 75,
  "is_available": true,
  "image_url": "/uploads/products/spicy-wings.webp",
  "created_at": "2025-11-24T10:30:00Z",
  "updated_at": "2025-11-24T11:45:00Z"
}
```

### Image Update Behavior
- Old image (`wings.webp`) is automatically deleted
- New image (`spicy-wings.jpg`) is processed and saved as `spicy-wings.webp`
- Image automatically resized to 800x800px and optimized to <200KB

---

## 5. Delete Product

Delete a product and its associated image file.

### Endpoint
```http
DELETE /api/v1/products/{product_id}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| product_id | string (UUID) | Yes | Product unique identifier |

### Example Request
```bash
curl -X DELETE "http://localhost:8000/api/v1/products/a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Success Response (200 OK)
```json
{
  "message": "Product deleted successfully"
}
```

### Delete Behavior
- Product record removed from database
- Associated image file (`/uploads/products/wings.webp`) automatically deleted
- Related orders retain product information (soft reference)

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid input data"
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
  "detail": "Product with id a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "price"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Image Processing Details

### Processing Pipeline

1. **Upload Validation**
   - Check file format (JPG, PNG, GIF, WebP, BMP)
   - Reject unsupported formats

2. **Image Loading**
   - Open with Pillow (PIL)
   - Convert RGBA/LA/P to RGB (white background)

3. **Resizing**
   - Target: 800x800 pixels
   - Algorithm: LANCZOS (high quality)
   - Center-padding if image smaller than target

4. **WebP Conversion**
   - Initial quality: 85
   - Compression method: 6 (best)

5. **Quality Adjustment**
   - Check file size
   - If > 200KB, reduce quality by 10
   - Repeat up to 5 times (85→75→65→55→50)
   - Stop when size ≤ 200KB or quality ≤ 50

6. **Save**
   - Format: WebP
   - Location: `/uploads/products/`
   - Filename: Original name with `.webp` extension

### Processing Examples

| Original | Size | Dimensions | Result | Size | Dimensions | Quality | Reduction |
|----------|------|------------|--------|------|------------|---------|-----------|
| wings.jpg | 450 KB | 2000x1500 | wings.webp | 145 KB | 800x800 | 75 | 67.8% |
| salad.png | 1.2 MB | 3000x3000 | salad.webp | 95 KB | 800x800 | 65 | 92.1% |
| burger.jpg | 180 KB | 1200x900 | burger.webp | 125 KB | 800x800 | 85 | 30.6% |
| small.jpg | 50 KB | 400x400 | small.webp | 35 KB | 800x800 | 85 | 30.0% |

---

## Best Practices

### Image Upload

✅ **DO:**
- Use high-quality source images (at least 800x800px)
- Upload JPG, PNG, or WebP formats
- Let backend handle resizing and optimization
- Use descriptive filenames

❌ **DON'T:**
- Pre-resize images on client side
- Use extremely large images (>5MB)
- Assume client-side optimization is needed
- Worry about file size limits

### Product Creation

✅ **DO:**
- Use unique, SEO-friendly slugs
- Provide clear, descriptive names
- Include accurate stock counts
- Set appropriate availability status
- Add comprehensive descriptions

❌ **DON'T:**
- Reuse slugs across products
- Leave price as zero unless intentional
- Forget to associate with valid category
- Skip SKU if using inventory tracking

### Product Updates

✅ **DO:**
- Update only changed fields
- Use partial updates for efficiency
- Test image updates in staging first
- Verify old images are cleaned up

❌ **DON'T:**
- Send all fields for small changes
- Update slug unnecessarily (breaks URLs)
- Upload new image without checking result
- Delete products with active orders

---

## Testing Examples

### Test Product Creation
```bash
# Test with image
curl -X POST "http://localhost:8000/api/v1/products/" \
  -H "Authorization: Bearer $TOKEN" \
  -F "name=Test Product" \
  -F "slug=test-product-$(date +%s)" \
  -F "category_id=YOUR_CATEGORY_ID" \
  -F "price=999" \
  -F "image=@test-image.jpg"

# Test without image
curl -X POST "http://localhost:8000/api/v1/products/" \
  -H "Authorization: Bearer $TOKEN" \
  -F "name=No Image Product" \
  -F "slug=no-image-$(date +%s)" \
  -F "category_id=YOUR_CATEGORY_ID" \
  -F "price=799"
```

### Test Image Update
```bash
PRODUCT_ID="your-product-id"

# Update only image
curl -X PUT "http://localhost:8000/api/v1/products/$PRODUCT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@new-image.jpg"

# Verify image processed correctly
curl -s "http://localhost:8000/api/v1/products/$PRODUCT_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '.image_url'
```

### Test Large Image Handling
```bash
# Download large test image
wget -O large-test.jpg "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=2000"

# Upload (will be auto-optimized)
curl -X POST "http://localhost:8000/api/v1/products/" \
  -H "Authorization: Bearer $TOKEN" \
  -F "name=Large Image Test" \
  -F "slug=large-test-$(date +%s)" \
  -F "category_id=YOUR_CATEGORY_ID" \
  -F "price=1500" \
  -F "image=@large-test.jpg"

# Check result
ls -lh uploads/products/ | grep webp
```

---

## Integration Examples

### React/Next.js
```javascript
async function createProduct(formData) {
  const data = new FormData();
  data.append('name', formData.name);
  data.append('slug', formData.slug);
  data.append('category_id', formData.categoryId);
  data.append('price', formData.price);
  data.append('description', formData.description);
  
  if (formData.image) {
    data.append('image', formData.image);
  }

  const response = await fetch('http://localhost:8000/api/v1/products/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: data
  });

  return response.json();
}
```

### Vue.js
```javascript
async function uploadProduct(product, imageFile) {
  const formData = new FormData();
  
  Object.keys(product).forEach(key => {
    formData.append(key, product[key]);
  });
  
  if (imageFile) {
    formData.append('image', imageFile);
  }

  const response = await axios.post(
    'http://localhost:8000/api/v1/products/',
    formData,
    {
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'multipart/form-data'
      }
    }
  );

  return response.data;
}
```

### Python Requests
```python
def create_product_with_image(token, product_data, image_path=None):
    """Create product with optional image upload."""
    url = "http://localhost:8000/api/v1/products/"
    headers = {"Authorization": f"Bearer {token}"}
    
    files = {}
    if image_path:
        files['image'] = open(image_path, 'rb')
    
    response = requests.post(
        url,
        headers=headers,
        data=product_data,
        files=files
    )
    
    if files:
        files['image'].close()
    
    return response.json()
```

---

## FAQ

### Q: What happens if I upload a very large image?
**A:** The backend automatically resizes it to 800x800px and adjusts quality to keep the file under 200KB. A 5MB image might be reduced to 80KB with no visible quality loss.

### Q: Can I upload images larger than 200KB?
**A:** Yes! Upload any size. The backend handles optimization automatically.

### Q: What if my image is smaller than 800x800?
**A:** It will be center-padded with a white background to reach 800x800px.

### Q: Are old images deleted when updating?
**A:** Yes, when you upload a new image, the old one is automatically removed from disk.

### Q: Can I remove an image without uploading a new one?
**A:** Currently, images can only be replaced. To remove, you'd need to update with a placeholder image or delete and recreate the product.

### Q: What image formats are supported?
**A:** Input: JPG, JPEG, PNG, GIF, WebP, BMP. Output: Always WebP for optimal compression.

### Q: How do I access the uploaded images?
**A:** Use the `image_url` field from the API response. Serve via static file handler or CDN.

### Q: Why WebP format?
**A:** WebP provides 25-35% better compression than JPEG with equivalent quality, reducing bandwidth and improving load times.

### Q: Does the API support bulk uploads?
**A:** Currently, products are created one at a time. For bulk operations, call the endpoint multiple times or use batch processing scripts.

### Q: What if the category_id doesn't exist?
**A:** You'll receive a 422 error indicating the foreign key constraint failed.

---

## Changelog

### v1.2.0 (2025-11-24)
- ✅ Added automatic image resizing to 800x800px
- ✅ Implemented adaptive quality adjustment (<200KB)
- ✅ WebP conversion for all uploaded images
- ✅ LANCZOS resampling for high-quality scaling
- ✅ Automatic old image cleanup on update/delete

### v1.1.0 (2025-11-23)
- ✅ Changed to multipart/form-data for image uploads
- ✅ Added direct image upload support
- ✅ Fixed UUID string comparison bug

### v1.0.0 (2025-11-20)
- ✅ Initial product API implementation
- ✅ CRUD operations
- ✅ JWT authentication

---

## Support

For issues or questions:
- Check error messages in API responses
- Verify image formats are supported
- Ensure category_id exists before creating products
- Test with small images first
- Review logs for processing details

**API Version:** 1.2.0  
**Last Updated:** November 24, 2025  
**Status:** ✅ Production Ready
