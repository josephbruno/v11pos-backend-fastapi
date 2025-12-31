#!/bin/bash

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyZjNiYWM3Yi00YjVjLTQyYTUtOGJlZS01MmM3NmU4OWIwOWIiLCJleHAiOjE3NjcxNzc1NDYsInR5cGUiOiJhY2Nlc3MifQ.504cMNDzVC6kluV-ev9nqZ6RV0bSU-FFy3q3OMj8zfc"
REST_ID="f87ec860-f5ca-40a5-9fb6-d2ee8e94f3b9"

echo "================================================"
echo "Data Import Module Testing"
echo "================================================"
echo "Restaurant ID: $REST_ID"
echo "================================================"
echo ""

echo "[1] Testing Category Import from CSV..."
curl -s -X POST "http://localhost:8000/api/v1/data-import/categories/import" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test_categories.csv" \
  -F "restaurant_id=$REST_ID" \
  -F "skip_duplicates=true" \
  -F "update_existing=false" | python3 -m json.tool

echo ""
echo "[2] Testing Product Import from CSV..."
curl -s -X POST "http://localhost:8000/api/v1/data-import/products/import" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test_products.csv" \
  -F "restaurant_id=$REST_ID" \
  -F "skip_duplicates=true" \
  -F "update_existing=false" \
  -F "create_missing_categories=true" | python3 -m json.tool

echo ""
echo "[3] Get Import History..."
curl -s "http://localhost:8000/api/v1/data-import/history?restaurant_id=$REST_ID&limit=5" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "[4] Get Import Statistics..."
curl -s "http://localhost:8000/api/v1/data-import/statistics?restaurant_id=$REST_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "[5] Download Category Template..."
curl -s "http://localhost:8000/api/v1/data-import/templates/category?format=csv" \
  -H "Authorization: Bearer $TOKEN" -o /tmp/category_template.csv
if [ -f /tmp/category_template.csv ]; then
  echo "✅ Category template downloaded successfully"
  head -3 /tmp/category_template.csv
else
  echo "❌ Template download failed"
fi

echo ""
echo "[6] Download Product Template..."
curl -s "http://localhost:8000/api/v1/data-import/templates/product?format=csv" \
  -H "Authorization: Bearer $TOKEN" -o /tmp/product_template.csv
if [ -f /tmp/product_template.csv ]; then
  echo "✅ Product template downloaded successfully"
  head -3 /tmp/product_template.csv
else
  echo "❌ Template download failed"
fi

echo ""
echo "================================================"
echo "Data Import Module Testing Complete"
echo "================================================"
