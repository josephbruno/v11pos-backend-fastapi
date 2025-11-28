"""
Complete API test - creates category, product, and order
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json"}

ADMIN = {"email": "admin@pos.com", "password": "admin123"}
admin_token = None

def log(message, is_error=False):
    prefix = "❌" if is_error else "✅"
    print(f"{prefix} {message}")

def test_admin_login():
    """Login as admin"""
    global admin_token
    response = requests.post(
        f"{BASE_URL}/auth/login/json",
        headers=HEADERS,
        json=ADMIN
    )
    if response.status_code == 200:
        admin_token = response.json().get("access_token")
        log("Admin Login successful")
        return True
    log(f"Admin Login failed: {response.status_code}", True)
    return False

def test_get_or_create_category():
    """Get existing category or create a new one"""
    if not admin_token:
        log("No token available", True)
        return None
    
    headers = {**HEADERS, "Authorization": f"Bearer {admin_token}"}
    
    # First try to get existing categories
    list_response = requests.get(
        f"{BASE_URL}/categories",
        headers=headers
    )
    
    if list_response.status_code == 200:
        categories = list_response.json()
        if categories:
            cat_id = categories[0].get('id')
            log(f"Using existing category: {cat_id}")
            return cat_id
    
    # If no categories exist, create one with unique slug
    import uuid
    unique_slug = f"test-category-{str(uuid.uuid4())[:8]}"
    category_data = {
        "name": "Test Category",
        "slug": unique_slug,
        "description": "Test category for pizza",
        "active": True
    }
    
    response = requests.post(
        f"{BASE_URL}/categories",
        headers=headers,
        json=category_data
    )
    
    if response.status_code in [200, 201]:
        category = response.json()
        cat_id = category.get('id')
        log(f"Category created: {cat_id}")
        return cat_id
    log(f"Create category failed: {response.status_code} - {response.text}", True)
    return None

def test_create_product(category_id):
    """Create product with correct schema"""
    if not admin_token or not category_id:
        log("Missing token or category ID", True)
        return None
    
    product_data = {
        "name": "Margherita Pizza",
        "description": "Fresh tomato, basil, mozzarella",
        "price": 299,  # Integer
        "category_id": str(category_id),
        "sku": "PIZZA-MARG-001",
        "slug": "margherita-pizza",
        "is_available": True,
        "image_url": "https://example.com/pizza.jpg"
    }
    
    headers = {**HEADERS, "Authorization": f"Bearer {admin_token}"}
    response = requests.post(
        f"{BASE_URL}/products",
        headers=headers,
        json=product_data
    )
    
    if response.status_code in [200, 201]:
        product = response.json()
        product_id = product.get('id')
        log(f"Product created: {product_id} - {product.get('name')}")
        return product_id
    log(f"Create product failed: {response.status_code} - {response.text}", True)
    return None

def test_create_order(product_id):
    """Create order with correct schema"""
    if not admin_token or not product_id:
        log("Missing token or product ID", True)
        return None
    
    order_data = {
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "customer_phone": "9876543210",
        "items": [
            {
                "product_id": str(product_id),
                "product_name": "Margherita Pizza",
                "quantity": 2,
                "unit_price": 299
            }
        ],
        "order_type": "dine_in",
        "table_number": "5"
    }
    
    headers = {**HEADERS, "Authorization": f"Bearer {admin_token}"}
    response = requests.post(
        f"{BASE_URL}/orders",
        headers=headers,
        json=order_data
    )
    
    if response.status_code in [200, 201]:
        order = response.json()
        order_id = order.get('id')
        total = order.get('total')
        log(f"Order created: {order_id} - Total: ₹{total}")
        return order_id
    log(f"Create order failed: {response.status_code} - {response.text}", True)
    return None

def test_get_orders():
    """Get all orders"""
    if not admin_token:
        return False
    
    headers = {**HEADERS, "Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BASE_URL}/orders", headers=headers)
    
    if response.status_code == 200:
        orders = response.json()
        count = len(orders) if isinstance(orders, list) else 0
        log(f"Retrieved {count} orders")
        return True
    log(f"Get orders failed: {response.status_code}", True)
    return False

def main():
    print("\n" + "="*70)
    print("  FULL API WORKFLOW TEST")
    print("="*70 + "\n")
    
    # Step 1: Login
    if not test_admin_login():
        return
    
    # Step 2: Create category
    category_id = test_get_or_create_category()
    if not category_id:
        return
    
    # Step 3: Create product
    product_id = test_create_product(category_id)
    if not product_id:
        return
    
    # Step 4: Create order
    order_id = test_create_order(product_id)
    if not order_id:
        return
    
    # Step 5: Get all orders
    test_get_orders()
    
    print("\n" + "="*70)
    print("  ✅ ALL TESTS COMPLETED SUCCESSFULLY")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
