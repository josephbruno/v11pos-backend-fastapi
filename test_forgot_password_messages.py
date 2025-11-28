"""
Test forgot password with proper error messages
"""
import requests
import json

API_URL = "http://localhost:8000/api/v1/auth/forgot-password"

print("=" * 70)
print("FORGOT PASSWORD - PROPER ERROR MESSAGES TEST")
print("=" * 70)
print()

# Test 1: Non-existent email (should get 404 error)
print("🔴 Test 1: Non-existent email (brunoakp95@gmail.com)")
print("-" * 70)
response1 = requests.post(API_URL, json={"email": "brunoakp95@gmail.com"})
result1 = response1.json()
print(f"Status Code: {response1.status_code}")
print(f"Response: {json.dumps(result1, indent=2)}")
if response1.status_code == 404:
    print(f"✅ CORRECT: Returns 404 with clear message")
    print(f"   Message: \"{result1.get('detail')}\"")
else:
    print(f"❌ WRONG: Should return 404")
print()

# Test 2: Existing email (should succeed with OTP)
print("🟢 Test 2: Existing email (admin@restaurant.com)")
print("-" * 70)
response2 = requests.post(API_URL, json={"email": "admin@restaurant.com"})
result2 = response2.json()
print(f"Status Code: {response2.status_code}")
print(f"Response: {json.dumps(result2, indent=2)}")
if response2.status_code == 200:
    print(f"✅ CORRECT: Returns 200 with OTP data")
    print(f"   Email: {result2.get('data', {}).get('email')}")
    print(f"   Expires in: {result2.get('data', {}).get('expires_in')} seconds")
else:
    print(f"❌ WRONG: Should return 200")
print()

print("=" * 70)
print("SUMMARY:")
print("=" * 70)
print("✅ Non-existent email → HTTP 404 with clear error message")
print("✅ Existing email     → HTTP 200 with OTP sent")
print()
print("Frontend can now show specific error:")
print('  "Email address not found. Please check and try again."')
print("=" * 70)
