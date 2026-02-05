#!/usr/bin/env python3
"""
Test script for login endpoint with both JSON and form-encoded data
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_login_json():
    """Test login with JSON payload"""
    print("\n" + "="*60)
    print("TEST 1: Login with JSON payload")
    print("="*60)
    
    url = f"{BASE_URL}/auth/login"
    headers = {"Content-Type": "application/json"}
    payload = {
        "email": "superadmin@restaurant.com",
        "password": "Super@123"
    }
    
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("\n✅ JSON Login Test: PASSED")
                return data.get("data", {}).get("access_token")
            else:
                print("\n❌ JSON Login Test: FAILED - Not successful")
        else:
            print("\n❌ JSON Login Test: FAILED - Wrong status code")
    except Exception as e:
        print(f"\n❌ JSON Login Test: FAILED - {str(e)}")
    
    return None


def test_login_form():
    """Test login with form-encoded payload"""
    print("\n" + "="*60)
    print("TEST 2: Login with Form-Encoded payload")
    print("="*60)
    
    url = f"{BASE_URL}/auth/login"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {
        "email": "superadmin@restaurant.com",
        "password": "Super@123"
    }
    
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {payload}")
    
    try:
        response = requests.post(url, data=payload, headers=headers)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("\n✅ Form Login Test: PASSED")
                return data.get("data", {}).get("access_token")
            else:
                print("\n❌ Form Login Test: FAILED - Not successful")
        else:
            print("\n❌ Form Login Test: FAILED - Wrong status code")
    except Exception as e:
        print(f"\n❌ Form Login Test: FAILED - {str(e)}")
    
    return None


def test_authenticated_endpoint(access_token):
    """Test an authenticated endpoint with the token"""
    if not access_token:
        print("\n⚠️  Skipping authenticated endpoint test - no token available")
        return
    
    print("\n" + "="*60)
    print("TEST 3: Authenticated Endpoint (/users/me)")
    print("="*60)
    
    url = f"{BASE_URL}/users/me"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print(f"URL: {url}")
    print(f"Headers: Authorization: Bearer {access_token[:20]}...")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("\n✅ Authenticated Endpoint Test: PASSED")
            else:
                print("\n❌ Authenticated Endpoint Test: FAILED - Not successful")
        else:
            print("\n❌ Authenticated Endpoint Test: FAILED - Wrong status code")
    except Exception as e:
        print(f"\n❌ Authenticated Endpoint Test: FAILED - {str(e)}")


def test_response_format():
    """Test that all responses follow the standard format"""
    print("\n" + "="*60)
    print("TEST 4: Response Format Validation")
    print("="*60)
    
    url = f"{BASE_URL}/auth/login"
    payload = {
        "email": "invalid@test.com",
        "password": "wrongpassword"
    }
    
    print("Testing error response format...")
    
    try:
        response = requests.post(url, json=payload)
        data = response.json()
        
        required_fields = ["success", "status_code", "message", "data", "error", "timestamp"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"\n❌ Response Format Test: FAILED - Missing fields: {missing_fields}")
        else:
            print(f"\n✅ Response Format Test: PASSED")
            print(f"   - All required fields present: {required_fields}")
            print(f"   - success: {data['success']}")
            print(f"   - status_code: {data['status_code']}")
            print(f"   - message: {data['message']}")
            print(f"   - error.code: {data.get('error', {}).get('code')}")
    except Exception as e:
        print(f"\n❌ Response Format Test: FAILED - {str(e)}")


def main():
    print("\n" + "="*60)
    print("POS Backend API - Login Endpoint Tests")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    
    # Test 1: JSON login
    token_json = test_login_json()
    
    # Test 2: Form-encoded login
    token_form = test_login_form()
    
    # Test 3: Use token from JSON login
    test_authenticated_endpoint(token_json)
    
    # Test 4: Response format validation
    test_response_format()
    
    print("\n" + "="*60)
    print("All Tests Completed")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
