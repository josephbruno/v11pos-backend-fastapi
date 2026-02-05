#!/bin/bash

# Test script for login endpoint with both JSON and form-encoded data

BASE_URL="http://localhost:8000/api/v1"

echo "=========================================="
echo "POS Backend API - Login Endpoint Tests"
echo "=========================================="
echo "Base URL: $BASE_URL"
echo ""

# Test 1: JSON Login
echo "=========================================="
echo "TEST 1: Login with JSON payload"
echo "=========================================="
echo "Request:"
echo "  URL: $BASE_URL/auth/login"
echo "  Content-Type: application/json"
echo "  Body: {\"email\": \"superadmin@restaurant.com\", \"password\": \"Super@123\"}"
echo ""
echo "Response:"
curl -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "superadmin@restaurant.com", "password": "Super@123"}' \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | jq '.'
echo ""

# Test 2: Form-Encoded Login
echo "=========================================="
echo "TEST 2: Login with Form-Encoded payload"
echo "=========================================="
echo "Request:"
echo "  URL: $BASE_URL/auth/login"
echo "  Content-Type: application/x-www-form-urlencoded"
echo "  Body: email=superadmin@restaurant.com&password=Super@123"
echo ""
echo "Response:"
curl -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=superadmin@restaurant.com&password=Super@123" \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | jq '.'
echo ""

# Test 3: Get access token and test authenticated endpoint
echo "=========================================="
echo "TEST 3: Testing Authenticated Endpoint"
echo "=========================================="
echo "Getting access token..."
ACCESS_TOKEN=$(curl -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "superadmin@restaurant.com", "password": "Super@123"}' \
  -s | jq -r '.data.access_token')

if [ "$ACCESS_TOKEN" != "null" ] && [ -n "$ACCESS_TOKEN" ]; then
  echo "Access Token: ${ACCESS_TOKEN:0:50}..."
  echo ""
  echo "Testing /users/me endpoint:"
  curl -X GET "$BASE_URL/users/me" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -w "\nHTTP Status: %{http_code}\n" \
    -s | jq '.'
else
  echo "Failed to get access token"
fi
echo ""

# Test 4: Error Response Format
echo "=========================================="
echo "TEST 4: Error Response Format"
echo "=========================================="
echo "Testing with invalid credentials..."
curl -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "invalid@test.com", "password": "wrongpassword"}' \
  -w "\nHTTP Status: %{http_code}\n" \
  -s | jq '.'
echo ""

echo "=========================================="
echo "All Tests Completed"
echo "=========================================="
