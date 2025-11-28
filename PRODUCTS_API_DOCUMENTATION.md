# Products API Integration Documentation

## Overview

Complete guide for integrating with the Restaurant POS Products API. All endpoints support pagination and require authentication.

---

## Authentication Required

All product endpoints require a valid JWT token in the Authorization header:

```
Authorization: Bearer <access_token>
```

Get your token from the [Login API](LOGIN_API_DOCUMENTATION.md).

---

## Base URL

```
http://localhost:8000/api/v1/products
```

---

## Endpoints

### 1. List Products (GET)

Retrieve a paginated list of all products with optional filtering.

#### Endpoint
```
GET /api/v1/products/
```

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| page | integer | No | 1 | Page number (starts at 1) |
| page_size | integer | No | 10 | Items per page (max: 100) |
| category_id | string | No | - | Filter by category UUID |
| available | boolean | No | - | Filter by availability |
| featured | boolean | No | - | Filter featured products |
| search | string | No | - | Search in name/description |
| min_price | integer | No | - | Minimum price in cents |
| max_price | integer | No | - | Maximum price in cents |

#### Success Response (200 OK)

```json
{
  "status": "success",
  "message": "Products retrieved successfully",
  "data": [
    {
      "id": "09292578-5eee-4f48-baf3-eb62a7046c1f",
      "name": "Buffalo Wings",
      "slug": "buffalo-wings",
      "description": "Spicy chicken wings",
      "price": 1250,
      "cost": 750,
      "category_id": "140a0e11-7a3b-4900-96dc-fb252156499a",
      "stock": 100,
      "min_stock": 5,
      "available": true,
      "featured": false,
      "image": null,
      "images": [],
      "tags": [],
      "department": "kitchen",
      "printer_tag": null,
      "preparation_time": 15,
      "nutritional_info": null,
      "created_at": "2025-11-23T08:29:58",
      "updated_at": "2025-11-23T08:29:58"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_items": 29,
    "total_pages": 3,
    "has_next": true,
    "has_previous": false
  }
}
```

#### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique product identifier (UUID) |
| name | string | Product name |
| slug | string | URL-friendly identifier |
| description | string | Product description |
| price | integer | Price in cents (e.g., 1250 = $12.50) |
| cost | integer | Cost price in cents |
| category_id | string | Category UUID |
| stock | integer | Current stock quantity |
| min_stock | integer | Minimum stock alert level |
| available | boolean | Product availability status |
| featured | boolean | Featured product flag |
| image | string\|null | Main product image URL |
| images | array | Additional product images |
| tags | array | Product tags |
| department | string | Department (e.g., "kitchen", "bar") |
| printer_tag | string\|null | Printer destination |
| preparation_time | integer | Estimated prep time in minutes |
| nutritional_info | object\|null | Nutritional information |
| created_at | string | Creation timestamp |
| updated_at | string | Last update timestamp |

---

### 2. Get Single Product (GET)

Retrieve detailed information about a specific product.

