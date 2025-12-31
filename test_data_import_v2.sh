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
curl -s -X POST "http://localhost:8000/api/v1/data-import/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test_categories.csv" \
  -F "import_name=Test Category Import" \
  -F "import_type=category" \
  -F "restaurant_id=$REST_ID" \
  -F "skip_duplicates=true" \
  -F "update_existing=false" \
  -F "validate_only=false" | python3 -m json.tool

echo ""
echo "[2] Testing Product Import from CSV..."
curl -s -X POST "http://localhost:8000/api/v1/data-import/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test_products.csv" \
  -F "import_name=Test Product Import" \
  -F "import_type=product" \
  -F "restaurant_id=$REST_ID" \
  -F "skip_duplicates=true" \
  -F "update_existing=false" \
  -F "validate_only=false" | python3 -m json.tool

echo ""
echo "[3] Get Import History..."
curl -s "http://localhost:8000/api/v1/data-import/imports?restaurant_id=$REST_ID&page=1&limit=5" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "[4] Download Category Template..."
curl -s "http://localhost:8000/api/v1/data-import/templates/category?format=csv" \
  -H "Authorization: Bearer $TOKEN" -o /tmp/category_template_new.csv
if [ -f /tmp/category_template_new.csv ]; then
  SIZE=$(stat -f%z /tmp/category_template_new.csv 2>/dev/null || stat -c%s /tmp/category_template_new.csv 2>/dev/null)
  if [ "$SIZE" -gt 100 ]; then
    echo "✅ Category template downloaded successfully ($SIZE bytes)"
    head -3 /tmp/category_template_new.csv
  else
    echo "❌ Template download failed or empty"
    cat /tmp/category_template_new.csv
  fi
else
  echo "❌ Template file not created"
fi

echo ""
echo "[5] Download Product Template..."
curl -s "http://localhost:8000/api/v1/data-import/templates/product?format=csv" \
  -H "Authorization: Bearer $TOKEN" -o /tmp/product_template_new.csv
if [ -f /tmp/product_template_new.csv ]; then
  SIZE=$(stat -f%z /tmp/product_template_new.csv 2>/dev/null || stat -c%s /tmp/product_template_new.csv 2>/dev/null)
  if [ "$SIZE" -gt 100 ]; then
    echo "✅ Product template downloaded successfully ($SIZE bytes)"
    head -3 /tmp/product_template_new.csv
  else
    echo "❌ Template download failed or empty"
    cat /tmp/product_template_new.csv
  fi
else
  echo "❌ Template file not created"
fi

echo ""
echo "================================================"
echo "Data Import Module Testing Complete"
echo "================================================"
