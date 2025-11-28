"""
Test script for File Manager API
Tests all endpoints: upload, view, delete, create folder, list, navigate
"""
import requests
import json
from pathlib import Path
from typing import Tuple

BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json"}

# Test credentials
ADMIN = {"email": "admin@pos.com", "password": "admin123"}
admin_token = None


def login() -> bool:
    """Login and get token"""
    global admin_token
    response = requests.post(
        f"{BASE_URL}/auth/login/json",
        headers=HEADERS,
        json=ADMIN
    )
    if response.status_code == 200:
        admin_token = response.json().get("access_token")
        print("✅ Login successful")
        return True
    print(f"❌ Login failed: {response.status_code}")
    return False


def get_auth_headers():
    """Get headers with authorization"""
    return {**HEADERS, "Authorization": f"Bearer {admin_token}"}


def test_create_folder() -> Tuple[bool, str]:
    """Test creating a folder"""
    print("\n" + "="*70)
    print("TEST 1: Create Folder")
    print("="*70)
    
    response = requests.post(
        f"{BASE_URL}/filemanager/create-folder",
        headers=get_auth_headers(),
        json={"folder_name": "test_images", "parent_path": ""}
    )
    
    if response.status_code == 201:
        data = response.json()
        print(f"✅ Folder created: {data['folder_name']}")
        print(f"   Path: {data['folder_path']}")
        return True, "test_images"
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False, ""


def test_upload_image(folder: str = "") -> Tuple[bool, str]:
    """Test uploading an image file"""
    print("\n" + "="*70)
    print("TEST 2: Upload Image File")
    print("="*70)
    
    # Create a test image file (simple PNG)
    test_image_path = Path("test_image.png")
    # Minimal PNG (1x1 pixel, transparent)
    png_bytes = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00'
        b'\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx'
        b'\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01\xb8\xd4c\x80\x00\x00'
        b'\x00\x00IEND\xaeB`\x82'
    )
    
    try:
        with open(test_image_path, "wb") as f:
            f.write(png_bytes)
        
        with open(test_image_path, "rb") as f:
            files = {"file": ("test_image.png", f, "image/png")}
            params = {"folder": folder} if folder else {}
            response = requests.post(
                f"{BASE_URL}/filemanager/upload",
                headers={"Authorization": f"Bearer {admin_token}"},
                files=files,
                params=params
            )
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Image uploaded: {data['file_name']}")
            print(f"   Size: {data['file_size']} bytes")
            print(f"   URL: {data['url']}")
            return True, data['file_path']
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False, ""
    finally:
        if test_image_path.exists():
            test_image_path.unlink()


