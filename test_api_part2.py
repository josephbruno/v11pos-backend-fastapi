"""
Comprehensive API Testing Script - Part 2
Tests: Products, Inventory, Orders, KDS
"""
import requests
import json
from datetime import datetime, date, timedelta
import time

# Base URL
BASE_URL = "http://localhost:8000"

# Load test data from Part 1
try:
    with open('test_data.json', 'r') as f:
        test_data = json.load(f)
    print("✅ Loaded test data from Part 1")
except:
    print("❌ Error: Run test_api_part1.py first!")
    exit(1)

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
# 6. PRODUCT TESTS
# ============================================================================

def test_product_endpoints():
    print_section("6. PRODUCT MODULE")
    
    if not test_data.get('restaurants', {}).get('main'):
        print("⚠️ Skipping - No restaurant created")
        return
    
    restaurant_id = test_data['restaurants']['main']['id']
    token = test_data['tokens']['admin']
    
    # 6.1 Create Categories
    print_test("/products/categories", "POST")
    categories = [
        {
            "name": "Appetizers",
            "description": "Starters and small plates",
            "display_order": 1,
            "is_active": True,
            "image_url": "https://example.com/appetizers.jpg"
        },
        {
            "name": "Main Course",
            "description": "Primary dishes",
            "display_order": 2,
            "is_active": True
        },
        {
            "name": "Beverages",
            "description": "Drinks and refreshments",
            "display_order": 3,
            "is_active": True
        },
        {
            "name": "Desserts",
            "description": "Sweet treats",
            "display_order": 4,
            "is_active": True
        }
    ]
    
    test_data['categories'] = {}
    for cat in categories:
        response = requests.post(
            f"{BASE_URL}/products/categories?restaurant_id={restaurant_id}",
            json=cat,
            headers=get_headers(token)
        )
        print_result(response, show_data=False)
        if response.status_code < 400:
            cat_data = response.json().get('data', {})
            test_data['categories'][cat['name']] = cat_data
    
    # 6.2 Create Products
    if test_data['categories'].get('Main Course'):
        print_test("/products", "POST")
        products = [
            {
                "category_id": test_data['categories']['Main Course']['id'],
                "name": "Butter Chicken",
                "description": "Tender chicken in rich tomato-butter gravy",
                "price": 45000,  # ₹450.00 in paise
                "cost_price": 20000,
                "sku": "BC001",
                "barcode": "8901234567890",
                "is_vegetarian": False,
                "is_vegan": False,
                "spice_level": "medium",
                "preparation_time": 25,
                "calories": 450,
                "is_available": True,
                "is_featured": True,
                "tags": ["popular", "spicy", "north-indian"],
                "allergens": ["dairy", "nuts"]
            },
            {
                "category_id": test_data['categories']['Main Course']['id'],
                "name": "Paneer Tikka Masala",
                "description": "Cottage cheese in spiced tomato gravy",
                "price": 38000,
                "cost_price": 15000,
                "sku": "PTM001",
                "is_vegetarian": True,
                "is_vegan": False,
                "spice_level": "medium",
                "preparation_time": 20,
                "calories": 380,
                "is_available": True,
                "tags": ["vegetarian", "popular"]
            }
        ]
        
        test_data['products'] = {}
        for prod in products:
            response = requests.post(
                f"{BASE_URL}/products?restaurant_id={restaurant_id}",
                json=prod,
                headers=get_headers(token)
            )
            print_result(response, show_data=False)
            if response.status_code < 400:
                prod_data = response.json().get('data', {})
                test_data['products'][prod['name']] = prod_data
    
    # 6.3 Create Beverages
    if test_data['categories'].get('Beverages'):
        beverages = [
            {
                "category_id": test_data['categories']['Beverages']['id'],
                "name": "Fresh Lime Soda",
                "description": "Refreshing lime juice with soda",
                "price": 8000,
                "cost_price": 2000,
                "sku": "FLS001",
                "is_vegetarian": True,
                "is_vegan": True,
                "preparation_time": 5,
                "calories": 80,
                "is_available": True
            },
            {
                "category_id": test_data['categories']['Beverages']['id'],
                "name": "Mango Lassi",
                "description": "Creamy mango yogurt drink",
                "price": 12000,
                "cost_price": 4000,
                "sku": "ML001",
                "is_vegetarian": True,
                "preparation_time": 5,
                "calories": 200,
                "is_available": True
            }
        ]
        
        for bev in beverages:
            response = requests.post(
                f"{BASE_URL}/products?restaurant_id={restaurant_id}",
                json=bev,
                headers=get_headers(token)
            )
            if response.status_code < 400:
                test_data['products'][bev['name']] = response.json().get('data', {})
    
    # 6.4 List Products
    print_test(f"/products/restaurant/{restaurant_id}", "GET")
    response = requests.get(
        f"{BASE_URL}/products/restaurant/{restaurant_id}?skip=0&limit=20",
        headers=get_headers(token)
    )
    print_result(response)
    
    # Save updated test data
    with open('test_data.json', 'w') as f:
        json.dump(test_data, f, indent=2, default=str)


