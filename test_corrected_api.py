"""
Corrected API Testing Script with proper schemas
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json"}

# Test credentials
ADMIN = {"email": "admin@pos.com", "password": "admin123"}
admin_token = None

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
        print(f"✅ Admin Login: {response.status_code}")
        return True
    print(f"❌ Admin Login: {response.status_code}")
    return False

def test_get_categories():
    """Get available categories"""
    if not admin_token:
        print("❌ No token available")
        return None
    
    headers = {**HEADERS, "Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BASE_URL}/categories", headers=headers)
    
    if response.status_code == 200:
        categories = response.json()
        if categories:
            cat_id = categories[0].get('id')
            print(f"✅ Got categories: {len(categories)} available")
            print(f"   First category ID: {cat_id}")
            return cat_id
        else:
            print("⚠️  No categories found, need to create one first")
            return None
    print(f"❌ Get categories: {response.status_code} - {response.text}")
    return None

def test_create_product(category_id):
    """Create product with correct schema"""
    if not admin_token or not category_id:
        print("❌ Missing token or category ID")
        return None
    
    product_data = {
        "name": "Test Pizza",
        "description": "Delicious test pizza",
        "price": 300,  # Integer, not float
        "category_id": category_id,
        "sku": "PIZZA001",
        "slug": "test-pizza",  # Required field
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
        print(f"✅ Create product: {response.status_code}")
        print(f"   Product ID: {product_id}")
        print(f"   Name: {product.get('name')}")
        return product_id
    print(f"❌ Create product: {response.status_code}")
    print(f"   Error: {response.text}")
    return None

def test_create_order(product_id):
    """Create order with correct schema"""
    if not admin_token or not product_id:
        print("❌ Missing token or product ID")
        return None
    
    order_data = {
        "customer_name": "Test Customer",
        "customer_email": "customer@example.com",
        "customer_phone": "9876543210",
        "items": [
            {
                "product_id": product_id,
                "product_name": "Test Pizza",
                "quantity": 2,
                "unit_price": 300,  # Required field
                "special_instructions": "No onions"
            }
        ],
        "order_type": "dine_in",  # Lowercase enum value
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
        print(f"✅ Create order: {response.status_code}")
        print(f"   Order ID: {order.get('id')}")
        print(f"   Total: {order.get('total')}")
        print(f"   Status: {order.get('status')}")
        return order.get('id')
    print(f"❌ Create order: {response.status_code}")
    print(f"   Error: {response.text}")
    return None

def main():
    print("\n" + "="*70)
    print("  CORRECTED API TESTS")
    print("="*70 + "\n")
    
    # Step 1: Login
    if not test_admin_login():
        return
    
    # Step 2: Get categories
    category_id = test_get_categories()
    if not category_id:
        print("⚠️  Creating new category first...")
        return
    
    # Step 3: Create product
    product_id = test_create_product(category_id)
    if not product_id:
        print("❌ Failed to create product, cannot proceed to order test")
        return
    
    # Step 4: Create order
    order_id = test_create_order(product_id)
    
    print("\n" + "="*70)
    if order_id:
        print("  ✅ ALL TESTS PASSED")
    else:
        print("  ⚠️  Some tests failed - check schema requirements above")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