#### Endpoint
```
GET /api/v1/products/{product_id}
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| product_id | string | Yes | Product UUID |

#### Success Response (200 OK)

```json
{
  "status": "success",
  "message": "Product retrieved successfully",
  "data": {
    "id": "09292578-5eee-4f48-baf3-eb62a7046c1f",
    "name": "Buffalo Wings",
    "slug": "buffalo-wings",
    "description": "Spicy chicken wings",
    "price": 1250,
    "cost": 750,
    "category_id": "140a0e11-7a3b-4900-96dc-fb252156499a",
    "stock": 100,
    "min_stock": 5,
    "available": true,
    "featured": false,
    "image": null,
    "images": [],
    "tags": [],
    "department": "kitchen",
    "printer_tag": null,
    "preparation_time": 15,
    "nutritional_info": null,
    "created_at": "2025-11-23T08:29:58",
    "updated_at": "2025-11-23T08:29:58"
  }
}
```

#### Error Response (404 Not Found)

```json
{
  "detail": "Product not found"
}
```

---

### 3. Create Product (POST)

Create a new product. **Requires admin/manager role**.

#### Endpoint
```
POST /api/v1/products/
```

#### Request Body

```json
{
  "name": "New Product",
  "slug": "new-product",
  "description": "Product description",
  "price": 1500,
  "cost": 900,
  "category_id": "category-uuid",
  "stock": 50,
  "min_stock": 10,
  "available": true,
  "featured": false,
  "department": "kitchen",
  "preparation_time": 20
}
```

#### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| name | string | Product name (max 200 chars) |
| slug | string | URL-friendly identifier (unique) |
| price | integer | Price in cents |
| category_id | string | Valid category UUID |

#### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| description | string | null | Product description |
| cost | integer | 0 | Cost price in cents |
| stock | integer | 0 | Initial stock quantity |
| min_stock | integer | 5 | Minimum stock level |
| available | boolean | true | Availability status |
| featured | boolean | false | Featured flag |
| image | string | null | Main image URL |
| images | array | [] | Additional images |
| tags | array | [] | Product tags |
| department | string | "kitchen" | Department |
| printer_tag | string | null | Printer destination |
| preparation_time | integer | 15 | Prep time in minutes |
| nutritional_info | object | null | Nutritional data |

#### Success Response (201 Created)

```json
{
  "status": "success",
  "message": "Product created successfully",
  "data": {
    "id": "new-product-uuid",
    "name": "New Product",
    ...
  }
}
```

---

### 4. Update Product (PUT)

Update an existing product. **Requires admin/manager role**.

#### Endpoint
```
PUT /api/v1/products/{product_id}
```

#### Request Body

Same as Create Product (all fields optional except those you want to update).

#### Success Response (200 OK)

```json
{
  "status": "success",
  "message": "Product updated successfully",
  "data": {
    "id": "product-uuid",
    "name": "Updated Product Name",
    ...
  }
}
```

---

### 5. Delete Product (DELETE)

Delete a product. **Requires admin/manager role**.

#### Endpoint
```
DELETE /api/v1/products/{product_id}
```

#### Success Response (200 OK)

```json
{
  "status": "success",
  "message": "Product deleted successfully"
}
```

---

## Integration Examples

### JavaScript (Fetch API)

#### Get All Products with Pagination

```javascript
async function getProducts(page = 1, pageSize = 10) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(
    `http://localhost:8000/api/v1/products/?page=${page}&page_size=${pageSize}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to fetch products');
  }
  
  const result = await response.json();
  return result;
}

// Usage
getProducts(1, 20)
  .then(result => {
    console.log('Products:', result.data);
    console.log('Total items:', result.pagination.total_items);
    console.log('Total pages:', result.pagination.total_pages);
  })
  .catch(error => console.error('Error:', error));
```

#### Get Single Product

```javascript
async function getProduct(productId) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(
    `http://localhost:8000/api/v1/products/${productId}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  if (!response.ok) {
    throw new Error('Product not found');
  }
  
  const result = await response.json();
  return result.data;
}
```

#### Filter Products

```javascript
async function searchProducts(query, filters = {}) {
  const token = localStorage.getItem('access_token');
  
  const params = new URLSearchParams({
    search: query,
    page: filters.page || 1,
    page_size: filters.pageSize || 10,
    ...(filters.categoryId && { category_id: filters.categoryId }),
    ...(filters.available !== undefined && { available: filters.available }),
    ...(filters.featured !== undefined && { featured: filters.featured })
  });
  
  const response = await fetch(
    `http://localhost:8000/api/v1/products/?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  return await response.json();
}

// Usage
searchProducts('burger', {
  page: 1,
  pageSize: 10,
  available: true,
  featured: true
});
```

#### Create Product

```javascript
async function createProduct(productData) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://localhost:8000/api/v1/products/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(productData)
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create product');
  }
  
  return await response.json();
}

// Usage
createProduct({
  name: 'Deluxe Burger',
  slug: 'deluxe-burger',
  description: 'Premium beef burger with special sauce',
  price: 1800, // $18.00
  cost: 1000,  // $10.00
  category_id: 'burgers-category-uuid',
  stock: 50,
  available: true
});
```

#### Update Product

```javascript
async function updateProduct(productId, updates) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(
    `http://localhost:8000/api/v1/products/${productId}`,
    {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updates)
    }
  );
  
  return await response.json();
}

// Usage - Update price and availability
updateProduct('product-uuid', {
  price: 2000,
  available: true
});
```

---

### Python (Requests)

#### Get All Products

```python
import requests

def get_products(token, page=1, page_size=10):
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    params = {
        'page': page,
        'page_size': page_size
    }
    
    response = requests.get(
        'http://localhost:8000/api/v1/products/',
        headers=headers,
        params=params
    )
    
    response.raise_for_status()
    return response.json()

# Usage
try:
    result = get_products(access_token, page=1, page_size=20)
    products = result['data']
    pagination = result['pagination']
    
    print(f"Total products: {pagination['total_items']}")
    for product in products:
        print(f"- {product['name']}: ${product['price']/100:.2f}")
except requests.exceptions.HTTPError as e:
    print(f"Error: {e}")