# ============================================================================
# 7. INVENTORY TESTS
# ============================================================================

def test_inventory_endpoints():
    print_section("7. INVENTORY MODULE")
    
    if not test_data.get('restaurants', {}).get('main'):
        print("⚠️ Skipping - No restaurant created")
        return
    
    restaurant_id = test_data['restaurants']['main']['id']
    token = test_data['tokens']['admin']
    
    # 7.1 Create Suppliers
    print_test("/inventory/suppliers", "POST")
    suppliers = [
        {
            "name": "Fresh Farm Suppliers",
            "code": "SUP001",
            "contact_person": "Ramesh Patel",
            "email": "ramesh@freshfarm.com",
            "phone": "+91-9876543240",
            "address": "Plot 45, APMC Market",
            "city": "Bangalore",
            "state": "Karnataka",
            "postal_code": "560002",
            "gstin": "29ABCDE5678F1Z5",
            "payment_terms_days": 30,
            "credit_limit": 50000000,
            "supply_categories": ["vegetables", "fruits", "dairy"],
            "rating": 4.5
        },
        {
            "name": "Spice Masters",
            "code": "SUP002",
            "contact_person": "Ahmed Khan",
            "email": "ahmed@spicemasters.com",
            "phone": "+91-9876543241",
            "address": "Shop 12, Spice Market",
            "city": "Bangalore",
            "state": "Karnataka",
            "postal_code": "560051",
            "payment_terms_days": 15,
            "credit_limit": 20000000,
            "supply_categories": ["spices", "condiments"]
        }
    ]
    
    test_data['suppliers'] = {}
    for sup in suppliers:
        response = requests.post(
            f"{BASE_URL}/inventory/suppliers?restaurant_id={restaurant_id}",
            json=sup,
            headers=get_headers(token)
        )
        print_result(response, show_data=False)
        if response.status_code < 400:
            sup_data = response.json().get('data', {})
            test_data['suppliers'][sup['name']] = sup_data
    
    # 7.2 Create Ingredients
    print_test("/inventory/ingredients", "POST")
    ingredients = [
        {
            "name": "Chicken Breast",
            "category": "Meat",
            "unit_of_measure": "kg",
            "current_stock": 50.0,
            "minimum_stock": 10.0,
            "reorder_level": 20.0,
            "maximum_stock": 100.0,
            "cost_price": 35000,
            "supplier_id": test_data['suppliers']['Fresh Farm Suppliers']['id'] if test_data['suppliers'].get('Fresh Farm Suppliers') else None,
            "sku": "ING-CHK001",
            "is_perishable": True,
            "shelf_life_days": 3,
            "track_expiry": True,
            "low_stock_alert_enabled": True
        },
        {
            "name": "Paneer",
            "category": "Dairy",
            "unit_of_measure": "kg",
            "current_stock": 30.0,
            "minimum_stock": 5.0,
            "reorder_level": 10.0,
            "cost_price": 30000,
            "supplier_id": test_data['suppliers']['Fresh Farm Suppliers']['id'] if test_data['suppliers'].get('Fresh Farm Suppliers') else None,
            "sku": "ING-PAN001",
            "is_perishable": True,
            "shelf_life_days": 5,
            "track_expiry": True
        },
        {
            "name": "Tomato",
            "category": "Vegetables",
            "unit_of_measure": "kg",
            "current_stock": 40.0,
            "minimum_stock": 15.0,
            "reorder_level": 25.0,
            "cost_price": 4000,
            "supplier_id": test_data['suppliers']['Fresh Farm Suppliers']['id'] if test_data['suppliers'].get('Fresh Farm Suppliers') else None,
            "sku": "ING-TOM001",
            "is_perishable": True,
            "shelf_life_days": 7
        },
        {
            "name": "Garam Masala",
            "category": "Spices",
            "unit_of_measure": "kg",
            "current_stock": 5.0,
            "minimum_stock": 1.0,
            "reorder_level": 2.0,
            "cost_price": 50000,
            "supplier_id": test_data['suppliers']['Spice Masters']['id'] if test_data['suppliers'].get('Spice Masters') else None,
            "sku": "ING-GM001",
            "is_perishable": False
        }
    ]
    
    test_data['ingredients'] = {}
    for ing in ingredients:
        response = requests.post(
            f"{BASE_URL}/inventory/ingredients?restaurant_id={restaurant_id}",
            json=ing,
            headers=get_headers(token)
        )
        print_result(response, show_data=False)
        if response.status_code < 400:
            ing_data = response.json().get('data', {})
            test_data['ingredients'][ing['name']] = ing_data
    
    # 7.3 Create Recipe
    if (test_data['products'].get('Butter Chicken') and 
        test_data['ingredients'].get('Chicken Breast')):
        print_test("/inventory/recipes", "POST")
        recipe_data = {
            "product_id": test_data['products']['Butter Chicken']['id'],
            "name": "Butter Chicken Recipe",
            "yield_quantity": 1,
            "prep_time_minutes": 15,
            "cook_time_minutes": 20,
            "instructions": "1. Marinate chicken\n2. Cook in butter\n3. Add gravy",
            "ingredients": [
                {
                    "ingredient_id": test_data['ingredients']['Chicken Breast']['id'],
                    "quantity": 0.250,
                    "unit": "kg",
                    "preparation_note": "Boneless, cut into cubes"
                },
                {
                    "ingredient_id": test_data['ingredients']['Tomato']['id'],
                    "quantity": 0.150,
                    "unit": "kg",
                    "preparation_note": "Pureed"
                }
            ]
        }
        
        if test_data['ingredients'].get('Garam Masala'):
            recipe_data['ingredients'].append({
                "ingredient_id": test_data['ingredients']['Garam Masala']['id'],
                "quantity": 0.005,
                "unit": "kg",
                "preparation_note": "Ground"
            })
        
        response = requests.post(
            f"{BASE_URL}/inventory/recipes?restaurant_id={restaurant_id}",
            json=recipe_data,
            headers=get_headers(token)
        )
        print_result(response)
        if response.status_code < 400:
            test_data['recipes'] = {'Butter Chicken': response.json().get('data', {})}
    
    # 7.4 Create Purchase Order
    if test_data['suppliers'].get('Fresh Farm Suppliers') and test_data['ingredients'].get('Chicken Breast'):
        print_test("/inventory/purchase-orders", "POST")
        po_data = {
            "supplier_id": test_data['suppliers']['Fresh Farm Suppliers']['id'],
            "expected_delivery_date": (date.today() + timedelta(days=2)).isoformat(),
            "payment_terms": "Net 30 days",
            "notes": "Urgent order - Festival season",
            "items": [
                {
                    "ingredient_id": test_data['ingredients']['Chicken Breast']['id'],
                    "quantity_ordered": 30.0,
                    "unit": "kg",
                    "unit_price": 33000,
                    "tax_percentage": 5.0,
                    "discount_percentage": 2.0
                },
                {
                    "ingredient_id": test_data['ingredients']['Tomato']['id'],
                    "quantity_ordered": 50.0,
                    "unit": "kg",
                    "unit_price": 3800,
                    "tax_percentage": 0.0
                }
            ],
            "shipping_charges": 50000,
            "discount_amount": 10000
        }
        
        response = requests.post(
            f"{BASE_URL}/inventory/purchase-orders?restaurant_id={restaurant_id}",
            json=po_data,
            headers=get_headers(token)
        )
        print_result(response)
        if response.status_code < 400:
            test_data['purchase_orders'] = {'main': response.json().get('data', {})}
    
    # 7.5 Stock Adjustment
    if test_data['ingredients'].get('Paneer'):
        print_test("/inventory/stock/adjustment", "POST")
        adjustment_data = {
            "ingredient_id": test_data['ingredients']['Paneer']['id'],
            "quantity": 5.0,
            "reason": "Physical count adjustment - found extra stock"
        }
        response = requests.post(
            f"{BASE_URL}/inventory/stock/adjustment?restaurant_id={restaurant_id}",
            json=adjustment_data,
            headers=get_headers(token)
        )
        print_result(response)
    
    # 7.6 Wastage Entry
    if test_data['ingredients'].get('Tomato'):
        print_test("/inventory/stock/wastage", "POST")
        wastage_data = {
            "ingredient_id": test_data['ingredients']['Tomato']['id'],
            "quantity": 2.5,
            "reason": "Spoiled - found rotten",
            "notes": "From yesterday's delivery - quality issue"
        }
        response = requests.post(
            f"{BASE_URL}/inventory/stock/wastage?restaurant_id={restaurant_id}",
            json=wastage_data,
            headers=get_headers(token)
        )
        print_result(response)
    
    # 7.7 Get Low Stock Alerts
    print_test(f"/inventory/alerts/low-stock/restaurant/{restaurant_id}", "GET")
    response = requests.get(
        f"{BASE_URL}/inventory/alerts/low-stock/restaurant/{restaurant_id}",
        headers=get_headers(token)
    )
    print_result(response)
    
    # Save updated test data
    with open('test_data.json', 'w') as f:
        json.dump(test_data, f, indent=2, default=str)


