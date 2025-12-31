#!/bin/bash

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyZjNiYWM3Yi00YjVjLTQyYTUtOGJlZS01MmM3NmU4OWIwOWIiLCJleHAiOjE3NjcxNzc1NDYsInR5cGUiOiJhY2Nlc3MifQ.504cMNDzVC6kluV-ev9nqZ6RV0bSU-FFy3q3OMj8zfc"
REST1="f87ec860-f5ca-40a5-9fb6-d2ee8e94f3b9"
REST2="bbda4879-9357-42b0-b49a-47877512c502"
CAT_ID="6606e491-a293-45ef-9005-a868bb4150ef"
PROD_ID="669f8d4f-b6df-4957-bbe1-926f8fc2a13f"

echo "================================================"
echo "Data Copy Module Testing"
echo "================================================"
echo ""

echo "[1] Testing Category Copy..."
curl -s -X POST "http://localhost:8000/api/v1/data-copy/categories" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_restaurant_id": "'$REST1'",
    "target_restaurant_id": "'$REST2'",
    "category_ids": ["'$CAT_ID'"]
  }' | python3 -m json.tool

echo ""
echo "[2] Testing Product Copy..."
curl -s -X POST "http://localhost:8000/api/v1/data-copy/products" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_restaurant_id": "'$REST1'",
    "target_restaurant_id": "'$REST2'",
    "product_ids": ["'$PROD_ID'"],
    "copy_category": true
  }' | python3 -m json.tool

echo ""
echo "[3] Testing Bulk Copy..."
curl -s -X POST "http://localhost:8000/api/v1/data-copy/bulk" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_restaurant_id": "'$REST1'",
    "target_restaurant_id": "'$REST2'",
    "copy_categories": true,
    "copy_products": true,
    "category_ids": ["'$CAT_ID'"],
    "product_ids": ["'$PROD_ID'"]
  }' | python3 -m json.tool

echo ""
echo "================================================"
echo "Data Copy Module Testing Complete"
echo "================================================"
