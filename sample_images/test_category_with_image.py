#!/usr/bin/env python3
"""
Test script to create and update categories with images
"""
import requests
from pathlib import Path

API_BASE = "http://localhost:8000/api/v1/categories"

def login():
    """Try to login and get token"""
    # Try multiple possible credentials
    credentials = [
        ("testadmin@pos.com", "admin123"),
        ("admin@restaurant.com", "admin123"),
        ("admin@pos.com", "admin123"),
    ]
    
    for email, password in credentials:
        try:
            response = requests.post(
                "http://localhost:8000/api/v1/auth/login",
                data={"username": email, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Login successful with {email}")
                return data.get('access_token')
            else:
                print(f"✗ Failed with {email}: {response.text}")
        except Exception as e:
            print(f"✗ Error with {email}: {e}")
    
    return None

def list_categories(token=None):
    """List existing categories"""
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    try:
        response = requests.get(f"{API_BASE}/", params={"page": 1, "page_size": 10}, headers=headers)
        print(f"\nList Categories Response: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            categories = data.get('data', [])
            print(f"Found {len(categories)} categories:")
            for cat in categories:
                print(f"  - ID: {cat['id']}, Name: {cat['name']}, Image: {cat.get('image', 'None')}")
            return categories
        else:
            print(f"Error: {response.text}")
            return []
    except Exception as e:
        print(f"Error listing categories: {e}")
        return []

def create_category_with_image(token=None):
    """Create a new category with image"""
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    # Prepare form data
    data = {
        'name': 'Sample Appetizers',
        'slug': 'sample-appetizers',
        'description': 'Delicious appetizers to start your meal',
        'active': 'true',
        'sort_order': '1'
    }
    
    # Open image file
    image_path = Path(__file__).parent / 'appetizers.jpg'
    if not image_path.exists():
        print(f"Error: Image not found at {image_path}")
        return None
    
    try:
        with open(image_path, 'rb') as img_file:
            files = {'image': ('appetizers.jpg', img_file, 'image/jpeg')}
            
            response = requests.post(f"{API_BASE}/", data=data, files=files, headers=headers)
            print(f"\nCreate Category Response: {response.status_code}")
            if response.status_code in [200, 201]:
                result = response.json()
                category = result.get('data', {})
                print(f"✓ Category created successfully!")
                print(f"  ID: {category.get('id')}")
                print(f"  Name: {category.get('name')}")
                print(f"  Image: {category.get('image')}")
                if category.get('image'):
                    print(f"  Full URL: http://localhost:8000/uploads/{category.get('image')}")
                return category
            else:
                print(f"✗ Error: {response.text}")
                return None
    except Exception as e:
        print(f"Error creating category: {e}")
        return None

def update_category_with_image(category_id, token=None):
    """Update existing category with a different image"""
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    data = {
        'name': 'Updated Desserts Category',
        'description': 'Sweet treats and delicious desserts'
    }
    
    image_path = Path(__file__).parent / 'desserts.jpg'
    if not image_path.exists():
        print(f"Error: Image not found at {image_path}")
        return None
    
    try:
        with open(image_path, 'rb') as img_file:
            files = {'image': ('desserts.jpg', img_file, 'image/jpeg')}
            
            response = requests.put(f"{API_BASE}/{category_id}", data=data, files=files, headers=headers)
            print(f"\nUpdate Category Response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                category = result.get('data', {})
                print(f"✓ Category updated successfully!")
                print(f"  ID: {category.get('id')}")
                print(f"  Name: {category.get('name')}")
                print(f"  Image: {category.get('image')}")
                if category.get('image'):
                    print(f"  Full URL: http://localhost:8000/uploads/{category.get('image')}")
                return category
            else:
                print(f"✗ Error: {response.text}")
                return None
    except Exception as e:
        print(f"Error updating category: {e}")
        return None

def main():
    print("=" * 60)
    print("Category Image Upload Test")
    print("=" * 60)
    
    # Step 1: Try to login
    print("\n[1] Attempting to login...")
    token = login()
    
    if not token:
        print("\n⚠ Warning: Could not login, trying without authentication...")
    
    # Step 2: List existing categories
    print("\n[2] Listing existing categories...")
    categories = list_categories(token)
    
    # Step 3: Create new category with image
    print("\n[3] Creating new category with image...")
    new_category = create_category_with_image(token)
    
    # Step 4: Update category with different image (if we have one)
    if new_category and categories:
        print("\n[4] Updating first category with new image...")
        first_category_id = categories[0]['id']
        update_category_with_image(first_category_id, token)
    
    # Step 5: List categories again to see changes
    print("\n[5] Listing categories after updates...")
    list_categories(token)
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