def test_list_folder(folder: str = "") -> bool:
    """Test listing folder contents"""
    print("\n" + "="*70)
    print("TEST 3: List Folder Contents")
    print("="*70)
    
    response = requests.get(
        f"{BASE_URL}/filemanager/list/{folder}" if folder else f"{BASE_URL}/filemanager/list/",
        headers=get_auth_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Folder path: {data['path'] or 'root'}")
        print(f"   Total items: {data['total_items']}")
        print(f"   Folders: {len(data['folders'])}")
        print(f"   Files: {len(data['files'])}")
        
        if data['files']:
            print("\n   Files:")
            for file in data['files']:
                print(f"     - {file['name']} ({file['size']} bytes)")
        
        if data['folders']:
            print("\n   Folders:")
            for folder in data['folders']:
                print(f"     - {folder['name']}/")
        
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def test_view_file_metadata(file_path: str) -> bool:
    """Test getting file metadata"""
    print("\n" + "="*70)
    print("TEST 4: Get File Metadata")
    print("="*70)
    
    response = requests.get(
        f"{BASE_URL}/filemanager/view-metadata/{file_path}",
        headers=get_auth_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ File: {data['file_name']}")
        print(f"   Path: {data['file_path']}")
        print(f"   Size: {data['file_size']} bytes")
        print(f"   MIME: {data['mime_type']}")
        print(f"   Is Image: {data['is_image']}")
        print(f"   Modified: {data['modified_at']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def test_get_info(path: str) -> bool:
    """Test getting file/folder info"""
    print("\n" + "="*70)
    print("TEST 5: Get File/Folder Info")
    print("="*70)
    
    response = requests.get(
        f"{BASE_URL}/filemanager/info/{path}",
        headers=get_auth_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Item: {data['name']}")
        print(f"   Type: {data['type']}")
        print(f"   Size: {data['size']} bytes")
        print(f"   Path: {data['path']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def test_navigate_folders(path: str) -> bool:
    """Test folder navigation"""
    print("\n" + "="*70)
    print("TEST 6: Navigate Folders")
    print("="*70)
    
    response = requests.get(
        f"{BASE_URL}/filemanager/navigate/{path}",
        headers=get_auth_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Current path: {data['path'] or 'root'}")
        print(f"   Parent path: {data['parent_path'] or 'N/A'}")
        print(f"   Items: {data['total_items']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        return False


def test_rename_item(file_path: str) -> Tuple[bool, str]:
    """Test renaming a file"""
    print("\n" + "="*70)
    print("TEST 7: Rename File")
    print("="*70)
    
    new_name = "renamed_image.png"
    response = requests.post(
        f"{BASE_URL}/filemanager/rename/{file_path}",
        headers=get_auth_headers(),
        json={"new_name": new_name}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ File renamed: {data['new_name']}")
        print(f"   Old path: {data['old_path']}")
        print(f"   New path: {data['new_path']}")
        return True, data['new_path']
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False, file_path


def test_delete_file(file_path: str) -> bool:
    """Test deleting a file"""
    print("\n" + "="*70)
    print("TEST 8: Delete File")
    print("="*70)
    
    response = requests.delete(
        f"{BASE_URL}/filemanager/delete/{file_path}",
        headers=get_auth_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Item deleted: {data['deleted_path']}")
        print(f"   Type: {data['type']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def test_delete_folder(folder_path: str) -> bool:
    """Test deleting a folder"""
    print("\n" + "="*70)
    print("TEST 9: Delete Folder")
    print("="*70)
    
    response = requests.delete(
        f"{BASE_URL}/filemanager/delete/{folder_path}",
        headers=get_auth_headers(),
        json={"recursive": True}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Folder deleted: {data['deleted_path']}")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def test_invalid_file_upload() -> bool:
    """Test uploading invalid file type"""
    print("\n" + "="*70)
    print("TEST 10: Invalid File Upload (should fail)")
    print("="*70)
    
    # Create a test text file
    test_file_path = Path("test.txt")
    
    try:
        with open(test_file_path, "w") as f:
            f.write("This is a text file")
        
        with open(test_file_path, "rb") as f:
            files = {"file": ("test.txt", f, "text/plain")}
            response = requests.post(
                f"{BASE_URL}/filemanager/upload",
                headers={"Authorization": f"Bearer {admin_token}"},
                files=files
            )
        
        if response.status_code == 400:
            print(f"✅ Invalid file type rejected (as expected)")
            print(f"   Error: {response.json()['detail']}")
            return True
        else:
            print(f"❌ Should have failed with 400, got {response.status_code}")
            return False
    finally:
        if test_file_path.exists():
            test_file_path.unlink()


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  FILE MANAGER API - COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    results = []
    
    # Login
    if not login():
        print("❌ Cannot proceed without login")
        return
    
    # Test 1: Create folder
    folder_success, folder_name = test_create_folder()
    results.append(("Create Folder", folder_success))
    
    # Test 2: Upload image
    upload_success, file_path = test_upload_image(folder_name if folder_success else "")
    results.append(("Upload Image", upload_success))
    
    # Test 3: List folder
    list_success = test_list_folder(folder_name if folder_success else "")
    results.append(("List Folder", list_success))
    
    # Test 4: View metadata
    if upload_success:
        metadata_success = test_view_file_metadata(file_path)
        results.append(("View Metadata", metadata_success))
    
    # Test 5: Get info
    if upload_success:
        info_success = test_get_info(file_path)
        results.append(("Get Info", info_success))
    
    # Test 6: Navigate
    if folder_success:
        nav_success = test_navigate_folders(folder_name)
        results.append(("Navigate Folders", nav_success))
    
    # Test 7: Rename
    if upload_success:
        rename_success, new_path = test_rename_item(file_path)
        results.append(("Rename File", rename_success))
        if rename_success:
            file_path = new_path
    
    # Test 8: Delete file
    if upload_success:
        delete_success = test_delete_file(file_path)
        results.append(("Delete File", delete_success))
    
    # Test 9: Delete folder
    if folder_success:
        delete_folder_success = test_delete_folder(folder_name)
        results.append(("Delete Folder", delete_folder_success))
    
    # Test 10: Invalid file
    invalid_success = test_invalid_file_upload()
    results.append(("Invalid File Rejection", invalid_success))
    
    # Print summary
    print("\n" + "="*70)
    print("  TEST SUMMARY")
    print("="*70 + "\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    print(f"\n{'='*70}")
    print(f"Results: {passed}/{total} tests passed")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
