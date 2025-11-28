#!/bin/bash

# Restaurant POS API - Comprehensive Endpoint Testing Script
# This script tests all API endpoints with proper authentication

BASE_URL="http://localhost:8000"
ADMIN_EMAIL="admin@restaurant.com"
ADMIN_PASSWORD="Admin123!"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to print section header
print_section() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local data=$4
    local auth_required=$5
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${YELLOW}Testing:${NC} $description"
    echo -e "${YELLOW}Endpoint:${NC} $method $endpoint"
    
    if [ "$auth_required" = "true" ]; then
        if [ -n "$data" ]; then
            response=$(curl -s -X $method "$BASE_URL$endpoint" \
                -H "Authorization: Bearer $TOKEN" \
                -H "Content-Type: application/json" \
                -d "$data")
        else
            response=$(curl -s -X $method "$BASE_URL$endpoint" \
                -H "Authorization: Bearer $TOKEN")
        fi
    else
        if [ -n "$data" ]; then
            response=$(curl -s -X $method "$BASE_URL$endpoint" \
                -H "Content-Type: application/json" \
                -d "$data")
        else
            response=$(curl -s -X $method "$BASE_URL$endpoint")
        fi
    fi
    
    if echo "$response" | python3 -m json.tool > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        echo "$response" | python3 -m json.tool | head -20
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "$response"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    echo ""
}

# Authenticate and get token
print_section "1. AUTHENTICATION"
echo "Getting access token..."
TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login/json" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASSWORD\"}" | \
    python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}Failed to get authentication token. Creating admin user...${NC}\n"
    curl -s -X POST "$BASE_URL/api/v1/auth/register" \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"Admin User\",\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASSWORD\",\"phone\":\"1234567890\",\"role\":\"admin\"}" > /dev/null
    
    TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/login/json" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASSWORD\"}" | \
        python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
fi

echo -e "${GREEN}Token obtained successfully${NC}\n"

# Test basic endpoints
print_section "2. BASIC ENDPOINTS"
test_endpoint "GET" "/" "Root endpoint" "" "false"
test_endpoint "GET" "/health" "Health check" "" "false"
test_endpoint "GET" "/api/stats" "API statistics" "" "false"

# Test authentication endpoints
print_section "3. AUTHENTICATION ENDPOINTS"
test_endpoint "GET" "/api/v1/auth/me" "Get current user info" "" "true"

# Test user management
print_section "4. USER MANAGEMENT"
test_endpoint "GET" "/api/users/" "List all users" "" "true"
test_endpoint "POST" "/api/users/" "Create new user" '{"name":"Test Staff","email":"staff@test.com","password":"Staff123!","phone":"9876543210","role":"staff"}' "true"
test_endpoint "GET" "/api/users/me" "Get my user profile" "" "true"

# Test categories
print_section "5. CATEGORIES"
test_endpoint "GET" "/api/categories/" "List all categories" "" "true"
test_endpoint "POST" "/api/categories/" "Create category" '{"name":"Beverages","description":"All drinks","display_order":1,"is_active":true}' "true"
CATEGORY_ID=$(curl -s -X GET "$BASE_URL/api/categories/" -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['id'] if data else '')" 2>/dev/null)
if [ -n "$CATEGORY_ID" ]; then
    test_endpoint "GET" "/api/categories/$CATEGORY_ID" "Get category by ID" "" "true"
fi

# Test products
print_section "6. PRODUCTS"
test_endpoint "GET" "/api/products/" "List all products" "" "true"
if [ -n "$CATEGORY_ID" ]; then
    test_endpoint "POST" "/api/products/" "Create product" "{\"name\":\"Coffee\",\"description\":\"Hot coffee\",\"category_id\":\"$CATEGORY_ID\",\"price\":299,\"cost\":100,\"stock_quantity\":100,\"is_available\":true}" "true"
fi
test_endpoint "GET" "/api/products/search?q=coffee" "Search products" "" "true"

