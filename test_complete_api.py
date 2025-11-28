"""
Comprehensive API Testing Script
Tests all major endpoints including authentication, products, orders, etc.
"""
import requests
import json
from typing import Dict, Any

# Base configuration
BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json"}

# Test data
TEST_USER = {
    "name": "Test User",
    "email": "testuser@pos.com",
    "phone": "9999999999",
    "password": "Test@12345",
    "role": "staff"
}

ADMIN_USER = {
    "email": "admin@pos.com",
    "password": "admin123"
}

# Global token storage
auth_token = None
admin_token = None


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def print_test(test_name: str, passed: bool, details: str = ""):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {test_name}")
    if details:
        print(f"       {details}")


def test_registration():
    """Test user registration"""
    global auth_token
    print_section("TEST 1: USER REGISTRATION")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            headers=HEADERS,
            json=TEST_USER,
            timeout=10
        )
        
        success = response.status_code == 201
        print_test("Register new user", success, f"Status: {response.status_code}")
        
        if success:
            data = response.json()
            auth_token = data.get("access_token")
            print(f"       Token: {auth_token[:30]}...")
            print(f"       User ID: {data.get('user', {}).get('id')}")
            return True
        else:
            print(f"       Error: {response.text}")
            return False
    except Exception as e:
        print_test("Register new user", False, str(e))
        return False


def test_admin_login():
    """Test admin login"""
    global admin_token
    print_section("TEST 2: ADMIN LOGIN")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login/json",
            headers=HEADERS,
            json=ADMIN_USER,
            timeout=10
        )
        
        success = response.status_code == 200
        print_test("Admin login", success, f"Status: {response.status_code}")
        
        if success:
            data = response.json()
            admin_token = data.get("access_token")
            print(f"       Token: {admin_token[:30]}...")
            print(f"       User: {data.get('user', {}).get('name')}")
            return True
        else:
            print(f"       Error: {response.text}")
            return False
    except Exception as e:
        print_test("Admin login", False, str(e))
        return False


def test_get_current_user():
    """Test getting current user info"""
    print_section("TEST 3: GET CURRENT USER")
    
    if not auth_token:
        print_test("Get current user", False, "No auth token available")
        return False
    
    try:
        headers = {**HEADERS, "Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/auth/me",
            headers=headers,
            timeout=10
        )
        
        success = response.status_code == 200
        print_test("Get current user info", success, f"Status: {response.status_code}")
        
        if success:
            data = response.json()
            print(f"       Name: {data.get('name')}")
            print(f"       Email: {data.get('email')}")
            print(f"       Role: {data.get('role')}")
            return True
        else:
            print(f"       Error: {response.text}")
            return False
    except Exception as e:
        print_test("Get current user info", False, str(e))
        return False


def test_create_product():
    """Test creating a product"""
    print_section("TEST 4: CREATE PRODUCT")
    
    if not admin_token:
        print_test("Create product", False, "No admin token available")
        return False
    
    product_data = {
        "name": "Test Pizza",
        "description": "Delicious test pizza",
        "price": 299.99,
        "category_id": "7e2f5c87-1a2b-4d5e-8f9a-1b2c3d4e5f6g",
        "sku": "PIZZA001",
        "image_url": "https://example.com/pizza.jpg"
    }
    
    try:
        headers = {**HEADERS, "Authorization": f"Bearer {admin_token}"}
        response = requests.post(
            f"{BASE_URL}/products",
            headers=headers,
            json=product_data,
            timeout=10
        )
        
        success = response.status_code in [200, 201]
        print_test("Create product", success, f"Status: {response.status_code}")
        
        if success:
            data = response.json()
            print(f"       Product ID: {data.get('id')}")
            print(f"       Name: {data.get('name')}")
            print(f"       Price: {data.get('price')}")
            return data.get('id')
        else:
            print(f"       Error: {response.text}")
            return None
    except Exception as e:
        print_test("Create product", False, str(e))
        return None


def test_get_products():
    """Test getting products list"""
    print_section("TEST 5: GET PRODUCTS")
    
    if not admin_token:
        print_test("Get products", False, "No admin token available")
        return False
    
    try:
        headers = {**HEADERS, "Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/products",
            headers=headers,
            timeout=10
        )
        
        success = response.status_code == 200
        print_test("Get products list", success, f"Status: {response.status_code}")
        
        if success:
            data = response.json()
            count = len(data) if isinstance(data, list) else data.get('total', 0)
            print(f"       Total products: {count}")
            return True
        else:
            print(f"       Error: {response.text}")
            return False
    except Exception as e:
        print_test("Get products list", False, str(e))
        return False


def test_create_order():
    """Test creating an order"""
    print_section("TEST 6: CREATE ORDER")
    
    if not auth_token:
        print_test("Create order", False, "No auth token available")
        return False
    
    order_data = {
        "customer_name": "Test Customer",
        "customer_email": "customer@example.com",
        "customer_phone": "9876543210",
        "items": [
            {
                "product_id": "7e2f5c87-1a2b-4d5e-8f9a-1b2c3d4e5f6g",
                "quantity": 2,
                "price": 299.99,
                "special_instructions": "No onions"
            }
        ],
        "order_type": "DINE_IN",
        "table_number": "5"
    }
    
    try:
        headers = {**HEADERS, "Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/orders",
            headers=headers,
            json=order_data,
            timeout=10
        )
        
        success = response.status_code in [200, 201]
        print_test("Create order", success, f"Status: {response.status_code}")
        
        if success:
            data = response.json()
            print(f"       Order ID: {data.get('id')}")
            print(f"       Total: {data.get('total')}")
            print(f"       Status: {data.get('status')}")
            return data.get('id')
        else:
            print(f"       Error: {response.text}")
            return None
    except Exception as e:
        print_test("Create order", False, str(e))
        return None


def test_get_orders():
    """Test getting orders list"""
    print_section("TEST 7: GET ORDERS")
    
    if not auth_token:
        print_test("Get orders", False, "No auth token available")
        return False
    
    try:
        headers = {**HEADERS, "Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/orders",
            headers=headers,
            timeout=10
        )
        
        success = response.status_code == 200
        print_test("Get orders list", success, f"Status: {response.status_code}")
        
        if success:
            data = response.json()
            count = len(data) if isinstance(data, list) else data.get('total', 0)
            print(f"       Total orders: {count}")
            return True
        else:
            print(f"       Error: {response.text}")
            return False
    except Exception as e:
        print_test("Get orders list", False, str(e))
        return False


def test_health_check():
    """Test API health"""
    print_section("TEST 0: API HEALTH CHECK")
    
    try:
        response = requests.get(
            f"{BASE_URL}/../health",
            timeout=10
        )
        
        success = response.status_code == 200
        print_test("API is running", success, f"Status: {response.status_code}")
        return success
    except Exception as e:
        print_test("API is running", False, str(e))
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  RESTAURANTPOS API COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    results = []
    
    # Run tests in order
    results.append(("Health Check", test_health_check()))
    results.append(("Registration", test_registration()))
    results.append(("Admin Login", test_admin_login()))
    results.append(("Get Current User", test_get_current_user()))
    results.append(("Create Product", test_create_product() is not None))
    results.append(("Get Products", test_get_products()))
    results.append(("Create Order", test_create_order() is not None))
    results.append(("Get Orders", test_get_orders()))
    
    # Print summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    print(f"\n{'='*70}")
    print(f"  Results: {passed}/{total} tests passed")
    print(f"{'='*70}\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
