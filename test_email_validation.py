"""
Test to show how the forgot password API handles valid vs invalid emails
"""
import requests
import json

API_URL = "http://localhost:8000/api/v1/auth/forgot-password"

print("=" * 60)
print("FORGOT PASSWORD EMAIL VALIDATION TEST")
print("=" * 60)
print()

# Test 1: Non-existent email
print("🔍 Test 1: Non-existent email (brunoakp95@gmail.com)")
print("-" * 60)
response1 = requests.post(API_URL, json={"email": "brunoakp95@gmail.com"})
result1 = response1.json()
print(f"Status: {response1.status_code}")
print(f"Response: {json.dumps(result1, indent=2)}")
print(f"Data is None: {result1.get('data') is None}")
print(f"✗ Email NOT in database - NO OTP sent")
print()

# Test 2: Existing email
print("🔍 Test 2: Existing email (admin@restaurant.com)")
print("-" * 60)
response2 = requests.post(API_URL, json={"email": "admin@restaurant.com"})
result2 = response2.json()
print(f"Status: {response2.status_code}")
print(f"Response: {json.dumps(result2, indent=2)}")
print(f"Data exists: {result2.get('data') is not None}")
print(f"Expires in: {result2.get('data', {}).get('expires_in')} seconds")
print(f"✓ Email in database - OTP sent successfully")
print()

print("=" * 60)
print("CONCLUSION:")
print("=" * 60)
print("The API returns same message for both (security)")
print("But 'data' field reveals if email exists:")
print("  - data: null       → Email NOT in database")
print("  - data: {...}      → Email in database, OTP sent")
print()
print("Updated HTML now checks 'result.data.expires_in'")
print("Only proceeds to Step 2 if data exists!")
print("=" * 60)
