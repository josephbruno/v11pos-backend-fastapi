#!/bin/bash

echo "🧪 Testing Category Image Upload API"
echo "========================================"
echo ""

cd /home/brunodoss/docs/pos/pos/pos-fastapi

# Get authentication token
echo "🔐 Getting authentication token..."
TOKEN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testadmin@pos.com&password=admin123")

TOKEN=$(echo $TOKEN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get authentication token"
    echo "Response: $TOKEN_RESPONSE"
    exit 1
fi

echo "✅ Token obtained successfully"
echo ""

# Test 1: Create category WITHOUT image
echo "📝 TEST 1: Create category WITHOUT image"
echo "=========================================="
curl -s -X POST "http://localhost:8000/api/v1/categories/" \
  -H "Authorization: Bearer $TOKEN" \
  -F "name=Smoothies" \
  -F "slug=smoothies-test" \
  -F "description=Fresh smoothies - no image" \
  -F "active=true" \
  -F "sort_order=30" | python3 -m json.tool

echo ""
echo ""

# Test 2: Create category WITH image
echo "📝 TEST 2: Create category WITH image"
echo "======================================="

# Find an image file
IMAGE_FILE=$(ls uploads/products/*.jpg 2>/dev/null | head -1)

if [ -f "$IMAGE_FILE" ]; then
    echo "Using image: $(basename $IMAGE_FILE)"
    echo ""
    
    curl -s -X POST "http://localhost:8000/api/v1/categories/" \
      -H "Authorization: Bearer $TOKEN" \
      -F "name=Sandwiches" \
      -F "slug=sandwiches-test" \
      -F "description=Delicious sandwiches with image" \
      -F "active=true" \
      -F "sort_order=40" \
      -F "image=@$IMAGE_FILE" | python3 -m json.tool
    
    echo ""
    echo ""
    echo "📂 Contents of uploads/categories/:"
    ls -lh uploads/categories/ 2>/dev/null || echo "Directory empty or doesn't exist"
else
    echo "❌ No image file found for testing"
fi

echo ""
echo "✅ Tests completed!"