```

#### Search and Filter

```python
def search_products(token, query, category_id=None, available=None):
    headers = {'Authorization': f'Bearer {token}'}
    
    params = {'search': query}
    if category_id:
        params['category_id'] = category_id
    if available is not None:
        params['available'] = available
    
    response = requests.get(
        'http://localhost:8000/api/v1/products/',
        headers=headers,
        params=params
    )
    
    return response.json()

# Usage
results = search_products(
    token=access_token,
    query='burger',
    available=True
)
```

#### Create Product

```python
def create_product(token, product_data):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        'http://localhost:8000/api/v1/products/',
        headers=headers,
        json=product_data
    )
    
    response.raise_for_status()
    return response.json()

# Usage
new_product = create_product(access_token, {
    'name': 'Caesar Salad',
    'slug': 'caesar-salad',
    'description': 'Fresh romaine with parmesan',
    'price': 1200,  # $12.00
    'cost': 600,    # $6.00
    'category_id': 'salads-category-uuid',
    'stock': 30,
    'available': True
})
```

---

### cURL Examples

#### List Products

```bash
# Get first page (10 items)
curl -X GET "http://localhost:8000/api/v1/products/?page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  | python3 -m json.tool

# Get second page (20 items)
curl -X GET "http://localhost:8000/api/v1/products/?page=2&page_size=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Filter by Category

```bash
curl -X GET "http://localhost:8000/api/v1/products/?category_id=CATEGORY_UUID&available=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Search Products

```bash
curl -X GET "http://localhost:8000/api/v1/products/?search=burger&page=1&page_size=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Get Single Product

```bash
curl -X GET "http://localhost:8000/api/v1/products/PRODUCT_UUID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Create Product

```bash
curl -X POST "http://localhost:8000/api/v1/products/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Spicy Chicken Wings",
    "slug": "spicy-chicken-wings",
    "description": "Hot and crispy wings",
    "price": 1400,
    "cost": 800,
    "category_id": "CATEGORY_UUID",
    "stock": 40,
    "available": true,
    "department": "kitchen",
    "preparation_time": 25
  }'
```

#### Update Product

```bash
curl -X PUT "http://localhost:8000/api/v1/products/PRODUCT_UUID" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "price": 1600,
    "available": true,
    "stock": 50
  }'
```

#### Delete Product

```bash
curl -X DELETE "http://localhost:8000/api/v1/products/PRODUCT_UUID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Pagination Guide

### Understanding Pagination Response

```javascript
{
  "pagination": {
    "page": 1,           // Current page number
    "page_size": 10,     // Items per page
    "total_items": 29,   // Total products in database
    "total_pages": 3,    // Total pages available
    "has_next": true,    // More pages available
    "has_previous": false // Previous page available
  }
}
```

### Building a Paginator

```javascript
class ProductPaginator {
  constructor(token) {
    this.token = token;
    this.currentPage = 1;
    this.pageSize = 10;
  }
  
  async fetchPage(page) {
    const response = await fetch(
      `http://localhost:8000/api/v1/products/?page=${page}&page_size=${this.pageSize}`,
      {
        headers: { 'Authorization': `Bearer ${this.token}` }
      }
    );
    
    const result = await response.json();
    this.currentPage = result.pagination.page;
    return result;
  }
  
  async nextPage() {
    return await this.fetchPage(this.currentPage + 1);
  }
  
  async previousPage() {
    if (this.currentPage > 1) {
      return await this.fetchPage(this.currentPage - 1);
    }
  }
  
  async firstPage() {
    return await this.fetchPage(1);
  }
  
  async lastPage(totalPages) {
    return await this.fetchPage(totalPages);
  }
}

// Usage
const paginator = new ProductPaginator(token);
const firstPage = await paginator.firstPage();
const nextPage = await paginator.nextPage();
```

---

## Price Handling

Prices are stored and returned in **cents** to avoid floating-point precision issues.

### Converting Prices

```javascript
// Display price (cents to dollars)
function formatPrice(priceInCents) {
  return `$${(priceInCents / 100).toFixed(2)}`;
}

console.log(formatPrice(1250)); // "$12.50"

// Submit price (dollars to cents)
function toCents(dollars) {
  return Math.round(dollars * 100);
}

const priceInCents = toCents(15.99); // 1599
```

### Python Price Conversion

```python
def format_price(price_in_cents):
    """Convert cents to dollar string"""
    return f"${price_in_cents / 100:.2f}"

def to_cents(dollars):
    """Convert dollars to cents"""
    return round(dollars * 100)