# ============================================================================
# 8. ORDER TESTS
# ============================================================================

def test_order_endpoints():
    print_section("8. ORDER MODULE")
    
    if not test_data.get('restaurants', {}).get('main'):
        print("⚠️ Skipping - No restaurant created")
        return
    
    restaurant_id = test_data['restaurants']['main']['id']
    token = test_data['tokens']['admin']
    
    # 8.1 Create Dine-in Order
    if (test_data.get('tables', {}).get('T001') and 
        test_data.get('products', {}).get('Butter Chicken') and
        test_data.get('customers', {}).get('vip')):
        
        print_test("/orders", "POST")
        order_data = {
            "order_type": "dine_in",
            "table_id": test_data['tables']['T001']['id'],
            "customer_id": test_data['customers']['vip']['id'],
            "customer_name": "Amit Verma",
            "customer_phone": "+91-9876543230",
            "notes": "Extra spicy, no onions",
            "items": [
                {
                    "product_id": test_data['products']['Butter Chicken']['id'],
                    "quantity": 2,
                    "unit_price": 45000,
                    "notes": "Extra spicy"
                }
            ]
        }
        
        # Add beverages if available
        if test_data.get('products', {}).get('Mango Lassi'):
            order_data['items'].append({
                "product_id": test_data['products']['Mango Lassi']['id'],
                "quantity": 2,
                "unit_price": 12000
            })
        
        response = requests.post(
            f"{BASE_URL}/orders?restaurant_id={restaurant_id}",
            json=order_data,
            headers=get_headers(token)
        )
        print_result(response)
        if response.status_code < 400:
            test_data['orders'] = {'dine_in': response.json().get('data', {})}
    
    # 8.2 Create Takeaway Order
    if test_data.get('products', {}).get('Paneer Tikka Masala'):
        print_test("/orders (Takeaway)", "POST")
        takeaway_order = {
            "order_type": "takeaway",
            "customer_name": "Sneha Reddy",
            "customer_phone": "+91-9876543231",
            "customer_id": test_data.get('customers', {}).get('regular', {}).get('id'),
            "items": [
                {
                    "product_id": test_data['products']['Paneer Tikka Masala']['id'],
                    "quantity": 1,
                    "unit_price": 38000
                }
            ]
        }
        
        if test_data.get('products', {}).get('Fresh Lime Soda'):
            takeaway_order['items'].append({
                "product_id": test_data['products']['Fresh Lime Soda']['id'],
                "quantity": 1,
                "unit_price": 8000
            })
        
        response = requests.post(
            f"{BASE_URL}/orders?restaurant_id={restaurant_id}",
            json=takeaway_order,
            headers=get_headers(token)
        )
        print_result(response)
        if response.status_code < 400:
            test_data['orders']['takeaway'] = response.json().get('data', {})
    
    # 8.3 List Orders
    print_test(f"/orders/restaurant/{restaurant_id}", "GET")
    response = requests.get(
        f"{BASE_URL}/orders/restaurant/{restaurant_id}?skip=0&limit=10",
        headers=get_headers(token)
    )
    print_result(response)
    
    # 8.4 Update Order Status
    if test_data.get('orders', {}).get('dine_in'):
        order_id = test_data['orders']['dine_in']['id']
        print_test(f"/orders/{order_id}/status", "PATCH")
        response = requests.patch(
            f"{BASE_URL}/orders/{order_id}/status?status=preparing",
            headers=get_headers(token)
        )
        print_result(response)
    
    # Save updated test data
    with open('test_data.json', 'w') as f:
        json.dump(test_data, f, indent=2, default=str)


