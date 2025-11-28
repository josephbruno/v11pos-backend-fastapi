"""
Simple end-to-end API test
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json"}

# Credentials
ADMIN = {"email": "admin@pos.com", "password": "admin123"}
admin_token = None

print("\n" + "="*70)
print("  API END-TO-END TEST")
print("="*70 + "\n")

# 1. Login
print("1️⃣  Logging in as admin...")
response = requests.post(
    f"{BASE_URL}/auth/login/json",
    headers=HEADERS,
    json=ADMIN
)

if response.status_code == 200:
    admin_token = response.json().get("access_token")
    print(f"   ✅ Login successful")
    print(f"   Token: {admin_token[:40]}...\n")
else:
    print(f"   ❌ Login failed: {response.status_code}\n")
    exit(1)

headers = {**HEADERS, "Authorization": f"Bearer {admin_token}"}

# 2. Get categories
print("2️⃣  Fetching categories...")
response = requests.get(f"{BASE_URL}/categories", headers=headers)
if response.status_code == 200:
    categories = response.json()
    print(f"   ✅ Found {len(categories)} categories")
    if categories:
        for i, cat in enumerate(categories[:3], 1):
            print(f"      {i}. {cat.get('name')} ({cat.get('id')})")
    print()
else:
    print(f"   ❌ Failed: {response.status_code}\n")

# 3. Get products
print("3️⃣  Fetching products...")
response = requests.get(f"{BASE_URL}/products", headers=headers)
if response.status_code == 200:
    products = response.json()
    print(f"   ✅ Found {len(products)} products")
    if products:
        for i, prod in enumerate(products[:3], 1):
            print(f"      {i}. {prod.get('name')} - ₹{prod.get('price')}")
    print()
else:
    print(f"   ❌ Failed: {response.status_code}\n")

# 4. Get orders
print("4️⃣  Fetching orders...")
response = requests.get(f"{BASE_URL}/orders", headers=headers)
if response.status_code == 200:
    orders = response.json()
    print(f"   ✅ Found {len(orders)} orders")
    if orders:
        for i, order in enumerate(orders[:3], 1):
            print(f"      {i}. Order #{order.get('order_number')} - Status: {order.get('status')}")
    print()
else:
    print(f"   ❌ Failed: {response.status_code}\n")

# 5. Get current user
print("5️⃣  Getting current user info...")
response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
if response.status_code == 200:
    user = response.json()
    print(f"   ✅ User: {user.get('name')}")
    print(f"      Email: {user.get('email')}")
    print(f"      Role: {user.get('role')}")
    print()
else:
    print(f"   ❌ Failed: {response.status_code}\n")

print("="*70)
print("  ✅ END-TO-END TEST COMPLETE")
print("="*70 + "\n")