# Usage
print(format_price(1250))  # "$12.50"
price_in_cents = to_cents(15.99)  # 1599
```

---

## Error Handling

### Common Errors

#### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```
**Solution**: Token expired or invalid. Login again.

#### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```
**Solution**: User doesn't have required role (admin/manager).

#### 404 Not Found
```json
{
  "detail": "Product not found"
}
```
**Solution**: Invalid product ID or product deleted.

#### 422 Validation Error
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
**Solution**: Missing or invalid field in request body.

### Error Handling Example

```javascript
async function getProductsSafely(page = 1) {
  const token = localStorage.getItem('access_token');
  
  if (!token) {
    throw new Error('Not authenticated. Please login.');
  }
  
  try {
    const response = await fetch(
      `http://localhost:8000/api/v1/products/?page=${page}&page_size=10`,
      {
        headers: { 'Authorization': `Bearer ${token}` }
      }
    );
    
    if (response.status === 401) {
      // Token expired - redirect to login
      localStorage.removeItem('access_token');
      window.location.href = '/login';
      return;
    }
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch products');
    }
    
    return await response.json();
    
  } catch (error) {
    console.error('Error fetching products:', error);
    throw error;
  }
}
```

---

## Sample Data Available

After seeding, 29 products are available across 8 categories:

- **Appetizers**: Spring Rolls, Garlic Bread, Buffalo Wings
- **Main Course**: Grilled Chicken, Beef Steak, Fish & Chips
- **Burgers**: Classic, Cheese, Chicken, Veggie
- **Pizza**: Margherita, Pepperoni, BBQ Chicken, Vegetarian
- **Pasta**: Carbonara, Alfredo, Arrabiata
- **Desserts**: Chocolate Cake, Cheesecake, Ice Cream Sundae, Tiramisu
- **Beverages**: Coca Cola, Orange Juice, Iced Tea, Mineral Water
- **Coffee**: Espresso, Cappuccino, Latte, Americano

---

## Best Practices

### 1. Cache Products Locally
```javascript
class ProductCache {
  constructor() {
    this.cache = new Map();
    this.cacheTime = 5 * 60 * 1000; // 5 minutes
  }
  
  set(key, data) {
    this.cache.set(key, {
      data: data,
      timestamp: Date.now()
    });
  }
  
  get(key) {
    const cached = this.cache.get(key);
    if (!cached) return null;
    
    const age = Date.now() - cached.timestamp;
    if (age > this.cacheTime) {
      this.cache.delete(key);
      return null;
    }
    
    return cached.data;
  }
}
```

### 2. Handle Token Expiration
```javascript
async function fetchWithAuth(url, options = {}) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (response.status === 401) {
    // Token expired - redirect to login
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  
  return response;
}
```

### 3. Implement Loading States
```javascript
async function loadProducts(page = 1) {
  setLoading(true);
  setError(null);
  
  try {
    const result = await getProducts(page);
    setProducts(result.data);
    setPagination(result.pagination);
  } catch (error) {
    setError(error.message);
  } finally {
    setLoading(false);
  }
}
```

### 4. Debounce Search Queries
```javascript
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

const searchProducts = debounce(async (query) => {
  const results = await fetch(
    `http://localhost:8000/api/v1/products/?search=${query}`,
    { headers: { 'Authorization': `Bearer ${token}` } }
  );
  // Update UI with results
}, 300); // Wait 300ms after user stops typing
```

---

## Testing

### Quick Test Commands

```bash
# Store token
TOKEN="your-access-token-here"

# Test list products
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/products/?page=1&page_size=5"

# Test search
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/products/?search=burger"

# Test filters
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/products/?available=true&featured=true"
```

---

## Related Documentation

- [Login API Documentation](LOGIN_API_DOCUMENTATION.md)
- [Complete API Reference](API_REFERENCE.md)
- [All Endpoints List](API_ENDPOINTS_LIST.md)
- [Quick Start Guide](QUICK_REFERENCE.md)

---

## Support

For issues or questions:
1. Check authentication token is valid
2. Verify request format and required fields
3. Review error response messages
4. Check API server logs for details

---

## Summary

✅ **Authentication**: Bearer token required  
✅ **Pagination**: All list endpoints support pagination  
✅ **Filtering**: Search, category, availability, price range  
✅ **CRUD**: Full create, read, update, delete operations  
✅ **Price Format**: All prices in cents  
✅ **Sample Data**: 29 products across 8 categories available  
✅ **Error Handling**: Comprehensive error responses  

**Ready to integrate!** Start with the examples above or open the interactive API docs at http://localhost:8000/docs
