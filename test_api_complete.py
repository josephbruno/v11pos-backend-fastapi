#!/usr/bin/env python3
"""
POS System - Complete API Testing with Full Sample Data
Tests all API endpoints with all required and optional fields populated
"""

import requests
import json
from datetime import datetime, date, timedelta
import random
import string


BASE_URL = "http://localhost:8000/api/v1"
TOKEN = None
RESTAURANT_ID = None
HEADERS = {"Content-Type": "application/json"}


def log(message, level="INFO"):
    """Print formatted log message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")


def extract_data(response):
    """Extract data from standard response format"""
    if response is None:
        return None
    if isinstance(response, dict):
        if "data" in response:
            return response["data"]
        return response
    return response


def test_endpoint(name, method, url, data=None, params=None, expect_success=True):
    """Test an API endpoint and return response"""
    headers = HEADERS.copy()
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            log(f"❌ {name}: Unknown method {method}", "ERROR")
            return None
        
        # Success status codes
        success_codes = [200, 201, 204]
        is_success = response.status_code in success_codes
        
        status_icon = "✅" if is_success else "❌"
        log(f"{status_icon} {name}: {response.status_code}")
        
        if not is_success and expect_success:
            try:
                error_data = response.json()
                log(f"   Error: {json.dumps(error_data)[:200]}", "ERROR")
            except:
                log(f"   Error: {response.text[:200]}", "ERROR")
        
        if is_success and response.text:
            try:
                return response.json()
            except:
                return response.text
        
        return None
        
    except Exception as e:
        log(f"❌ {name}: Exception - {str(e)}", "ERROR")
        return None


def generate_code(prefix, length=6):
    """Generate random code"""
    return f"{prefix}{random.randint(10**(length-1), 10**length-1)}"


def main():
    global TOKEN, RESTAURANT_ID
    
    # Initialize all IDs that will be used across sections
    customer_id = None
    table_id = None
    category_id = None
    product_id = None
    supplier_id = None
    order_id = None
    
    print("=" * 80)
    print("🚀 POS SYSTEM - COMPLETE API TESTING WITH FULL SAMPLE DATA")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # ========================================================================
    # 1. HEALTH CHECK
    # ========================================================================
    print("📍 1. HEALTH CHECK")
    test_endpoint("Health Check", "GET", "http://localhost:8000/health")
    test_endpoint("Root Endpoint", "GET", "http://localhost:8000/")
    print()
    
    # ========================================================================
    # 2. USER & AUTH MODULE
    # ========================================================================
    print("📍 2. USER & AUTH MODULE")
    
    # Create admin user with ALL fields
    admin_data = {
        "email": f"admin{random.randint(1000,9999)}@postest.com",
        "username": f"adminuser{random.randint(1000,9999)}",
        "password": "Admin@123456",
        "full_name": "Admin Test User",
        "phone": "+91-9876543210",
        "role": "admin",
        "is_active": True
    }
    admin_user = test_endpoint("Create Admin User", "POST", f"{BASE_URL}/users", data=admin_data)
    
    # Login
    login_data = {
        "email": admin_data["email"],
        "password": admin_data["password"]
    }
    login_response = test_endpoint("Login Admin", "POST", f"{BASE_URL}/auth/login", data=login_data)
    
    if login_response:
        # Extract token from response (wrapped in data object)
        if "data" in login_response and "access_token" in login_response["data"]:
            TOKEN = login_response["data"]["access_token"]
            log(f"🔑 Token: {TOKEN[:50]}...")
        elif "access_token" in login_response:
            TOKEN = login_response["access_token"]
            log(f"🔑 Token: {TOKEN[:50]}...")
    
    # Get current user
    test_endpoint("Get Current User", "GET", f"{BASE_URL}/users/me")
    print()
    
    # ========================================================================
    # 3. RESTAURANT MODULE
    # ========================================================================
    print("📍 3. RESTAURANT MODULE")
    
    # Create restaurant with ALL fields
    slug_num = random.randint(1000,9999)
    restaurant_data = {
        "name": f"Test Restaurant {slug_num}",
        "slug": f"test-restaurant-{slug_num}",
        "business_name": f"Test Business Pvt Ltd {slug_num}",
        "business_type": "restaurant",
        "cuisine_type": ["North Indian", "Chinese", "Continental"],
        "description": "A premium multi-cuisine restaurant offering delightful dining experience",
        "email": f"restaurant{slug_num}@test.com",
        "phone": "+91-9876543211",
        "alternate_phone": "+91-9876543212",
        "address": "123 MG Road, Near City Center",
        "city": "Bangalore",
        "state": "Karnataka",
        "country": "India",
        "postal_code": "560001",
        "gstin": "29ABCDE1234F1Z5",
        "fssai_license": "12345678901234",
        "pan_number": "ABCDE1234F",
        "timezone": "Asia/Kolkata",
        "currency": "INR",
        "language": "en",
        "enable_gst": True,
        "cgst_rate": 2.5,
        "sgst_rate": 2.5,
        "igst_rate": 5.0,
        "service_charge_percentage": 10.0
    }
    restaurant_response = test_endpoint("Create Restaurant", "POST", f"{BASE_URL}/restaurants", data=restaurant_data)
    restaurant_response = extract_data(restaurant_response)
    
    if restaurant_response and "id" in restaurant_response:
        RESTAURANT_ID = restaurant_response["id"]
        log(f"🏪 Restaurant ID: {RESTAURANT_ID}")
    
    if RESTAURANT_ID:
        test_endpoint("Get Restaurant", "GET", f"{BASE_URL}/restaurants/{RESTAURANT_ID}")
        test_endpoint("Update Restaurant", "PUT", f"{BASE_URL}/restaurants/{RESTAURANT_ID}", 
                     data={"description": "Updated description with full details"})
    print()
    
    # ========================================================================
    # 4. STAFF & ROLE MANAGEMENT
    # ========================================================================
    print("📍 4. STAFF & ROLE MANAGEMENT MODULE")
    
    if RESTAURANT_ID:
        # Create Manager Role with ALL fields
        manager_role_data = {
            "name": "Restaurant Manager",
            "code": "manager",  # lowercase enum value
            "description": "Full restaurant management access",
            "level": 8,
            "permissions": [
                "view_staff", "create_staff", "update_staff", "delete_staff",
                "view_order", "create_order", "update_order", "cancel_order",
                "view_product", "create_product", "update_product",
                "view_ingredient", "update_ingredient",
                "view_reports", "view_sales_report", "view_inventory_report"
            ]
        }
        manager_role = test_endpoint("Create Manager Role", "POST", 
                                     f"{BASE_URL}/staff/roles?restaurant_id={RESTAURANT_ID}", 
                                     data=manager_role_data)
        manager_role = extract_data(manager_role)
        
        manager_role_id = manager_role.get("id") if manager_role else None
        
        if manager_role_id:
            # Create Staff with ALL fields
            staff_data = {
                "role_id": manager_role_id,
                "employee_code": generate_code("EMP"),
                "first_name": "Rajesh",
                "last_name": "Kumar",
                "email": f"rajesh{random.randint(1000,9999)}@test.com",
                "phone": "+91-9876543213",
                "alternate_phone": "+91-9876543214",
                "address_line1": "456 Brigade Road",
                "address_line2": "Apt 101",
                "city": "Bangalore",
                "state": "Karnataka",
                "postal_code": "560025",
                "country": "India",
                "emergency_contact_name": "Sunita Kumar",
                "emergency_contact_phone": "+91-9876543215",
                "emergency_contact_relation": "Wife",
                "date_of_joining": (date.today() - timedelta(days=180)).isoformat(),
                "employment_type": "Full Time",
                "department": "Operations",
                "designation": "Restaurant Manager",
                "basic_salary": 50000.00,
                "allowances": 10000.00,
                "aadhar_number": "123456789012",
                "pan_number": "ABCDE1234F",
                "bank_account_number": "1234567890",
                "bank_name": "State Bank of India",
                "bank_ifsc_code": "SBIN0001234",
                "working_hours_per_week": 48,
                "leaves_per_year": 24
            }
            staff = test_endpoint("Create Staff", "POST", 
                                 f"{BASE_URL}/staff?restaurant_id={RESTAURANT_ID}", 
                                 data=staff_data)
            staff = extract_data(staff)
            
            staff_id = staff.get("id") if staff else None
            
            if staff_id:
                # Create Shift with ALL fields
                shift_data = {
                    "name": "Morning Shift",
                    "shift_type": "MORNING",
                    "start_time": "08:00:00",
                    "end_time": "16:00:00",
                    "break_duration_minutes": 60,
                    "break_start_time": "12:00:00",
                    "days_of_week": [0, 1, 2, 3, 4],  # Mon-Fri
                    "max_staff": 10,
                    "color_code": "#4CAF50",
                    "description": "Morning shift from 8 AM to 4 PM with 1 hour lunch break",
                    "is_active": True
                }
                shift = test_endpoint("Create Shift", "POST", 
                                     f"{BASE_URL}/staff/shifts?restaurant_id={RESTAURANT_ID}", 
                                     data=shift_data)
                shift = extract_data(shift)
                
                shift_id = shift.get("id") if shift else None
                
                if shift_id:
                    # Mark Attendance with ALL fields
                    attendance_data = {
                        "shift_id": shift_id,
                        "check_in_time": "08:05:00",
                        "check_in_location": "Main Entrance",
                        "check_in_notes": "On time, ready to start",
                        "check_out_time": "16:10:00",
                        "check_out_location": "Main Entrance",
                        "check_out_notes": "Completed all tasks",
                        "actual_hours": 8.08,
                        "overtime_hours": 0.17,
                        "break_duration_minutes": 60,
                        "status": "PRESENT",
                        "notes": "Productive day, handled 15 orders",
                        "approved_by": None
                    }
                    test_endpoint("Mark Attendance", "POST", 
                                 f"{BASE_URL}/staff/{staff_id}/attendance", 
                                 data=attendance_data)
                    
                    # Apply Leave with ALL fields
                    leave_data = {
                        "leave_type": "SICK",
                        "start_date": (date.today() + timedelta(days=7)).isoformat(),
                        "end_date": (date.today() + timedelta(days=9)).isoformat(),
                        "total_days": 3,
                        "reason": "Medical checkup and recovery - Doctor's appointment scheduled",
                        "emergency_contact": "+91-9876543215",
                        "medical_certificate": "MC_2024_001.pdf",
                        "notes": "Will share medical reports post recovery"
                    }
                    test_endpoint("Apply Leave", "POST", 
                                 f"{BASE_URL}/staff/{staff_id}/leaves", 
                                 data=leave_data)
        
        # List all staff
        test_endpoint("List Staff", "GET", f"{BASE_URL}/staff?restaurant_id={RESTAURANT_ID}")
    print()
    
    # ========================================================================
    # 5. CUSTOMER MODULE
    # ========================================================================
    print("📍 5. CUSTOMER MODULE")
    
    if RESTAURANT_ID:
        # Create Customer with ALL fields
        customer_data = {
            "name": "Priya Sharma",
            "email": f"priya{random.randint(1000,9999)}@test.com",
            "phone": "+91-9876543216",
            "alternate_phone": "+91-9876543217",
            "date_of_birth": "1990-05-15",
            "anniversary_date": "2015-12-10",
            "gender": "female",
            "address_line1": "789 Koramangala",
            "address_line2": "5th Block",
            "city": "Bangalore",
            "state": "Karnataka",
            "postal_code": "560034",
            "country": "India",
            "loyalty_points": 500,
            "total_orders": 15,
            "total_spent": 750000,  # ₹7,500 in paise
            "average_order_value": 50000,  # ₹500 in paise
            "last_order_date": datetime.now().isoformat(),
            "notes": "VIP customer, prefers vegetarian options, allergic to nuts",
            "tags": ["VIP", "Vegetarian", "Regular"],
            "preferences": {
                "seating": "Window seat",
                "cuisine": "North Indian",
                "spice_level": "Medium",
                "dietary": "Vegetarian"
            },
            "is_active": True
        }
        customer = test_endpoint("Create Customer", "POST", 
                                f"{BASE_URL}/customers?restaurant_id={RESTAURANT_ID}", 
                                data=customer_data)
        customer = extract_data(customer)
        
        customer_id = customer.get("id") if customer else None
        
        if customer_id:
            test_endpoint("Get Customer", "GET", f"{BASE_URL}/customers/{customer_id}")
            test_endpoint("Update Customer", "PUT", f"{BASE_URL}/customers/{customer_id}", 
                         data={"loyalty_points": 600, "notes": "Updated: Recently celebrated anniversary here"})
        
        test_endpoint("List Customers", "GET", f"{BASE_URL}/customers?restaurant_id={RESTAURANT_ID}")
    print()
    
    # ========================================================================
    # 6. TABLE MANAGEMENT
    # ========================================================================
    print("📍 6. TABLE MANAGEMENT MODULE")
    
    if RESTAURANT_ID:
        # Create Table with ALL fields
        table_data = {
            "restaurant_id": RESTAURANT_ID,
            "table_number": f"T{random.randint(100,999)}",
            "table_name": "Premium Window Table",
            "capacity": 4,
            "min_capacity": 2,
            "floor": "Ground Floor",
            "section": "Window Section",
            "position_x": 100,
            "position_y": 200,
            "image": "https://example.com/table.jpg",
            "qr_code": f"QR{random.randint(10000,99999)}",
            "status": "available",  # lowercase enum value
            "is_bookable": True,
            "is_outdoor": False,
            "is_accessible": True,
            "has_power_outlet": True,
            "minimum_spend": 100000,  # ₹1,000 in paise
            "description": "Premium window table with city view, power outlets, best for families",
            "notes": "Popular table, requires advance booking on weekends"
        }
        table = test_endpoint("Create Table", "POST", f"{BASE_URL}/tables", data=table_data)
        table = extract_data(table)
        
        table_id = table.get("id") if table else None
        
        if table_id:
            test_endpoint("Get Table", "GET", f"{BASE_URL}/tables/{table_id}")
            test_endpoint("Update Table Status", "PATCH", f"{BASE_URL}/tables/{table_id}/status", 
                         data={"status": "occupied"})
        
        test_endpoint("List Tables", "GET", f"{BASE_URL}/tables", 
                     params={"restaurant_id": RESTAURANT_ID})
    print()
    
    # ========================================================================
    # 7. PRODUCT MODULE
    # ========================================================================
    print("📍 7. PRODUCT MODULE")
    
    if RESTAURANT_ID:
        # Create Category with ALL fields
        slug = f"main-course-{random.randint(1000,9999)}"
        category_data = {
            "restaurant_id": RESTAURANT_ID,
            "name": "Main Course",
            "slug": slug,
            "description": "Delicious main course dishes - includes rice, rotis, curries and biryanis",
            "active": True,
            "sort_order": 2,
            "image": "https://example.com/category-main.jpg"
        }
        category = test_endpoint("Create Category", "POST", f"{BASE_URL}/products/categories", 
                                data=category_data)
        category = extract_data(category)
        
        category_id = category.get("id") if category else None
        
        if category_id:
            # Create Product with ALL fields
            product_slug = f"paneer-butter-masala-{random.randint(1000,9999)}"
            product_data = {
                "restaurant_id": RESTAURANT_ID,
                "name": "Paneer Butter Masala",
                "slug": product_slug,
                "description": "Rich and creamy paneer curry with butter, tomatoes, and aromatic spices. Served with naan or rice.",
                "price": 32000,  # ₹320 in paise
                "cost": 15000,   # ₹150 in paise
                "category_id": category_id,
                "stock": 50,
                "min_stock": 10,
                "available": True,
                "featured": True,
                "image": "https://example.com/paneer-butter-masala.jpg",
                "images": [
                    "https://example.com/paneer-1.jpg",
                    "https://example.com/paneer-2.jpg"
                ],
                "tags": ["Vegetarian", "Popular", "North Indian", "Spicy"],
                "department": "kitchen",
                "printer_tag": "KITCHEN_MAIN",
                "preparation_time": 20,
                "nutritional_info": {
                    "calories": 350,
                    "protein": "15g",
                    "carbs": "25g",
                    "fat": "20g",
                    "fiber": "5g"
                }
            }
            product = test_endpoint("Create Product", "POST", f"{BASE_URL}/products", 
                                   data=product_data)
            product = extract_data(product)
            
            product_id = product.get("id") if product else None
            
            if product_id:
                test_endpoint("Get Product", "GET", f"{BASE_URL}/products/{product_id}")
                test_endpoint("Update Product", "PUT", f"{BASE_URL}/products/{product_id}", 
                             data={"price": 35000, "stock": 45})
            
            test_endpoint("List Products", "GET", f"{BASE_URL}/products", 
                         params={"restaurant_id": RESTAURANT_ID})
    print()
    
    # ========================================================================
    # 8. INVENTORY MODULE
    # ========================================================================
    print("📍 8. INVENTORY MODULE")
    
    if RESTAURANT_ID:
        # Create Supplier with ALL fields
        supplier_data = {
            "restaurant_id": RESTAURANT_ID,
            "name": "Fresh Farm Suppliers",
            "code": generate_code("SUP"),
            "company_name": "Fresh Farm Suppliers Pvt Ltd",
            "contact_person": "Ramesh Patel",
            "email": f"ramesh{random.randint(1000,9999)}@freshfarm.com",
            "phone": "+91-9876543218",
            "alternate_phone": "+91-9876543219",
            "address_line1": "Plot 45, Industrial Area",
            "address_line2": "Phase 2",
            "city": "Bangalore",
            "state": "Karnataka",
            "postal_code": "560058",
            "country": "India",
            "gstin": "29ABCDE1234F2Z5",
            "pan": "ABCDE1234G",
            "payment_terms_days": 30,
            "credit_limit": 50000000,  # ₹5,00,000 in paise
            "supply_categories": ["Vegetables", "Dairy", "Spices"],
            "bank_name": "HDFC Bank",
            "account_number": "9876543210",
            "ifsc_code": "HDFC0001234",
            "notes": "Reliable supplier, delivers fresh produce daily. Good payment history."
        }
        supplier = test_endpoint("Create Supplier", "POST", f"{BASE_URL}/inventory/suppliers", 
                                data=supplier_data)
        supplier = extract_data(supplier)
        
        supplier_id = supplier.get("id") if supplier else None
        
        if supplier_id:
            test_endpoint("Get Supplier", "GET", f"{BASE_URL}/inventory/suppliers/{supplier_id}")
            test_endpoint("List Suppliers", "GET", f"{BASE_URL}/inventory/suppliers", 
                         params={"restaurant_id": RESTAURANT_ID})
    print()
    
    # ========================================================================
    # 9. ORDER MODULE
    # ========================================================================
    print("📍 9. ORDER MODULE")
    
    if RESTAURANT_ID and product_id and table_id and customer_id:
        # Create Order with ALL fields
        order_data = {
            "restaurant_id": RESTAURANT_ID,
            "order_type": "dine_in",
            "table_id": table_id,
            "customer_id": customer_id,
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2,
                    "notes": "Extra spicy, no onions"
                }
            ],
            "guest_count": 2,
            "special_instructions": "Customer is allergic to nuts",
            "kitchen_notes": "Anniversary celebration - please add complimentary dessert",
            "is_priority": False,
            "requires_cutlery": True
        }
        order = test_endpoint("Create Order", "POST", 
                             f"{BASE_URL}/orders", 
                             data=order_data)
        order = extract_data(order)
        
        order_id = order.get("id") if order else None
        
        if order_id:
            test_endpoint("Get Order", "GET", f"{BASE_URL}/orders/{order_id}")
            test_endpoint("Update Order Status", "PATCH", f"{BASE_URL}/orders/{order_id}/status", 
                         data={"status": "preparing"})
            test_endpoint("List Orders", "GET", f"{BASE_URL}/orders", 
                         params={"restaurant_id": RESTAURANT_ID})
    print()
    
    # ========================================================================
    # 10. KDS (Kitchen Display System) MODULE
    # ========================================================================
    print("📍 10. KDS (KITCHEN DISPLAY SYSTEM) MODULE")
    
    if RESTAURANT_ID:
        test_endpoint("Get Kitchen Orders", "GET", f"{BASE_URL}/kds/orders", 
                     params={"restaurant_id": RESTAURANT_ID, "department": "kitchen"})
        
        if order_id:
            test_endpoint("Update KDS Item Status", "PATCH", 
                         f"{BASE_URL}/kds/orders/{order_id}/items/{product_id}/status", 
                         data={"status": "preparing"})
    print()
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("=" * 80)
    print("✨ TESTING COMPLETED")
    print("=" * 80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n📊 All API endpoints tested with complete sample data!")
    print("🎉 Check the logs above for detailed results")


if __name__ == "__main__":
    main()
