"""
Quick API Test Script - Tests all modules with sample data
"""
import requests
import json
from datetime import datetime, date, timedelta

BASE_URL = "http://localhost:8000/api/v1"

# Test results tracking
results = {
    "passed": 0,
    "failed": 0,
    "tests": []
}

def test_endpoint(name, method, url, data=None, headers=None, params=None):
    """Test an endpoint and record result"""
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, params=params)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, params=params)
        elif method == "PATCH":
            response = requests.patch(url, json=data, headers=headers, params=params)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, params=params)
        
        success = response.status_code < 400
        icon = "✅" if success else "❌"
        
        print(f"{icon} {name}: {response.status_code}")
        
        if success:
            results["passed"] += 1
            try:
                resp_data = response.json()
                if isinstance(resp_data, dict) and 'data' in resp_data:
                    results["tests"].append({
                        "name": name,
                        "status": "PASSED",
                        "data": resp_data['data']
                    })
                    return resp_data['data']
                else:
                    results["tests"].append({
                        "name": name,
                        "status": "PASSED",
                        "data": resp_data
                    })
                    return resp_data
            except:
                return response.text
        else:
            results["failed"] += 1
            print(f"   Error: {response.text[:200]}")
            results["tests"].append({
                "name": name,
                "status": "FAILED",
                "error": response.text
            })
            return None
            
    except Exception as e:
        results["failed"] += 1
        print(f"❌ {name}: Exception - {str(e)}")
        results["tests"].append({
            "name": name,
            "status": "ERROR",
            "error": str(e)
        })
        return None

print("\n" + "="*80)
print("🚀 POS SYSTEM - COMPREHENSIVE API TESTING")
print("="*80)
print(f"Base URL: {BASE_URL}")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# ============= 1. HEALTH CHECK =============
print("\n📍 1. HEALTH CHECK")
test_endpoint("Health Check", "GET", "http://localhost:8000/health")
test_endpoint("Root Endpoint", "GET", "http://localhost:8000/")

# ============= 2. USER & AUTH =============
print("\n📍 2. USER & AUTH MODULE")

# Create admin user
admin_data = {
    "email": "admin@postest.com",
    "username": "adminuser",
    "password": "Admin@123456",
    "full_name": "Admin User",
    "role": "admin"
}
admin_user = test_endpoint("Create Admin User", "POST", f"{BASE_URL}/users", data=admin_data)

# Login admin
login_data = {"email": "admin@postest.com", "password": "Admin@123456"}
token_response = test_endpoint("Login Admin", "POST", f"{BASE_URL}/auth/login", data=login_data)