# ============================================================================
# 9. KDS TESTS
# ============================================================================

def test_kds_endpoints():
    print_section("9. KITCHEN DISPLAY SYSTEM (KDS)")
    
    if not test_data.get('restaurants', {}).get('main'):
        print("⚠️ Skipping - No restaurant created")
        return
    
    restaurant_id = test_data['restaurants']['main']['id']
    token = test_data['tokens']['admin']
    
    # 9.1 Create Kitchen Stations
    print_test("/kds/stations", "POST")
    stations = [
        {
            "name": "Main Kitchen",
            "code": "MAIN-KIT",
            "type": "hot_kitchen",
            "description": "Primary cooking station",
            "is_active": True,
            "display_order": 1
        },
        {
            "name": "Beverage Counter",
            "code": "BEV-CNT",
            "type": "beverage",
            "description": "Drinks and beverages preparation",
            "is_active": True,
            "display_order": 2
        },
        {
            "name": "Dessert Station",
            "code": "DST-STN",
            "type": "dessert",
            "description": "Desserts and sweets",
            "is_active": True,
            "display_order": 3
        }
    ]
    
    test_data['kitchen_stations'] = {}
    for station in stations:
        response = requests.post(
            f"{BASE_URL}/kds/stations?restaurant_id={restaurant_id}",
            json=station,
            headers=get_headers(token)
        )
        print_result(response, show_data=False)
        if response.status_code < 400:
            station_data = response.json().get('data', {})
            test_data['kitchen_stations'][station['name']] = station_data
    
    # 9.2 List Active KDS Items
    print_test(f"/kds/displays/restaurant/{restaurant_id}", "GET")
    response = requests.get(
        f"{BASE_URL}/kds/displays/restaurant/{restaurant_id}?status=pending",
        headers=get_headers(token)
    )
    print_result(response)
    
    # 9.3 Get KDS Items by Station
    if test_data.get('kitchen_stations', {}).get('Main Kitchen'):
        station_id = test_data['kitchen_stations']['Main Kitchen']['id']
        print_test(f"/kds/displays/station/{station_id}", "GET")
        response = requests.get(
            f"{BASE_URL}/kds/displays/station/{station_id}",
            headers=get_headers(token)
        )
        print_result(response)
    
    # Save updated test data
    with open('test_data.json', 'w') as f:
        json.dump(test_data, f, indent=2, default=str)