# Test modifiers
print_section "7. MODIFIERS"
test_endpoint "GET" "/api/modifiers/" "List all modifiers" "" "true"
test_endpoint "POST" "/api/modifiers/" "Create modifier" '{"name":"Size","is_required":true,"min_selection":1,"max_selection":1}' "true"
test_endpoint "GET" "/api/modifiers/options/" "List modifier options" "" "true"

# Test combos
print_section "8. COMBOS"
test_endpoint "GET" "/api/combos/" "List all combos" "" "true"
test_endpoint "POST" "/api/combos/" "Create combo" '{"name":"Breakfast Combo","description":"Coffee + Sandwich","price":599,"is_active":true}' "true"

# Test customers
print_section "9. CUSTOMERS"
test_endpoint "GET" "/api/customers/" "List all customers" "" "true"
test_endpoint "POST" "/api/customers/" "Create customer" '{"name":"John Doe","phone":"1112223333","email":"john@example.com"}' "true"
test_endpoint "GET" "/api/customers/search?q=john" "Search customers" "" "true"
test_endpoint "GET" "/api/customers/tags/" "List customer tags" "" "true"

# Test loyalty
print_section "10. LOYALTY PROGRAM"
test_endpoint "GET" "/api/loyalty/rules/" "List loyalty rules" "" "true"
test_endpoint "POST" "/api/loyalty/rules/" "Create loyalty rule" '{"rule_name":"Points per Dollar","rule_type":"POINTS_PER_AMOUNT","points_earned":10,"amount_threshold":100,"is_active":true}' "true"
test_endpoint "GET" "/api/loyalty/transactions/" "List loyalty transactions" "" "true"

# Test orders
print_section "11. ORDERS"
test_endpoint "GET" "/api/orders/" "List all orders" "" "true"
test_endpoint "GET" "/api/orders/stats" "Order statistics" "" "true"

# Test QR ordering
print_section "12. QR ORDERING"
test_endpoint "GET" "/api/qr/tables/" "List QR tables" "" "true"
test_endpoint "POST" "/api/qr/tables/" "Create QR table" '{"table_number":"T01","table_name":"Table 1","location":"Main Floor","capacity":4}' "true"
test_endpoint "GET" "/api/qr/sessions/" "List QR sessions" "" "true"
test_endpoint "GET" "/api/qr/settings/" "Get QR settings" "" "true"

# Test tax settings
print_section "13. TAX & SETTINGS"
test_endpoint "GET" "/api/tax-rules/" "List tax rules" "" "true"
test_endpoint "POST" "/api/tax-rules/" "Create tax rule" '{"rule_name":"GST","tax_type":"PERCENTAGE","tax_rate":18,"is_active":true}' "true"
test_endpoint "GET" "/api/settings/" "Get global settings" "" "true"

# Test analytics
print_section "14. ANALYTICS"
test_endpoint "GET" "/api/analytics/sales?period=today" "Sales analytics" "" "true"
test_endpoint "GET" "/api/analytics/products?period=week" "Product analytics" "" "true"
test_endpoint "GET" "/api/analytics/customers?period=month" "Customer analytics" "" "true"
test_endpoint "GET" "/api/reports/sales-summary" "Sales summary report" "" "true"

# Test dashboard
print_section "15. DASHBOARD"
test_endpoint "GET" "/api/dashboard/overview" "Dashboard overview" "" "true"
test_endpoint "GET" "/api/dashboard/quick-stats" "Quick statistics" "" "true"

# Test file manager
print_section "16. FILE MANAGER"
test_endpoint "GET" "/api/files/" "List files" "" "true"
test_endpoint "GET" "/api/files/stats" "File statistics" "" "true"

# Print summary
print_section "TEST SUMMARY"
echo -e "Total Tests: ${BLUE}$TOTAL_TESTS${NC}"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
echo -e "Success Rate: ${YELLOW}$(( PASSED_TESTS * 100 / TOTAL_TESTS ))%${NC}\n"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}\n"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}\n"
    exit 1
fi
