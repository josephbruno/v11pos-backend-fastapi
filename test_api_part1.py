"""
Comprehensive API Testing Script for POS System
Tests all endpoints with complete sample data
"""
import requests
import json
from datetime import datetime, date, timedelta
import time

# Base URL
BASE_URL = "http://localhost:8000"

# Test data storage
test_data = {
    "tokens": {},
    "users": {},
    "restaurants": {},
    "roles": {},
    "staff": {},
    "customers": {},
    "tables": {},
    "categories": {},
    "products": {},
    "suppliers": {},
    "ingredients": {},
    "recipes": {},
    "purchase_orders": {},
    "kitchen_stations": {},
    "orders": {},
    "shifts": {},
    "attendance": {},
    "leave_applications": {}
}

def print_section(title):
    """Print section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_test(endpoint, method="GET"):
    """Print test info"""
    print(f"\n🧪 Testing: {method} {endpoint}")

def print_result(response, show_data=True):
    """Print test result"""
    status_icon = "✅" if response.status_code < 400 else "❌"
    print(f"{status_icon} Status: {response.status_code}")
    
    if show_data and response.status_code < 400:
        try:
            data = response.json()
            if isinstance(data, dict) and 'data' in data:
                print(f"📦 Data: {json.dumps(data['data'], indent=2, default=str)[:500]}...")
            else:
                print(f"📦 Response: {json.dumps(data, indent=2, default=str)[:500]}...")
        except:
            print(f"📦 Response: {response.text[:500]}")
    elif response.status_code >= 400:
        print(f"❌ Error: {response.text[:500]}")

def get_headers(token=None):
    """Get request headers"""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


# ============================================================================
# 1. AUTHENTICATION & USER TESTS
# ============================================================================

def test_auth_endpoints():
    print_section("1. AUTHENTICATION & USER MODULE")
    
    # 1.1 Register Admin User
    print_test("/auth/register", "POST")
    admin_data = {
        "email": "admin@postest.com",
        "password": "Admin@123456",
        "full_name": "Admin User",
        "phone": "+91-9876543210",
        "role": "admin",
        "is_active": True
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=admin_data)
    print_result(response)
    if response.status_code < 400:
        user_data = response.json().get('data', {})
        test_data['users']['admin'] = user_data
    
    time.sleep(1)
    
    # 1.2 Login Admin
    print_test("/auth/login", "POST")
    login_data = {
        "email": "admin@postest.com",
        "password": "Admin@123456"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print_result(response)
    if response.status_code < 400:
        token_data = response.json().get('data', {})
        test_data['tokens']['admin'] = token_data.get('access_token')
        print(f"🔑 Admin Token: {test_data['tokens']['admin'][:50]}...")
    
    # 1.3 Get Current User
    print_test("/auth/me", "GET")
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers=get_headers(test_data['tokens']['admin'])
    )
    print_result(response)
    
    # 1.4 Register Manager User
    print_test("/auth/register (Manager)", "POST")
    manager_data = {
        "email": "manager@postest.com",
        "password": "Manager@123456",
        "full_name": "Manager User",
        "phone": "+91-9876543211",
        "role": "manager",
        "is_active": True
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=manager_data)
    print_result(response)
    if response.status_code < 400:
        test_data['users']['manager'] = response.json().get('data', {})
    
    # 1.5 Login Manager
    print_test("/auth/login (Manager)", "POST")
    login_data = {
        "email": "manager@postest.com",
        "password": "Manager@123456"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print_result(response)
    if response.status_code < 400:
        test_data['tokens']['manager'] = response.json().get('data', {}).get('access_token')


# ============================================================================
# 2. RESTAURANT TESTS
# ============================================================================

def test_restaurant_endpoints():
    print_section("2. RESTAURANT MODULE")
    
    # 2.1 Create Restaurant
    print_test("/restaurants", "POST")
    restaurant_data = {
        "name": "The Grand Dine",
        "slug": "the-grand-dine",
        "business_name": "Grand Dine Pvt Ltd",
        "business_type": "fine_dining",
        "cuisine_type": ["italian", "continental", "indian"],
        "description": "Premium fine dining restaurant with multi-cuisine menu",
        "email": "contact@granddine.com",
        "phone": "+91-9876543200",
        "alternate_phone": "+91-9876543201",
        "address": "123, MG Road, Brigade Gateway",
        "city": "Bangalore",
        "state": "Karnataka",
        "country": "India",
        "postal_code": "560001",
        "latitude": "12.9716",
        "longitude": "77.5946",
        "gstin": "29ABCDE1234F1Z5",
        "fssai_license": "12345678901234",
        "pan_number": "ABCDE1234F",
        "primary_color": "#2C3E50",
        "accent_color": "#E74C3C",
        "timezone": "Asia/Kolkata",
        "currency": "INR",
        "language": "en",
        "enable_gst": True,
        "cgst_rate": 2.5,
        "sgst_rate": 2.5,
        "service_charge_percentage": 10.0
    }
    response = requests.post(
        f"{BASE_URL}/restaurants",
        json=restaurant_data,
        headers=get_headers(test_data['tokens']['admin'])
    )
    print_result(response)
    if response.status_code < 400:
        test_data['restaurants']['main'] = response.json().get('data', {})
        print(f"🏪 Restaurant ID: {test_data['restaurants']['main'].get('id')}")
    
    # 2.2 Get Restaurant by ID
    if test_data['restaurants'].get('main'):
        restaurant_id = test_data['restaurants']['main']['id']
        print_test(f"/restaurants/{restaurant_id}", "GET")
        response = requests.get(
            f"{BASE_URL}/restaurants/{restaurant_id}",
            headers=get_headers(test_data['tokens']['admin'])
        )
        print_result(response)
    
    # 2.3 List Restaurants
    print_test("/restaurants", "GET")
    response = requests.get(
        f"{BASE_URL}/restaurants?skip=0&limit=10",
        headers=get_headers(test_data['tokens']['admin'])
    )
    print_result(response)
    
    # 2.4 Update Restaurant
    if test_data['restaurants'].get('main'):
        restaurant_id = test_data['restaurants']['main']['id']
        print_test(f"/restaurants/{restaurant_id}", "PUT")
        update_data = {
            "description": "Premium fine dining restaurant - Updated",
            "service_charge_percentage": 12.0
        }
        response = requests.put(
            f"{BASE_URL}/restaurants/{restaurant_id}",
            json=update_data,
            headers=get_headers(test_data['tokens']['admin'])
        )
        print_result(response)


# ============================================================================
# 3. STAFF & ROLE TESTS
# ============================================================================

def test_staff_endpoints():
    print_section("3. STAFF & ROLE MANAGEMENT MODULE")
    
    if not test_data['restaurants'].get('main'):
        print("⚠️ Skipping - No restaurant created")
        return
    
    restaurant_id = test_data['restaurants']['main']['id']
    
    # 3.1 Create Manager Role
    print_test("/staff/roles", "POST")
    role_data = {
        "name": "Restaurant Manager",
        "code": "manager",
        "description": "Full restaurant management access",
        "level": 8,
        "permissions": [
            "create_order", "view_order", "update_order", "cancel_order",
            "create_staff", "view_staff", "update_staff",
            "approve_leave", "view_reports", "manage_payment"
        ]
    }
    response = requests.post(
        f"{BASE_URL}/staff/roles?restaurant_id={restaurant_id}",
        json=role_data,
        headers=get_headers(test_data['tokens']['admin'])
    )
    print_result(response)
    if response.status_code < 400:
        test_data['roles']['manager'] = response.json().get('data', {})
    
    # 3.2 Create Cashier Role
    print_test("/staff/roles (Cashier)", "POST")
    cashier_role = {
        "name": "Cashier",
        "code": "cashier",
        "description": "POS operations only",
        "level": 4,
        "permissions": ["create_order", "view_order", "manage_payment"]
    }
    response = requests.post(
        f"{BASE_URL}/staff/roles?restaurant_id={restaurant_id}",
        json=cashier_role,
        headers=get_headers(test_data['tokens']['admin'])
    )
    print_result(response)
    if response.status_code < 400:
        test_data['roles']['cashier'] = response.json().get('data', {})
    
    # 3.3 List Roles
    print_test(f"/staff/roles/restaurant/{restaurant_id}", "GET")
    response = requests.get(
        f"{BASE_URL}/staff/roles/restaurant/{restaurant_id}",
        headers=get_headers(test_data['tokens']['admin'])
    )
    print_result(response)
    
    # 3.4 Create Staff Member
    if test_data['roles'].get('manager'):
        print_test("/staff/members", "POST")
        staff_data = {
            "role_id": test_data['roles']['manager']['id'],
            "employee_code": "EMP001",
            "first_name": "Rajesh",
            "last_name": "Kumar",
            "email": "rajesh.kumar@granddine.com",
            "phone": "+91-9876543220",
            "alternate_phone": "+91-9876543221",
            "address_line1": "456, Koramangala",
            "address_line2": "5th Block",
            "city": "Bangalore",
            "state": "Karnataka",
            "postal_code": "560095",
            "country": "India",
            "emergency_contact_name": "Priya Kumar",
            "emergency_contact_phone": "+91-9876543222",
            "emergency_contact_relation": "Spouse",
            "date_of_joining": "2024-01-01",
            "employment_type": "full_time",
            "department": "Operations",
            "designation": "Floor Manager",
            "basic_salary": 45000.00,
            "allowances": 5000.00,
            "aadhar_number": "123456789012",
            "pan_number": "ABCDE1234F",
            "bank_account_number": "1234567890",
            "bank_name": "HDFC Bank",
            "bank_ifsc_code": "HDFC0001234",
            "default_shift_type": "morning",
            "working_days_per_week": 6,
            "notes": "Experienced manager with 5 years in hospitality"
        }
        response = requests.post(
            f"{BASE_URL}/staff/members?restaurant_id={restaurant_id}",
            json=staff_data,
            headers=get_headers(test_data['tokens']['admin'])
        )
        print_result(response)
        if response.status_code < 400:
            test_data['staff']['manager'] = response.json().get('data', {})
    
    # 3.5 Create Cashier Staff
    if test_data['roles'].get('cashier'):
        print_test("/staff/members (Cashier)", "POST")
        cashier_data = {
            "role_id": test_data['roles']['cashier']['id'],
            "employee_code": "EMP002",
            "first_name": "Priya",
            "last_name": "Sharma",
            "email": "priya.sharma@granddine.com",
            "phone": "+91-9876543223",
            "address_line1": "789, Indiranagar",
            "city": "Bangalore",
            "state": "Karnataka",
            "postal_code": "560038",
            "date_of_joining": "2024-02-01",
            "employment_type": "full_time",
            "department": "Billing",
            "designation": "Senior Cashier",
            "basic_salary": 30000.00,
            "allowances": 3000.00,
            "default_shift_type": "afternoon",
            "working_days_per_week": 6
        }
        response = requests.post(
            f"{BASE_URL}/staff/members?restaurant_id={restaurant_id}",
            json=cashier_data,
            headers=get_headers(test_data['tokens']['admin'])
        )
        print_result(response)
        if response.status_code < 400:
            test_data['staff']['cashier'] = response.json().get('data', {})
    
    # 3.6 List Staff
    print_test(f"/staff/members/restaurant/{restaurant_id}", "GET")
    response = requests.get(
        f"{BASE_URL}/staff/members/restaurant/{restaurant_id}?skip=0&limit=10",
        headers=get_headers(test_data['tokens']['admin'])
    )
    print_result(response)
    
    # 3.7 Create Shift
    if test_data['staff'].get('manager'):
        print_test("/staff/shifts", "POST")
        shift_data = {
            "staff_id": test_data['staff']['manager']['id'],
            "shift_date": (date.today() + timedelta(days=1)).isoformat(),
            "shift_type": "morning",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
            "break_duration_minutes": 60,
            "notes": "Opening shift - handle morning setup"
        }
        response = requests.post(
            f"{BASE_URL}/staff/shifts?restaurant_id={restaurant_id}",
            json=shift_data,
            headers=get_headers(test_data['tokens']['admin'])
        )
        print_result(response)
        if response.status_code < 400:
            test_data['shifts']['morning'] = response.json().get('data', {})
    
    # 3.8 Check-in Attendance
    if test_data['staff'].get('manager') and test_data['shifts'].get('morning'):
        print_test("/staff/attendance/check-in", "POST")
        checkin_data = {
            "staff_id": test_data['staff']['manager']['id'],
            "shift_id": test_data['shifts']['morning']['id'],
            "check_in_location": "Main Entrance",
            "remarks": "On time"
        }
        response = requests.post(
            f"{BASE_URL}/staff/attendance/check-in?restaurant_id={restaurant_id}",
            json=checkin_data,
            headers=get_headers(test_data['tokens']['admin'])
        )
        print_result(response)
        if response.status_code < 400:
            test_data['attendance']['manager'] = response.json().get('data', {})
    
    # 3.9 Create Leave Application
    if test_data['staff'].get('cashier'):
        print_test("/staff/leave-applications", "POST")
        leave_data = {
            "staff_id": test_data['staff']['cashier']['id'],
            "leave_type": "casual_leave",
            "start_date": (date.today() + timedelta(days=7)).isoformat(),
            "end_date": (date.today() + timedelta(days=9)).isoformat(),
            "is_half_day": False,
            "reason": "Family function - wedding ceremony in hometown",
            "contact_number": "+91-9876543223"
        }
        response = requests.post(
            f"{BASE_URL}/staff/leave-applications?restaurant_id={restaurant_id}",
            json=leave_data,
            headers=get_headers(test_data['tokens']['admin'])
        )
        print_result(response)
        if response.status_code < 400:
            test_data['leave_applications']['cashier'] = response.json().get('data', {})
    
    # 3.10 Get Leave Balance
    if test_data['staff'].get('cashier'):
        staff_id = test_data['staff']['cashier']['id']
        print_test(f"/staff/leave-balance/{staff_id}", "GET")
        response = requests.get(
            f"{BASE_URL}/staff/leave-balance/{staff_id}",
            headers=get_headers(test_data['tokens']['admin'])
        )
        print_result(response)


# ============================================================================
# 4. CUSTOMER TESTS
# ============================================================================

def test_customer_endpoints():
    print_section("4. CUSTOMER MODULE")
    
    if not test_data['restaurants'].get('main'):
        print("⚠️ Skipping - No restaurant created")
        return
    
    restaurant_id = test_data['restaurants']['main']['id']
    
    # 4.1 Create Customer
    print_test("/customers", "POST")
    customer_data = {
        "name": "Amit Verma",
        "email": "amit.verma@gmail.com",
        "phone": "+91-9876543230",
        "address": "101, Whitefield, Bangalore",
        "city": "Bangalore",
        "state": "Karnataka",
        "postal_code": "560066",
        "date_of_birth": "1990-05-15",
        "anniversary_date": "2015-12-20",
        "notes": "VIP customer - prefers window seating",
        "tags": ["vip", "regular", "corporate"]
    }
    response = requests.post(
        f"{BASE_URL}/customers?restaurant_id={restaurant_id}",
        json=customer_data,
        headers=get_headers(test_data['tokens']['admin'])
    )
    print_result(response)
    if response.status_code < 400:
        test_data['customers']['vip'] = response.json().get('data', {})
    
    # 4.2 Create Regular Customer
    print_test("/customers (Regular)", "POST")
    regular_customer = {
        "name": "Sneha Reddy",
        "email": "sneha.reddy@yahoo.com",
        "phone": "+91-9876543231",
        "address": "202, HSR Layout, Bangalore",
        "city": "Bangalore",
        "state": "Karnataka",
        "postal_code": "560102",
        "notes": "Vegetarian preferences",
        "tags": ["regular", "vegetarian"]
    }
    response = requests.post(
        f"{BASE_URL}/customers?restaurant_id={restaurant_id}",
        json=regular_customer,
        headers=get_headers(test_data['tokens']['admin'])
    )
    print_result(response)
    if response.status_code < 400:
        test_data['customers']['regular'] = response.json().get('data', {})
    
    # 4.3 List Customers
    print_test(f"/customers/restaurant/{restaurant_id}", "GET")
    response = requests.get(
        f"{BASE_URL}/customers/restaurant/{restaurant_id}?skip=0&limit=10",
        headers=get_headers(test_data['tokens']['admin'])
    )
    print_result(response)
    
    # 4.4 Search Customers
    print_test("/customers/restaurant/{restaurant_id}?search=amit", "GET")
    response = requests.get(
        f"{BASE_URL}/customers/restaurant/{restaurant_id}?search=amit",
        headers=get_headers(test_data['tokens']['admin'])
    )
    print_result(response)


# ============================================================================
# 5. TABLE TESTS
# ============================================================================

def test_table_endpoints():
    print_section("5. TABLE MANAGEMENT MODULE")
    
    if not test_data['restaurants'].get('main'):
        print("⚠️ Skipping - No restaurant created")
        return
    
    restaurant_id = test_data['restaurants']['main']['id']
    
    # 5.1 Create Tables
    tables_to_create = [
        {
            "table_number": "T001",
            "table_name": "Window Table 1",
            "capacity": 4,
            "floor": "Ground Floor",
            "section": "Window Section",
            "position_x": 100,
            "position_y": 100,
            "shape": "square",
            "is_active": True
        },
        {
            "table_number": "T002",
            "table_name": "VIP Booth",
            "capacity": 6,
            "floor": "First Floor",
            "section": "VIP Section",
            "position_x": 200,
            "position_y": 150,
            "shape": "rectangle",
            "is_active": True,
            "notes": "Premium booth with privacy curtain"
        },
        {
            "table_number": "T003",
            "table_name": "Corner Table",
            "capacity": 2,
            "floor": "Ground Floor",
            "section": "Couple Section",
            "position_x": 300,
            "position_y": 200,
            "shape": "round",
            "is_active": True
        }
    ]
    
    for idx, table_data in enumerate(tables_to_create):
        print_test(f"/tables (Table {idx+1})", "POST")
        response = requests.post(
            f"{BASE_URL}/tables?restaurant_id={restaurant_id}",
            json=table_data,
            headers=get_headers(test_data['tokens']['admin'])
        )
        print_result(response, show_data=False)
        if response.status_code < 400:
            test_data['tables'][table_data['table_number']] = response.json().get('data', {})
    
    # 5.2 List Tables
    print_test(f"/tables/restaurant/{restaurant_id}", "GET")
    response = requests.get(
        f"{BASE_URL}/tables/restaurant/{restaurant_id}",
        headers=get_headers(test_data['tokens']['admin'])
    )
    print_result(response)
    
    # 5.3 Update Table Status (Occupy)
    if test_data['tables'].get('T001'):
        table_id = test_data['tables']['T001']['id']
        print_test(f"/tables/{table_id}/status", "PATCH")
        response = requests.patch(
            f"{BASE_URL}/tables/{table_id}/status?status=occupied",
            headers=get_headers(test_data['tokens']['admin'])
        )
        print_result(response)


# ============================================================================
# Main Execution
# ============================================================================

def main():
    print("\n" + "🚀"*40)
    print("  COMPREHENSIVE POS SYSTEM API TESTING")
    print("🚀"*40)
    print(f"\n📍 Base URL: {BASE_URL}")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test each module
        test_auth_endpoints()
        test_restaurant_endpoints()
        test_staff_endpoints()
        test_customer_endpoints()
        test_table_endpoints()
        
        print_section("TEST SUMMARY")
        print(f"✅ Tests completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n📊 Test Data Created:")
        print(f"   - Users: {len(test_data['users'])}")
        print(f"   - Restaurants: {len(test_data['restaurants'])}")
        print(f"   - Roles: {len(test_data['roles'])}")
        print(f"   - Staff: {len(test_data['staff'])}")
        print(f"   - Customers: {len(test_data['customers'])}")
        print(f"   - Tables: {len(test_data['tables'])}")
        
        # Save test data
        with open('test_data.json', 'w') as f:
            json.dump(test_data, f, indent=2, default=str)
        print(f"\n💾 Test data saved to: test_data.json")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Testing interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
