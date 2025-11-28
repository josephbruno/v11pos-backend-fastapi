#!/bin/bash
# Test script to verify all endpoints return standardized response format
# Format: {"status": "success", "message": "...", "data": {...}}

BASE_URL="http://localhost:8000"

echo "==========================================="
echo "Testing Standardized API Response Format"
echo "==========================================="
echo ""

# Function to check response format
check_response() {
    local response="$1"
    local test_name="$2"
    
    # Check if response has "status" field
    if echo "$response" | python3 -c "import sys, json; d=json.load(sys.stdin); sys.exit(0 if 'status' in d else 1)" 2>/dev/null; then
        # Check if response has "message" field
        if echo "$response" | python3 -c "import sys, json; d=json.load(sys.stdin); sys.exit(0 if 'message' in d else 1)" 2>/dev/null; then
            # Check if response has "data" field
            if echo "$response" | python3 -c "import sys, json; d=json.load(sys.stdin); sys.exit(0 if 'data' in d else 1)" 2>/dev/null; then
                echo "✅ $test_name - Format is correct"
                return 0
            fi
        fi
    fi
    echo "❌ $test_name - Format is incorrect"
    echo "Response: $response" | head -5
    return 1
}

# Test 1: Root endpoint
echo "Test 1: Root Endpoint (GET /)"
RESPONSE=$(curl -s "$BASE_URL/")
check_response "$RESPONSE" "Root endpoint"
echo "$RESPONSE" | python3 -m json.tool | head -15
echo ""

# Test 2: Health check
echo "Test 2: Health Check (GET /health)"
RESPONSE=$(curl -s "$BASE_URL/health")
check_response "$RESPONSE" "Health check"
echo "$RESPONSE" | python3 -m json.tool
echo ""

# Test 3: API Stats
echo "Test 3: API Stats (GET /api/stats)"
RESPONSE=$(curl -s "$BASE_URL/api/stats")
check_response "$RESPONSE" "API stats"
echo "$RESPONSE" | python3 -m json.tool | head -20
echo ""

# Test 4: Login
echo "Test 4: Login (POST /api/v1/auth/login/json)"
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login/json" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@restaurant.com","password":"Admin123!"}')
check_response "$RESPONSE" "Login"

# Extract token
TOKEN=$(echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('data', {}).get('access_token', ''))" 2>/dev/null)
echo "Token extracted: ${TOKEN:0:50}..."
echo ""

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get token. Stopping tests."
    exit 1
fi

# Test 5: Get current user
echo "Test 5: Get Current User (GET /api/v1/auth/me)"
RESPONSE=$(curl -s "$BASE_URL/api/v1/auth/me" -H "Authorization: Bearer $TOKEN")
check_response "$RESPONSE" "Get current user"
echo "$RESPONSE" | python3 -m json.tool | head -15
echo ""

# Test 6: List categories
echo "Test 6: List Categories (GET /api/v1/categories/)"
RESPONSE=$(curl -s "$BASE_URL/api/v1/categories/" -H "Authorization: Bearer $TOKEN")
check_response "$RESPONSE" "List categories"
echo "$RESPONSE" | python3 -m json.tool | head -20
echo ""

# Test 7: Create category
echo "Test 7: Create Category (POST /api/v1/categories/)"
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/categories/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Category","slug":"test-category","description":"Testing standard response","sort_order":1,"active":true}')
check_response "$RESPONSE" "Create category"
echo "$RESPONSE" | python3 -m json.tool | head -20
echo ""

# Test 8: List customers
echo "Test 8: List Customers (GET /api/v1/customers/)"
RESPONSE=$(curl -s "$BASE_URL/api/v1/customers/" -H "Authorization: Bearer $TOKEN")
check_response "$RESPONSE" "List customers"
echo "$RESPONSE" | python3 -m json.tool | head -20
echo ""

# Test 9: Logout
echo "Test 9: Logout (POST /api/v1/auth/logout)"
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/logout" -H "Authorization: Bearer $TOKEN")
check_response "$RESPONSE" "Logout"
echo "$RESPONSE" | python3 -m json.tool
echo ""

echo "==========================================="
echo "Test Summary"
echo "==========================================="
echo "All critical endpoints tested for standardized response format"
echo "Format: {status, message, data}"
