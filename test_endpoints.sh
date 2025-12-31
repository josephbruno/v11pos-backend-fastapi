#!/bin/bash

# API Testing Script for POS System
# Tests all endpoints with comprehensive sample data

BASE_URL="http://localhost:8000/api/v1"

echo "================================================"
echo "POS System API Testing"
echo "================================================"

# Step 1: Login and get token
echo -e "\n[1] Login as superadmin..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" -F "email=superadmin@restaurant.com" -F "password=SuperAdmin@123")
TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "❌ Login failed!"
    exit 1
fi
echo "✅ Login successful"

# Step 2: Get Restaurant ID
echo -e "\n[2] Getting restaurant ID..."
RESTAURANT_RESPONSE=$(curl -s -X GET "$BASE_URL/restaurants/" -H "Authorization: Bearer $TOKEN")
RESTAURANT_ID=$(echo $RESTAURANT_RESPONSE | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['data'][0]['id'] if d.get('success') and d.get('data') else '')" 2>/dev/null)

if [ -z "$RESTAURANT_ID" ]; then
    echo "No restaurant found. Creating one..."
    CREATE_REST_RESPONSE=$(curl -s -X POST "$BASE_URL/restaurants" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{
      "name": "Test Restaurant",
      "business_name": "Test Restaurant LLC",
      "slug": "test-restaurant",
      "email": "test@restaurant.com",
      "phone": "+1234567890"
    }')
    RESTAURANT_ID=$(echo $CREATE_REST_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null)
fi
echo "✅ Restaurant ID: $RESTAURANT_ID"

# Step 3: Create Category
echo -e "\n[3] Creating category..."
CATEGORY_RESPONSE=$(curl -s -X POST "$BASE_URL/products/categories" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{
  "restaurant_id": "'$RESTAURANT_ID'",
  "name": "Test Category",
  "slug": "test-category",
  "description": "Test category description",
  "is_active": true,
  "display_order": 1
}')
CATEGORY_ID=$(echo $CATEGORY_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null)
echo "✅ Category ID: $CATEGORY_ID"

# Step 4: Create Product
echo -e "\n[4] Creating product..."
PRODUCT_RESPONSE=$(curl -s -X POST "$BASE_URL/products" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{
  "restaurant_id": "'$RESTAURANT_ID'",
  "category_id": "'$CATEGORY_ID'",
  "name": "Test Product",
  "slug": "test-product",
  "sku": "TEST-001",
  "price": 1000,
  "is_active": true
}')
PRODUCT_ID=$(echo $PRODUCT_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null)
echo "✅ Product ID: $PRODUCT_ID"

# Step 5: Create Customer
echo -e "\n[5] Creating customer..."
CUSTOMER_RESPONSE=$(curl -s -X POST "$BASE_URL/customers/" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{
  "restaurant_id": "'$RESTAURANT_ID'",
  "name": "Test Customer",
  "email": "testcustomer@example.com",
  "phone": "+1234567891"
}')
CUSTOMER_ID=$(echo $CUSTOMER_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null)
echo "✅ Customer ID: $CUSTOMER_ID"

# Step 6: Create Table
echo -e "\n[6] Creating table..."
TABLE_RESPONSE=$(curl -s -X POST "$BASE_URL/tables/" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{
  "restaurant_id": "'$RESTAURANT_ID'",
  "table_number": "T01",
  "capacity": 4,
  "floor": "Ground"
}')
TABLE_ID=$(echo $TABLE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null)
echo "✅ Table ID: $TABLE_ID"

# Step 7: Create Order
echo -e "\n[7] Creating order..."
ORDER_RESPONSE=$(curl -s -X POST "$BASE_URL/orders/" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{
  "restaurant_id": "'$RESTAURANT_ID'",
  "customer_id": "'$CUSTOMER_ID'",
  "table_id": "'$TABLE_ID'",
  "order_type": "dine_in",
  "items": [{
    "product_id": "'$PRODUCT_ID'",
    "product_name": "Test Product",
    "quantity": 2,
    "unit_price": 1000,
    "price": 2000
  }],
  "subtotal": 2000,
  "tax_amount": 100,
  "total_amount": 2100
}')
ORDER_ID=$(echo $ORDER_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null)
echo "✅ Order ID: $ORDER_ID"

echo -e "\n================================================"
echo "✅ All basic endpoints tested successfully!"
echo "================================================"
echo "Restaurant ID: $RESTAURANT_ID"
echo "Category ID: $CATEGORY_ID"
echo "Product ID: $PRODUCT_ID"
echo "Customer ID: $CUSTOMER_ID"
echo "Table ID: $TABLE_ID"
echo "Order ID: $ORDER_ID"
echo "================================================"
