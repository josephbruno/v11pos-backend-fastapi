#!/bin/bash

# 🧪 Test API Endpoints on Production Server
# Base URL: https://apipos.v11tech.com

set -e

BASE_URL="https://apipos.v11tech.com"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Testing API Endpoints${NC}"
echo -e "${BLUE}   Base URL: ${BASE_URL}${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Test function
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local header=$4
    
    echo -e "${YELLOW}Testing:${NC} ${description}"
    echo -e "${BLUE}  ${method} ${BASE_URL}${endpoint}${NC}"
    
    if [ -z "$header" ]; then
        response=$(curl -s -X ${method} "${BASE_URL}${endpoint}")
    else
        response=$(curl -s -X ${method} -H "${header}" "${BASE_URL}${endpoint}")
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}  ✓ Success${NC}"
        echo "$response" | jq '.' 2>/dev/null | head -n 10 || echo "$response" | head -c 200
    else
        echo -e "${RED}  ✗ Failed${NC}"
    fi
    echo ""
}

# Root endpoint
echo -e "${GREEN}[1] Testing Root Endpoint${NC}"
test_endpoint "GET" "/" "API Root"

# Products endpoints
echo -e "${GREEN}[2] Testing Products API${NC}"
test_endpoint "GET" "/api/v1/products/" "List all products"
test_endpoint "GET" "/api/v1/products/" "List products in Spanish" "Accept-Language: es"
test_endpoint "GET" "/api/v1/products/" "List products in French" "Accept-Language: fr"

# Categories endpoints
echo -e "${GREEN}[3] Testing Categories API${NC}"
test_endpoint "GET" "/api/v1/categories/" "List all categories"
test_endpoint "GET" "/api/v1/categories/" "List categories in Spanish" "Accept-Language: es"

# Modifiers endpoints
echo -e "${GREEN}[4] Testing Modifiers API${NC}"
test_endpoint "GET" "/api/v1/modifiers/" "List all modifiers"
test_endpoint "GET" "/api/v1/modifiers/" "List modifiers in Spanish" "Accept-Language: es"

# Combos endpoints
echo -e "${GREEN}[5] Testing Combos API${NC}"
test_endpoint "GET" "/api/v1/combos" "List all combos"
test_endpoint "GET" "/api/v1/combos" "List combos in French" "Accept-Language: fr"

# Translation endpoints
echo -e "${GREEN}[6] Testing Translation API${NC}"
test_endpoint "GET" "/api/v1/translations/languages" "List supported languages"
test_endpoint "GET" "/api/v1/translations/en" "Get English translations"
test_endpoint "GET" "/api/v1/translations/es" "Get Spanish translations"

# API Documentation
echo -e "${GREEN}[7] Testing API Documentation${NC}"
echo -e "${YELLOW}Swagger UI:${NC} ${BASE_URL}/docs"
echo -e "${YELLOW}ReDoc:${NC} ${BASE_URL}/redoc"

# Image uploads test
echo -e "${GREEN}[8] Testing Image Access${NC}"
echo -e "${YELLOW}Sample category image:${NC}"
curl -I "${BASE_URL}/uploads/categories/beverages.jpg" 2>&1 | grep "HTTP"
echo -e "${YELLOW}Sample product image:${NC}"
curl -I "${BASE_URL}/uploads/products/coca-cola.jpg" 2>&1 | grep "HTTP"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}   Testing Complete! ✓${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}API Documentation URLs:${NC}"
echo -e "  Swagger: ${GREEN}${BASE_URL}/docs${NC}"
echo -e "  ReDoc: ${GREEN}${BASE_URL}/redoc${NC}"
echo ""