# ============================================================================
# Main Execution
# ============================================================================

def main():
    print("\n" + "🚀"*40)
    print("  POS SYSTEM API TESTING - PART 2")
    print("  (Products, Inventory, Orders, KDS)")
    print("🚀"*40)
    print(f"\n📍 Base URL: {BASE_URL}")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Test each module
        test_product_endpoints()
        test_inventory_endpoints()
        test_order_endpoints()
        test_kds_endpoints()
        
        print_section("TEST SUMMARY - PART 2")
        print(f"✅ Tests completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n📊 Additional Test Data Created:")
        print(f"   - Categories: {len(test_data.get('categories', {}))}")
        print(f"   - Products: {len(test_data.get('products', {}))}")
        print(f"   - Suppliers: {len(test_data.get('suppliers', {}))}")
        print(f"   - Ingredients: {len(test_data.get('ingredients', {}))}")
        print(f"   - Recipes: {len(test_data.get('recipes', {}))}")
        print(f"   - Purchase Orders: {len(test_data.get('purchase_orders', {}))}")
        print(f"   - Kitchen Stations: {len(test_data.get('kitchen_stations', {}))}")
        print(f"   - Orders: {len(test_data.get('orders', {}))}")
        
        print(f"\n💾 Updated test data saved to: test_data.json")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Testing interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
