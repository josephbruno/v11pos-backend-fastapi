# 🍔 Products API - Quick Integration Guide

## ✅ System Status

- **API Server**: http://localhost:8000
- **Total Products**: 29 items across 8 categories
- **Authentication**: Bearer token required
- **Pagination**: Supported on all list endpoints
- **Filters**: Search, category, availability, featured, price range

---

## 🚀 Quick Start

### 1. Get Your Token

```bash
# Login to get access token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -d "username=admin@restaurant.com&password=Admin123!"
```

### 2. List Products

```bash
curl "http://localhost:8000/api/v1/products/?page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Search Products

```bash
curl "http://localhost:8000/api/v1/products/?search=burger" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📡 API Endpoints Summary

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/products/` | List all products (paginated) | ✅ |
| GET | `/api/v1/products/{id}` | Get single product | ✅ |
| POST | `/api/v1/products/` | Create product | ✅ Admin/Manager |
| PUT | `/api/v1/products/{id}` | Update product | ✅ Admin/Manager |
| DELETE | `/api/v1/products/{id}` | Delete product | ✅ Admin/Manager |

---

## 🔍 Query Parameters

### Pagination
- `page` (default: 1) - Page number
- `page_size` (default: 10, max: 100) - Items per page

### Filters
- `search` - Search in name/description
- `category_id` - Filter by category UUID
- `available` - Filter by availability (true/false)
- `featured` - Filter featured products (true/false)
- `min_price` - Minimum price in cents
- `max_price` - Maximum price in cents

---

## 📦 Response Format

```json
{
  "status": "success",
  "message": "Products retrieved successfully",
  "data": [
    {
      "id": "product-uuid",
      "name": "Buffalo Wings",
      "slug": "buffalo-wings",
      "description": "Spicy chicken wings",
      "price": 1250,
      "cost": 750,
      "category_id": "category-uuid",
      "stock": 100,
      "min_stock": 5,
      "available": true,
      "featured": false,
      "department": "kitchen",
      "preparation_time": 15
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

---

## 💻 Integration Examples

### JavaScript (Fetch)

```javascript
// Get products with pagination
async function getProducts(page = 1, pageSize = 10) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(
    `http://localhost:8000/api/v1/products/?page=${page}&page_size=${pageSize}`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  
  return await response.json();
}

// Search products
async function searchProducts(query) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(
    `http://localhost:8000/api/v1/products/?search=${query}`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  
  return await response.json();
}

// Usage
const result = await getProducts(1, 10);
console.log(`Found ${result.pagination.total_items} products`);
```

### Python

```python
import requests

def get_products(token, page=1, page_size=10):
    headers = {'Authorization': f'Bearer {token}'}
    params = {'page': page, 'page_size': page_size}
    
    response = requests.get(
        'http://localhost:8000/api/v1/products/',
        headers=headers,
        params=params
    )
    
    return response.json()

# Usage
result = get_products(access_token, page=1, page_size=20)
print(f"Total products: {result['pagination']['total_items']}")
```

---

## 💰 Price Handling

**Important**: All prices are in **cents** (not dollars).

```javascript
// Display price
function formatPrice(priceInCents) {
  return `$${(priceInCents / 100).toFixed(2)}`;
}

formatPrice(1250); // "$12.50"

// Submit price
function toCents(dollars) {
  return Math.round(dollars * 100);
}

toCents(15.99); // 1599
```

---

## 🧪 Test Tools

### 1. Interactive HTML Page
```
Open: products_test.html
```
Features:
- ✅ Visual product cards
- ✅ Search and filters
- ✅ Pagination controls
- ✅ Real-time API responses

### 2. Postman Collection
```
Import: postman_products_collection.json
```
Includes:
- ✅ 11 pre-configured requests
- ✅ List, search, filter examples
- ✅ CRUD operations
- ✅ Combined filters

### 3. cURL Commands
```bash
# List products
curl "http://localhost:8000/api/v1/products/" \
  -H "Authorization: Bearer TOKEN"

# Search
curl "http://localhost:8000/api/v1/products/?search=burger" \
  -H "Authorization: Bearer TOKEN"

# Filter available + featured
curl "http://localhost:8000/api/v1/products/?available=true&featured=true" \
  -H "Authorization: Bearer TOKEN"
```

---

## 📊 Sample Data

29 products available across 8 categories:

| Category | Count | Examples |
|----------|-------|----------|
| Appetizers | 3 | Spring Rolls, Garlic Bread, Buffalo Wings |
| Main Course | 3 | Grilled Chicken, Beef Steak, Fish & Chips |
| Burgers | 4 | Classic, Cheese, Chicken, Veggie |
| Pizza | 4 | Margherita, Pepperoni, BBQ Chicken |
| Pasta | 3 | Carbonara, Alfredo, Arrabiata |
| Desserts | 4 | Chocolate Cake, Cheesecake, Ice Cream |
| Beverages | 4 | Coca Cola, Orange Juice, Iced Tea |
| Coffee | 4 | Espresso, Cappuccino, Latte, Americano |

---

## 🎯 Common Use Cases

### 1. Display Product Menu
```javascript
async function loadMenu() {
  const result = await getProducts(1, 50);
  
  result.data.forEach(product => {
    displayProductCard({
      name: product.name,
      price: formatPrice(product.price),
      description: product.description,
      available: product.available
    });
  });
}
```

### 2. Search with Autocomplete
```javascript
const debounce = (func, wait) => {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

const searchInput = document.getElementById('search');
searchInput.addEventListener('input', debounce(async (e) => {
  const results = await searchProducts(e.target.value);
  updateSearchResults(results.data);
}, 300));
```

### 3. Paginated Product List
```javascript
class ProductPaginator {
  constructor(token) {
    this.token = token;
    this.currentPage = 1;
  }
  
  async fetchPage(page) {
    const response = await fetch(
      `http://localhost:8000/api/v1/products/?page=${page}&page_size=10`,
      { headers: { 'Authorization': `Bearer ${this.token}` } }
    );
    
    const result = await response.json();
    this.currentPage = page;
    return result;
  }
  
  async nextPage() {
    return await this.fetchPage(this.currentPage + 1);
  }
  
  async previousPage() {
    return await this.fetchPage(this.currentPage - 1);
  }
}
```

### 4. Filter by Category
```javascript
async function getProductsByCategory(categoryId) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(
    `http://localhost:8000/api/v1/products/?category_id=${categoryId}&available=true`,
    { headers: { 'Authorization': `Bearer ${token}` } }
  );
  
  return await response.json();
}
```

---

## ⚠️ Error Handling

### Common Errors

| Status | Error | Solution |
|--------|-------|----------|
| 401 | Could not validate credentials | Token expired - login again |
| 403 | Not enough permissions | Admin/Manager role required |
| 404 | Product not found | Invalid product ID |
| 422 | Validation error | Check required fields |

### Error Handling Example

```javascript
async function getProductsSafely(page = 1) {
  const token = localStorage.getItem('access_token');
  
  if (!token) {
    throw new Error('Please login first');
  }
  
  try {
    const response = await fetch(
      `http://localhost:8000/api/v1/products/?page=${page}`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    
    if (response.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
      return;
    }
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Request failed');
    }
    
    return await response.json();
    
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}
```

---

## 🔐 Security Best Practices

1. **Store tokens securely**
   - Use `localStorage` for web apps
   - Use secure storage for mobile apps
   - Never expose tokens in URLs

2. **Handle token expiration**
   - Tokens expire after 24 hours
   - Redirect to login on 401 errors
   - Implement automatic token refresh

3. **Validate user input**
   - Sanitize search queries
   - Validate price ranges
   - Check pagination bounds

4. **Rate limiting**
   - Implement client-side caching
   - Debounce search queries
   - Don't make excessive requests

---

## 📚 Full Documentation

- **[PRODUCTS_API_DOCUMENTATION.md](PRODUCTS_API_DOCUMENTATION.md)** - Complete API guide with detailed examples
- **[LOGIN_API_DOCUMENTATION.md](LOGIN_API_DOCUMENTATION.md)** - Authentication guide
- **[API_REFERENCE.md](API_REFERENCE.md)** - All API endpoints
- **[API_ENDPOINTS_LIST.md](API_ENDPOINTS_LIST.md)** - Endpoint reference

---

## ✅ Testing Checklist

- [x] Login and get access token
- [x] List products with pagination
- [x] Search products by name
- [x] Filter by availability
- [x] Filter by featured status
- [x] Filter by price range
- [x] Get single product details
- [x] Navigate through pages
- [x] Handle authentication errors
- [x] Handle validation errors

---

## 🎊 Quick Test

```bash
# 1. Login
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -d "username=admin@restaurant.com&password=Admin123!" \
  | python3 -c "import sys, json; print(json.loads(sys.stdin.read())['access_token'])")

# 2. Get products
curl -s "http://localhost:8000/api/v1/products/?page=1&page_size=5" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# 3. Search burgers
curl -s "http://localhost:8000/api/v1/products/?search=burger" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

## 🆘 Troubleshooting

### "Could not validate credentials"
- Token expired (24 hours) - login again
- Token not included in Authorization header
- Invalid token format

### "Not enough permissions"
- Only admin/manager can create/update/delete
- Check user role in token

### No results returned
- Check if products exist in database
- Verify filters are correct
- Try without filters first

### Pagination not working
- Ensure page >= 1
- Ensure page_size between 1-100
- Check total_pages in response

---

## 🎯 Next Steps

1. **Test the API**
   - Open `products_test.html` in browser
   - Import Postman collection
   - Try cURL examples

2. **Integrate in your app**
   - Copy code examples
   - Implement error handling
   - Add loading states

3. **Explore related APIs**
   - Categories API for product categories
   - Orders API for order management
   - Customers API for customer data

---

## 📞 Support

**Test Server**: http://localhost:8000  
**API Docs**: http://localhost:8000/docs  
**Sample Data**: 29 products seeded and ready

✅ **Ready to integrate!** All tools and documentation are complete.