if token_response:
    token = token_response.get('access_token')
    headers = {"Authorization": f"Bearer {token}"}
    print(f"   🔑 Token: {token[:50]}...")
    
    # Get current user
    test_endpoint("Get Current User", "GET", f"{BASE_URL}/users/me", headers=headers)
    
    # ============= 3. RESTAURANT =============
    print("\n📍 3. RESTAURANT MODULE")
    
    restaurant_data = {
        "name": "The Grand Dine",
        "slug": f"the-grand-dine-{int(datetime.now().timestamp())}",
        "business_name": "Grand Dine Pvt Ltd",
        "business_type": "fine_dining",
        "cuisine_type": ["italian", "continental", "indian"],
        "description": "Premium fine dining restaurant",
        "email": "contact@granddine.com",
        "phone": "+91-9876543200",
        "alternate_phone": "+91-9876543201",
        "address": "123, MG Road, Brigade Gateway",
        "city": "Bangalore",
        "state": "Karnataka",
        "country": "India",
        "postal_code": "560001",
        "gstin": "29ABCDE1234F1Z5",
        "fssai_license": "12345678901234",
        "pan_number": "ABCDE1234F",
        "enable_gst": True,
        "cgst_rate": 2.5,
        "sgst_rate": 2.5,
        "service_charge_percentage": 10.0
    }
    restaurant = test_endpoint("Create Restaurant", "POST", f"{BASE_URL}/restaurants", data=restaurant_data, headers=headers)
    
    if restaurant:
        restaurant_id = restaurant.get('id')
        print(f"   🏪 Restaurant ID: {restaurant_id}")
        
        # Get restaurant
        test_endpoint("Get Restaurant", "GET", f"{BASE_URL}/restaurants/{restaurant_id}", headers=headers)
        
        # List restaurants
        test_endpoint("List Restaurants", "GET", f"{BASE_URL}/restaurants", headers=headers)
        
        # ============= 4. STAFF & ROLES =============
        print("\n📍 4. STAFF & ROLE MANAGEMENT")
        
        # Create role
        role_data = {
            "name": "Restaurant Manager",
            "code": "manager",
            "description": "Full restaurant management access",
            "level": 8,
            "permissions": ["create_order", "view_order", "create_staff", "view_staff", "approve_leave"]
        }
        role = test_endpoint("Create Manager Role", "POST", f"{BASE_URL}/staff/roles?restaurant_id={restaurant_id}", data=role_data, headers=headers)
        
        if role:
            role_id = role.get('id')
            
            # Create staff
            staff_data = {
                "role_id": role_id,
                "employee_code": f"EMP{int(datetime.now().timestamp())}",
                "first_name": "Rajesh",
                "last_name": "Kumar",
                "email": "rajesh.kumar@granddine.com",
                "phone": "+91-9876543220",
                "address_line1": "456, Koramangala",
                "city": "Bangalore",
                "state": "Karnataka",
                "postal_code": "560095",
                "date_of_joining": "2024-01-01",
                "employment_type": "full_time",
                "department": "Operations",
                "designation": "Floor Manager",
                "basic_salary": 45000.00,
                "allowances": 5000.00,
                "default_shift_type": "morning",
                "working_days_per_week": 6
            }
            staff = test_endpoint("Create Staff Member", "POST", f"{BASE_URL}/staff/members?restaurant_id={restaurant_id}", data=staff_data, headers=headers)
            
            # List staff
            test_endpoint("List Staff", "GET", f"{BASE_URL}/staff/members/restaurant/{restaurant_id}", headers=headers)
            
            if staff:
                staff_id = staff.get('id')
                
                # Create shift
                shift_data = {
                    "staff_id": staff_id,
                    "shift_date": (date.today() + timedelta(days=1)).isoformat(),
                    "shift_type": "morning",
                    "start_time": "09:00:00",
                    "end_time": "17:00:00",
                    "break_duration_minutes": 60
                }
                shift = test_endpoint("Create Shift", "POST", f"{BASE_URL}/staff/shifts?restaurant_id={restaurant_id}", data=shift_data, headers=headers)
                
                # Get leave balance
                test_endpoint("Get Leave Balance", "GET", f"{BASE_URL}/staff/leave-balance/{staff_id}", headers=headers)
        
        # ============= 5. CUSTOMERS =============
        print("\n📍 5. CUSTOMER MODULE")
        
        customer_data = {
            "name": "Amit Verma",
            "email": f"amit{int(datetime.now().timestamp())}@gmail.com",
            "phone": "+91-9876543230",
            "address": "101, Whitefield, Bangalore",
            "city": "Bangalore",
            "state": "Karnataka",
            "postal_code": "560066",
            "tags": ["vip", "regular"]
        }
        customer = test_endpoint("Create Customer", "POST", f"{BASE_URL}/customers?restaurant_id={restaurant_id}", data=customer_data, headers=headers)
        
        # List customers
        test_endpoint("List Customers", "GET", f"{BASE_URL}/customers/restaurant/{restaurant_id}", headers=headers, params={"restaurant_id": restaurant_id})
        
        # ============= 6. TABLES =============
        print("\n📍 6. TABLE MANAGEMENT")
        
        table_data = {
            "table_number": f"T{int(datetime.now().timestamp() % 1000)}",
            "table_name": "Window Table 1",
            "capacity": 4,
            "floor": "Ground Floor",
            "section": "Window Section",
            "shape": "square",
            "is_active": True
        }
        table = test_endpoint("Create Table", "POST", f"{BASE_URL}/tables?restaurant_id={restaurant_id}", data=table_data, headers=headers)
        
        # List tables
        test_endpoint("List Tables", "GET", f"{BASE_URL}/tables/restaurant/{restaurant_id}", headers=headers)
        
        # ============= 7. PRODUCTS =============
        print("\n📍 7. PRODUCT MODULE")
        
        # Create category
        category_data = {
            "name": "Main Course",
            "description": "Primary dishes",
            "display_order": 1,
            "is_active": True
        }
        category = test_endpoint("Create Category", "POST", f"{BASE_URL}/products/categories?restaurant_id={restaurant_id}", data=category_data, headers=headers)
        
        if category:
            category_id = category.get('id')
            
            # Create product
            product_data = {
                "category_id": category_id,
                "name": "Butter Chicken",
                "description": "Tender chicken in rich tomato-butter gravy",
                "price": 45000,
                "cost_price": 20000,
                "sku": f"BC{int(datetime.now().timestamp())}",
                "is_vegetarian": False,
                "spice_level": "medium",
                "preparation_time": 25,
                "is_available": True,
                "is_featured": True
            }
            product = test_endpoint("Create Product", "POST", f"{BASE_URL}/products?restaurant_id={restaurant_id}", data=product_data, headers=headers)
            
            # List products
            test_endpoint("List Products", "GET", f"{BASE_URL}/products/restaurant/{restaurant_id}", headers=headers)
        
        # ============= 8. INVENTORY =============
        print("\n📍 8. INVENTORY MODULE")
        
        # Create supplier
        supplier_data = {
            "name": "Fresh Farm Suppliers",
            "code": f"SUP{int(datetime.now().timestamp())}",
            "contact_person": "Ramesh Patel",
            "email": f"ramesh{int(datetime.now().timestamp())}@freshfarm.com",
            "phone": "+91-9876543240",
            "address": "Plot 45, APMC Market",
            "city": "Bangalore",
            "state": "Karnataka",
            "payment_terms_days": 30,
            "credit_limit": 50000000
        }
        supplier = test_endpoint("Create Supplier", "POST", f"{BASE_URL}/inventory/suppliers?restaurant_id={restaurant_id}", data=supplier_data, headers=headers)
        
        if supplier:
            supplier_id = supplier.get('id')
            
            # Create ingredient
            ingredient_data = {
                "name": "Chicken Breast",
                "category": "Meat",
                "unit_of_measure": "kg",
                "current_stock": 50.0,
                "minimum_stock": 10.0,
                "reorder_level": 20.0,
                "cost_price": 35000,
                "supplier_id": supplier_id,
                "sku": f"ING{int(datetime.now().timestamp())}",
                "is_perishable": True,
                "low_stock_alert_enabled": True
            }
            ingredient = test_endpoint("Create Ingredient", "POST", f"{BASE_URL}/inventory/ingredients?restaurant_id={restaurant_id}", data=ingredient_data, headers=headers)
            
            # List ingredients
            test_endpoint("List Ingredients", "GET", f"{BASE_URL}/inventory/ingredients/restaurant/{restaurant_id}", headers=headers)
            
            # Get low stock alerts
            test_endpoint("Get Low Stock Alerts", "GET", f"{BASE_URL}/inventory/alerts/low-stock/restaurant/{restaurant_id}", headers=headers)
        
        # ============= 9. ORDERS =============
        print("\n📍 9. ORDER MODULE")
        
        if product and table and customer:
            order_data = {
                "order_type": "dine_in",
                "table_id": table.get('id'),
                "customer_id": customer.get('id'),
                "customer_name": "Amit Verma",
                "customer_phone": "+91-9876543230",
                "items": [
                    {
                        "product_id": product.get('id'),
                        "quantity": 2,
                        "unit_price": 45000
                    }
                ]
            }
            order = test_endpoint("Create Order", "POST", f"{BASE_URL}/orders?restaurant_id={restaurant_id}", data=order_data, headers=headers)
            
            # List orders
            test_endpoint("List Orders", "GET", f"{BASE_URL}/orders/restaurant/{restaurant_id}", headers=headers)
        
        # ============= 10. KDS =============
        print("\n📍 10. KITCHEN DISPLAY SYSTEM")
        
        # Create kitchen station
        station_data = {
            "name": "Main Kitchen",
            "code": f"MAIN{int(datetime.now().timestamp())}",
            "type": "hot_kitchen",
            "description": "Primary cooking station",
            "is_active": True,
            "display_order": 1
        }
        station = test_endpoint("Create Kitchen Station", "POST", f"{BASE_URL}/kds/stations?restaurant_id={restaurant_id}", data=station_data, headers=headers)
        
        # List KDS displays
        test_endpoint("List KDS Displays", "GET", f"{BASE_URL}/kds/displays/restaurant/{restaurant_id}", headers=headers, params={"status": "pending"})

# ============= SUMMARY =============
print("\n" + "="*80)
print("📊 TEST SUMMARY")
print("="*80)
print(f"✅ Passed: {results['passed']}")
print(f"❌ Failed: {results['failed']}")
print(f"📈 Total: {results['passed'] + results['failed']}")
print(f"📊 Success Rate: {(results['passed']/(results['passed']+results['failed'])*100):.1f}%")
print(f"\n⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Save results
with open('test_results.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)
print(f"\n💾 Results saved to: test_results.json")

print("\n" + "="*80)
