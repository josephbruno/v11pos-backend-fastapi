"""
Comprehensive API Testing Script
Tests all endpoints with SuperAdmin authentication
"""
import requests
import json
from datetime import datetime
import os

# Configuration
BASE_URL = "http://localhost:8000"
SUPERADMIN_EMAIL = "admin@platform.com"
SUPERADMIN_PASSWORD = "admin123"

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

class APITester:
    def __init__(self):
        self.token = None
        self.restaurant_id = None
        self.test_results = []
        self.created_ids = {}
        
    def print_header(self, text):
        """Print section header"""
        print(f"\n{'=' * 60}")
        print(f"{Colors.BLUE}{text}{Colors.RESET}")
        print(f"{'=' * 60}\n")
    
    def print_success(self, text):
        """Print success message"""
        print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")
    
    def print_error(self, text):
        """Print error message"""
        print(f"{Colors.RED}✗ {text}{Colors.RESET}")
    
    def print_info(self, text):
        """Print info message"""
        print(f"{Colors.YELLOW}ℹ {text}{Colors.RESET}")
    
    def test_endpoint(self, method, endpoint, data=None, files=None, description=""):
        """Test an API endpoint"""
        url = f"{BASE_URL}{endpoint}"
        headers = {}
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                if files:
                    response = requests.post(url, headers=headers, files=files, data=data)
                else:
                    headers["Content-Type"] = "application/json"
                    response = requests.post(url, headers=headers, json=data)
            elif method == "PUT":
                headers["Content-Type"] = "application/json"
                response = requests.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                self.print_error(f"Unknown method: {method}")
                return None
            
            # Record result
            result = {
                "method": method,
                "endpoint": endpoint,
                "status": response.status_code,
                "success": 200 <= response.status_code < 300,
                "description": description
            }
            self.test_results.append(result)
            
            # Print result
            if result["success"]:
                self.print_success(f"{method} {endpoint} - {response.status_code}")
                if description:
                    print(f"  {description}")
            else:
                self.print_error(f"{method} {endpoint} - {response.status_code}")
                if description:
                    print(f"  {description}")
                try:
                    error_detail = response.json()
                    print(f"  Error: {error_detail}")
                except:
                    print(f"  Error: {response.text[:200]}")
            
            return response
            
        except requests.exceptions.ConnectionError:
            self.print_error(f"Connection failed to {url}")
            self.print_info("Make sure the server is running: uvicorn app.main:app --reload")
            return None
        except Exception as e:
            self.print_error(f"Error testing {endpoint}: {str(e)}")
            return None
    
    def login_superadmin(self):
        """Login as SuperAdmin"""
        self.print_header("1. SUPERADMIN LOGIN")
        
        response = self.test_endpoint(
            "POST",
            "/api/v1/auth/login/json",
            data={
                "email": SUPERADMIN_EMAIL,
                "password": SUPERADMIN_PASSWORD
            },
            description="Login as SuperAdmin"
        )
        
        if response and response.status_code == 200:
            data = response.json()
            if data.get("success"):
                self.token = data["data"]["access_token"]
                self.print_success(f"SuperAdmin logged in successfully!")
                self.print_info(f"Token: {self.token[:50]}...")
                return True
        
        self.print_error("SuperAdmin login failed!")
        return False
    
    def test_onboarding(self):
        """Test restaurant onboarding"""
        self.print_header("2. RESTAURANT ONBOARDING")
        
        # Register a test restaurant
        response = self.test_endpoint(
            "POST",
            "/api/v1/onboarding/register",
            data={
                "restaurant_name": "Test Restaurant",
                "business_type": "restaurant",
                "cuisine_type": ["italian", "american"],
                "owner_name": "Test Owner",
                "owner_email": f"owner{datetime.now().timestamp()}@test.com",
                "owner_phone": "1234567890",
                "password": "password123",
                "address": "123 Test St",
                "city": "New York",
                "state": "NY",
                "country": "USA",
                "postal_code": "10001",
                "timezone": "America/New_York",
                "currency": "USD",
                "language": "en"
            },
            description="Register new restaurant"
        )
        
        if response and response.status_code == 201:
            data = response.json()
            if data.get("success"):
                self.restaurant_id = data["data"]["restaurant"]["id"]
                self.created_ids["restaurant"] = self.restaurant_id
                self.print_success(f"Restaurant created: {self.restaurant_id}")
    
    def test_categories(self):
        """Test category endpoints"""
        self.print_header("3. CATEGORY MANAGEMENT")
        
        if not self.restaurant_id:
            self.print_error("No restaurant ID available")
            return
        
        # Create category
        response = self.test_endpoint(
            "POST",
            "/api/v1/categories",
            data={
                "name": "Appetizers",
                "description": "Starter dishes",
                "display_order": 1,
                "active": True
            },
            description="Create category"
        )
        
        if response and response.status_code in [200, 201]:
            try:
                data = response.json()
                if data.get("success") and data.get("data"):
                    category_id = data["data"].get("id")
                    if category_id:
                        self.created_ids["category"] = category_id
                        self.print_success(f"Category created: {category_id}")
            except:
                pass
        
        # List categories
        self.test_endpoint(
            "GET",
            "/api/v1/categories",
            description="List all categories"
        )
    
    def test_products(self):
        """Test product endpoints"""
        self.print_header("4. PRODUCT MANAGEMENT")
        
        # Create product
        product_data = {
            "name": "Margherita Pizza",
            "description": "Classic Italian pizza with tomato and mozzarella",
            "price": 1299,  # $12.99 in cents
            "category_id": self.created_ids.get("category"),
            "available": True,
            "featured": True,
            "vegetarian": True,
            "vegan": False,
            "spicy_level": 0
        }
        
        response = self.test_endpoint(
            "POST",
            "/api/v1/products",
            data=product_data,
            description="Create product"
        )
        
        if response and response.status_code in [200, 201]:
            try:
                data = response.json()
                if data.get("success") and data.get("data"):
                    product_id = data["data"].get("id")
                    if product_id:
                        self.created_ids["product"] = product_id
                        self.print_success(f"Product created: {product_id}")
            except:
                pass
        
        # List products
        self.test_endpoint(
            "GET",
            "/api/v1/products",
            description="List all products"
        )
    
    def test_customers(self):
        """Test customer endpoints"""
        self.print_header("5. CUSTOMER MANAGEMENT")
        
        # Create customer
        response = self.test_endpoint(
            "POST",
            "/api/v1/customers",
            data={
                "name": "John Doe",
                "email": f"customer{datetime.now().timestamp()}@test.com",
                "phone": "5551234567",
                "address": "456 Customer Ave",
                "city": "Boston",
                "state": "MA",
                "postal_code": "02101"
            },
            description="Create customer"
        )
        
        if response and response.status_code in [200, 201]:
            try:
                data = response.json()
                if data.get("success") and data.get("data"):
                    customer_id = data["data"].get("id")
                    if customer_id:
                        self.created_ids["customer"] = customer_id
                        self.print_success(f"Customer created: {customer_id}")
            except:
                pass
        
        # List customers
        self.test_endpoint(
            "GET",
            "/api/v1/customers",
            description="List all customers"
        )
    
    def test_orders(self):
        """Test order endpoints"""
        self.print_header("6. ORDER MANAGEMENT")
        
        # Create order
        order_data = {
            "customer_id": self.created_ids.get("customer"),
            "order_type": "dine_in",
            "table_number": "5",
            "items": [
                {
                    "product_id": self.created_ids.get("product"),
                    "quantity": 2,
                    "price": 1299,
                    "notes": "Extra cheese"
                }
            ],
            "subtotal": 2598,
            "tax": 260,
            "total": 2858,
            "payment_method": "cash",
            "payment_status": "pending"
        }
        
        response = self.test_endpoint(
            "POST",
            "/api/v1/orders",
            data=order_data,
            description="Create order"
        )
        
        if response and response.status_code in [200, 201]:
            try:
                data = response.json()
                if data.get("success") and data.get("data"):
                    order_id = data["data"].get("id")
                    if order_id:
                        self.created_ids["order"] = order_id
                        self.print_success(f"Order created: {order_id}")
            except:
                pass
        
        # List orders
        self.test_endpoint(
            "GET",
            "/api/v1/orders",
            description="List all orders"
        )
    
    def test_users(self):
        """Test user endpoints"""
        self.print_header("7. USER MANAGEMENT")
        
        # List users
        self.test_endpoint(
            "GET",
            "/api/v1/users",
            description="List all users"
        )
        
        # Get current user
        self.test_endpoint(
            "GET",
            "/api/v1/auth/me",
            description="Get current user info"
        )
    
    def test_analytics(self):
        """Test analytics endpoints"""
        self.print_header("8. ANALYTICS & DASHBOARD")
        
        # Dashboard stats
        self.test_endpoint(
            "GET",
            "/api/v1/dashboard/stats",
            description="Get dashboard statistics"
        )
        
        # Analytics
        self.test_endpoint(
            "GET",
            "/api/v1/analytics/sales",
            description="Get sales analytics"
        )
    
    def test_qr_ordering(self):
        """Test QR ordering endpoints"""
        self.print_header("9. QR ORDERING")
        
        # Create QR table
        response = self.test_endpoint(
            "POST",
            "/api/v1/qr/tables",
            data={
                "table_number": "10",
                "capacity": 4,
                "location": "Main Hall",
                "active": True
            },
            description="Create QR table"
        )
        
        # List QR tables
        self.test_endpoint(
            "GET",
            "/api/v1/qr/tables",
            description="List QR tables"
        )
    
    def test_loyalty(self):
        """Test loyalty program endpoints"""
        self.print_header("10. LOYALTY PROGRAM")
        
        # Create loyalty rule
        self.test_endpoint(
            "POST",
            "/api/v1/loyalty/rules",
            data={
                "name": "Points per Dollar",
                "description": "Earn 1 point per dollar spent",
                "points_per_dollar": 1,
                "active": True
            },
            description="Create loyalty rule"
        )
        
        # List loyalty rules
        self.test_endpoint(
            "GET",
            "/api/v1/loyalty/rules",
            description="List loyalty rules"
        )
    
    def test_modifiers(self):
        """Test modifier endpoints"""
        self.print_header("11. PRODUCT MODIFIERS")
        
        # Create modifier
        response = self.test_endpoint(
            "POST",
            "/api/v1/modifiers",
            data={
                "name": "Size",
                "type": "single",
                "required": True,
                "options": [
                    {"name": "Small", "price": 0},
                    {"name": "Medium", "price": 200},
                    {"name": "Large", "price": 400}
                ]
            },
            description="Create modifier"
        )
        
        # List modifiers
        self.test_endpoint(
            "GET",
            "/api/v1/modifiers",
            description="List modifiers"
        )
    
    def test_tax_settings(self):
        """Test tax settings endpoints"""
        self.print_header("12. TAX SETTINGS")
        
        # Create tax rule
        self.test_endpoint(
            "POST",
            "/api/v1/tax-settings",
            data={
                "name": "Sales Tax",
                "type": "percentage",
                "percentage": 850,  # 8.5%
                "applicable_on": "all",
                "active": True
            },
            description="Create tax rule"
        )
        
        # List tax rules
        self.test_endpoint(
            "GET",
            "/api/v1/tax-settings",
            description="List tax rules"
        )
    
    def test_translations(self):
        """Test translation endpoints"""
        self.print_header("13. TRANSLATIONS")
        
        # Create translation
        self.test_endpoint(
            "POST",
            "/api/v1/translations",
            data={
                "entity_type": "product",
                "entity_id": self.created_ids.get("product"),
                "field_name": "name",
                "language": "es",
                "translated_value": "Pizza Margherita"
            },
            description="Create translation"
        )
        
        # List translations
        self.test_endpoint(
            "GET",
            "/api/v1/translations",
            description="List translations"
        )
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = total - passed
        
        print(f"Total Tests: {total}")
        self.print_success(f"Passed: {passed}")
        if failed > 0:
            self.print_error(f"Failed: {failed}")
        
        print(f"\n{'=' * 60}")
        print("FAILED TESTS:")
        print(f"{'=' * 60}\n")
        
        for result in self.test_results:
            if not result["success"]:
                print(f"{Colors.RED}✗ {result['method']} {result['endpoint']} - {result['status']}{Colors.RESET}")
                if result["description"]:
                    print(f"  {result['description']}")
        
        print(f"\n{'=' * 60}")
        print("CREATED RESOURCES:")
        print(f"{'=' * 60}\n")
        
        for key, value in self.created_ids.items():
            print(f"{key}: {value}")
        
        print(f"\n{'=' * 60}\n")
        
        # Calculate success rate
        success_rate = (passed / total * 100) if total > 0 else 0
        
        if success_rate == 100:
            self.print_success(f"🎉 ALL TESTS PASSED! ({success_rate:.1f}%)")
        elif success_rate >= 80:
            self.print_info(f"✓ Most tests passed ({success_rate:.1f}%)")
        else:
            self.print_error(f"⚠ Many tests failed ({success_rate:.1f}%)")
    
    def run_all_tests(self):
        """Run all API tests"""
        print(f"\n{'=' * 60}")
        print(f"{Colors.BLUE}🚀 COMPREHENSIVE API TESTING{Colors.RESET}")
        print(f"{'=' * 60}")
        print(f"Base URL: {BASE_URL}")
        print(f"SuperAdmin: {SUPERADMIN_EMAIL}")
        print(f"{'=' * 60}\n")
        
        # Step 1: Login
        if not self.login_superadmin():
            self.print_error("Cannot proceed without SuperAdmin login")
            return
        
        # Step 2: Test onboarding
        self.test_onboarding()
        
        # Step 3-13: Test all endpoints
        self.test_categories()
        self.test_products()
        self.test_customers()
        self.test_orders()
        self.test_users()
        self.test_analytics()
        self.test_qr_ordering()
        self.test_loyalty()
        self.test_modifiers()
        self.test_tax_settings()
        self.test_translations()
        
        # Print summary
        self.print_summary()


def main():
    """Main function"""
    tester = APITester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
