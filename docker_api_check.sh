#!/usr/bin/env bash
# Verify POS billing / reports APIs against the running Docker stack.
set -euo pipefail

BASE="${BASE_URL:-http://localhost:8000/api/v1}"
EMAIL="${API_EMAIL:-superadmin@restaurant.com}"
PASSWORD="${API_PASSWORD:-Admin@123}"

echo "==> Login ($EMAIL)"
TOKEN=$(curl -sf -X POST "$BASE/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

RID=$(curl -sf "$BASE/restaurants/all?skip=0&limit=1" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d[0]['id'] if isinstance(d,list) else d['restaurants'][0]['id'])")

echo "==> Restaurant: $RID"

echo "==> Unit tests in container"
docker compose exec -T fastapi python test_cashier_reports.py

echo "==> Order statistics aliases"
curl -sf "$BASE/orders/restaurant/$RID/statistics" -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; assert 'avg_order_value' in d and 'delivered_orders' in d; print('OK', d['avg_order_value'], d['delivered_orders'])"

echo "==> Sales reports (live monthly)"
curl -sf "$BASE/reports/sales?restaurant_id=$RID&period_type=monthly&skip=0&limit=2" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); rows=d['data']; assert isinstance(rows,list) and rows[0].get('total_revenue') is not None; print('OK rows', len(rows))"

echo "==> Item reports"
curl -sf "$BASE/reports/items?restaurant_id=$RID&skip=0&limit=5" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); assert isinstance(d['data'], list); print('OK count', len(d['data']))"

echo "==> Restaurant dashboard"
curl -sf "$BASE/reports/dashboard/restaurant/$RID?period=30d" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; assert 'order_statistics' in d; print('OK keys', list(d.keys()))"

echo "==> All Docker API checks passed"
