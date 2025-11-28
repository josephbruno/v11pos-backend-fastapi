#!/usr/bin/env python
"""Test registration endpoint"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_register():
    """Test user registration"""
    print("Testing user registration...")
    print("-" * 50)
    
    # Test data
    user_data = {
        "name": "Test User",
        "email": "testuser@pos.com",
        "phone": "9876543210",
        "password": "TestPassword123",
        "role": "STAFF"
    }
    
    # Register user
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json=user_data
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("\n[OK] Registration successful!")
        return response.json()
    else:
        print(f"\n[ERROR] Registration failed!")
        return None

def test_login(email, password):
    """Test user login"""
    print("\nTesting user login...")
    print("-" * 50)
    
    login_data = {
        "email": email,
        "password": password
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login/json",
        json=login_data
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("\n[OK] Login successful!")
        return response.json()
    else:
        print(f"\n[ERROR] Login failed!")
        return None

if __name__ == "__main__":
    print("\n" + "="*50)
    print("RESTAURANTPOS API - AUTHENTICATION TEST")
    print("="*50 + "\n")
    
    # Test registration
    result = test_register()
    
    if result:
        # Test login
        test_login("testuser@pos.com", "TestPassword123")
    
    print("\n" + "="*50)
    print("Test completed!")
    print("="*50 + "\n")
