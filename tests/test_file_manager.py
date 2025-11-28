"""
Comprehensive File Manager API Tests
Tests all endpoints: upload, view, delete, create folder, list, navigate
"""
import requests
import json
from pathlib import Path
from typing import Optional

BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Content-Type": "application/json"}

# Test credentials
ADMIN = {"email": "admin@pos.com", "password": "admin123"}
admin_token: Optional[str] = None

# Test files (we'll create these locally for testing)
TEST_IMAGE_PATH = Path("test_image.jpg")
TEST_FOLDER = "test_folder"
TEST_SUBFOLDER = "test_subfolder"


def setup_test_image():
    """Create a simple test image"""
    # Create a minimal JPEG (1x1 pixel)
    jpeg_data = bytes.fromhex(
        "ffd8ffe000104a46494600010100000100010000ffdb4300080606070605080707"
        "07090909080a0c140d0c0b0b0c1912130f141d1a1f1e1d1a1c1c20242e2720222c"
        "231c1c28372a1e277e65626270393b763c4c6b33495762f1ffdb4301090909090c"
        "0b0c0c15100d10f1ffc00011080001000101011100021101031101ffc4001f000001"
        "05010101010101000000000000000102030405060708090a0bffc400b5100002010303"
        "0402040505040409000102030011041005122131410613516107227114328191a1082342"
        "b1c11552d1f0243362728209029c17f125a26a7282938373a3b3c3d3e3f40414243444546"
        "47484950515253545556575859595a5b5c5d5e5f60616263646566676869696a6b6c6d6e6f"
        "707172737475767778797a7b7c7d7e7f80818283848586878889898a8b8c8d8e8f909192939495"
        "9697989a9b9c9d9e9f"
    )
    with open(TEST_IMAGE_PATH, "wb") as f:
        f.write(jpeg_data)


def cleanup_test_image():
    """Remove test image"""
    if TEST_IMAGE_PATH.exists():
        TEST_IMAGE_PATH.unlink()


def login() -> bool:
    """Authenticate and get token"""
    global admin_token
    print("\n📝 STEP 1: Authenticating...")
    
    response = requests.post(
        f"{BASE_URL}/auth/login/json",
        headers=HEADERS,
        json=ADMIN
    )
    
    if response.status_code == 200:
        admin_token = response.json().get("access_token")
        print(f"✅ Login successful - Token: {admin_token[:30]}...")
        return True
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return False


def get_auth_headers():
    """Get headers with authentication"""
    return {**HEADERS, "Authorization": f"Bearer {admin_token}"}


def test_upload_file():
    """Test file upload endpoint"""
    print("\n📝 STEP 2: Testing File Upload...")
    
    # Ensure test image exists
    setup_test_image()
    
    with open(TEST_IMAGE_PATH, "rb") as f:
        files = {"file": (TEST_IMAGE_PATH.name, f, "image/jpeg")}
        response = requests.post(
            f"{BASE_URL}/filemanager/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            files=files
        )
    
    if response.status_code == 201:
        data = response.json()
        print(f"✅ File uploaded: {data.get('file_name')}")
        print(f"   Path: {data.get('file_path')}")
        print(f"   Size: {data.get('file_size')} bytes")
        print(f"   URL: {data.get('url')}")
        return data.get("file_path")
    else:
        print(f"❌ Upload failed: {response.status_code} - {response.text}")
        return None


def test_upload_to_folder(file_path: str):
    """Test file upload to specific folder"""
    print("\n📝 STEP 3: Testing Upload to Folder...")
    
    setup_test_image()
    
    with open(TEST_IMAGE_PATH, "rb") as f:
        files = {"file": (TEST_IMAGE_PATH.name, f, "image/jpeg")}
        response = requests.post(
            f"{BASE_URL}/filemanager/upload?folder={TEST_FOLDER}",
            headers={"Authorization": f"Bearer {admin_token}"},
            files=files
        )
    
    if response.status_code == 201:
        data = response.json()
        print(f"✅ File uploaded to folder: {data.get('file_path')}")
        return data.get("file_path")
    else:
        print(f"❌ Upload to folder failed: {response.status_code} - {response.text}")
        return None


def test_invalid_file_type():
    """Test upload with invalid file type"""
    print("\n📝 STEP 4: Testing Invalid File Type Rejection...")
    
    # Create a text file
    test_file = Path("test.txt")
    test_file.write_text("This is a test file")
    
    try:
        with open(test_file, "rb") as f:
            files = {"file": (test_file.name, f, "text/plain")}
            response = requests.post(
                f"{BASE_URL}/filemanager/upload",
                headers={"Authorization": f"Bearer {admin_token}"},
                files=files
            )
        
        if response.status_code == 400:
            print(f"✅ Invalid file type rejected correctly: {response.json().get('detail')}")
        else:
            print(f"❌ Should have rejected invalid file type: {response.status_code}")
    finally:
        test_file.unlink()


def test_view_file(file_path: str):
    """Test file view endpoint"""
    print("\n📝 STEP 5: Testing View File...")
    
    response = requests.get(
        f"{BASE_URL}/filemanager/view/{file_path}",
        headers=get_auth_headers()
    )
    
    if response.status_code == 200:
        print(f"✅ File retrieved successfully")
        print(f"   Content-Type: {response.headers.get('content-type')}")
        print(f"   Content-Length: {len(response.content)} bytes")
    else:
        print(f"❌ View failed: {response.status_code}")


def test_view_metadata(file_path: str):
    """Test file metadata endpoint"""
    print("\n📝 STEP 6: Testing View File Metadata...")
    
    response = requests.get(
        f"{BASE_URL}/filemanager/view-metadata/{file_path}",
        headers=get_auth_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ File metadata retrieved:")
        print(f"   Name: {data.get('file_name')}")
        print(f"   Size: {data.get('file_size')} bytes")
        print(f"   MIME Type: {data.get('mime_type')}")
        print(f"   Created: {data.get('created_at')}")
    else:
        print(f"❌ Metadata retrieval failed: {response.status_code}")


def test_create_folder():
    """Test folder creation"""
    print("\n📝 STEP 7: Testing Create Folder...")
    
    response = requests.post(
        f"{BASE_URL}/filemanager/create-folder?folder_name={TEST_FOLDER}",
        headers=get_auth_headers()
    )
    
    if response.status_code == 201:
        data = response.json()
        print(f"✅ Folder created: {data.get('folder_path')}")
        return True
    else:
        print(f"❌ Folder creation failed: {response.status_code} - {response.text}")
        return False


def test_create_subfolder():
    """Test nested folder creation"""
    print("\n📝 STEP 8: Testing Create Nested Folder...")
    
    response = requests.post(
        f"{BASE_URL}/filemanager/create-folder?folder_name={TEST_SUBFOLDER}&parent_path={TEST_FOLDER}",
        headers=get_auth_headers()
    )
    
    if response.status_code == 201:
        data = response.json()
        print(f"✅ Nested folder created: {data.get('folder_path')}")
        return True
    else:
        print(f"❌ Nested folder creation failed: {response.status_code}")
        return False


def test_list_folder_root():
    """Test listing root folder"""
    print("\n📝 STEP 9: Testing List Root Folder...")
    
    response = requests.get(
        f"{BASE_URL}/filemanager/list/",
        headers=get_auth_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Root folder contents:")
        print(f"   Total items: {data.get('total_items')}")
        print(f"   Files: {len(data.get('files', []))}")
        print(f"   Folders: {len(data.get('folders', []))}")
        
        if data.get('files'):
            print(f"   First file: {data['files'][0].get('name')}")
        if data.get('folders'):
            print(f"   First folder: {data['folders'][0].get('name')}")
    else:
        print(f"❌ List failed: {response.status_code}")


def test_list_subfolder(folder_path: str):
    """Test listing subfolder"""
    print(f"\n📝 STEP 10: Testing List Subfolder ({folder_path})...")
    
    response = requests.get(
        f"{BASE_URL}/filemanager/list/{folder_path}",
        headers=get_auth_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Subfolder contents:")
        print(f"   Current path: {data.get('path')}")
        print(f"   Total items: {data.get('total_items')}")
        print(f"   Files: {len(data.get('files', []))}")
        print(f"   Folders: {len(data.get('folders', []))}")
    else:
        print(f"❌ List subfolder failed: {response.status_code}")


def test_navigate():
    """Test folder navigation"""
    print("\n📝 STEP 11: Testing Navigation...")
    
    response = requests.get(
        f"{BASE_URL}/filemanager/navigate/{TEST_FOLDER}",
        headers=get_auth_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Navigation successful:")
        print(f"   Current path: {data.get('path')}")
        print(f"   Parent path: {data.get('parent_path')}")
        print(f"   Total items: {data.get('total_items')}")
    else:
        print(f"❌ Navigation failed: {response.status_code}")


def test_get_file_info(file_path: str):
    """Test get file info endpoint"""
    print("\n📝 STEP 12: Testing Get File Info...")
    
    response = requests.get(
        f"{BASE_URL}/filemanager/info/{file_path}",
        headers=get_auth_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ File info retrieved:")
        print(f"   Name: {data.get('name')}")
        print(f"   Type: {data.get('type')}")
        print(f"   Size: {data.get('size')} bytes")
        print(f"   Is Image: {data.get('is_image')}")
    else:
        print(f"❌ Get info failed: {response.status_code}")


def test_rename_file(file_path: str):
    """Test file rename"""
    print("\n📝 STEP 13: Testing Rename File...")
    
    response = requests.post(
        f"{BASE_URL}/filemanager/rename/{file_path}?new_name=renamed_image.jpg",
        headers=get_auth_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ File renamed:")
        print(f"   Old path: {data.get('old_path')}")
        print(f"   New path: {data.get('new_path')}")
        return data.get("new_path")
    else:
        print(f"❌ Rename failed: {response.status_code}")
        return file_path


def test_delete_file(file_path: str):
    """Test file deletion"""
    print("\n📝 STEP 14: Testing Delete File...")
    
    response = requests.delete(
        f"{BASE_URL}/filemanager/delete/{file_path}",
        headers=get_auth_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ File deleted: {data.get('deleted_path')}")
    else:
        print(f"❌ Delete failed: {response.status_code}")


def test_delete_folder(folder_path: str):
    """Test folder deletion"""
    print("\n📝 STEP 15: Testing Delete Folder...")
    
    response = requests.delete(
        f"{BASE_URL}/filemanager/delete/{folder_path}?recursive=true",
        headers=get_auth_headers()
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Folder deleted: {data.get('deleted_path')}")
    else:
        print(f"❌ Delete folder failed: {response.status_code}")


def test_path_traversal_protection():
    """Test directory traversal attack protection"""
    print("\n📝 STEP 16: Testing Path Traversal Protection...")
    
    # Try to access parent directory
    response = requests.get(
        f"{BASE_URL}/filemanager/list/../",
        headers=get_auth_headers()
    )
    
    if response.status_code == 403:
        print(f"✅ Path traversal blocked correctly")
    else:
        print(f"⚠️  Path traversal might not be properly blocked: {response.status_code}")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  FILE MANAGER API - COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    try:
        # Setup
        if not login():
            print("❌ Cannot proceed without authentication")
            return
        
        # Run tests
        file_path = test_upload_file()
        if not file_path:
            print("❌ Cannot proceed without uploaded file")
            return
        
        test_upload_to_folder(file_path)
        test_invalid_file_type()
        test_view_file(file_path)
        test_view_metadata(file_path)
        test_create_folder()
        test_create_subfolder()
        test_list_folder_root()
        test_list_subfolder(TEST_FOLDER)
        test_navigate()
        test_get_file_info(file_path)
        renamed_path = test_rename_file(file_path)
        test_delete_file(renamed_path)
        test_delete_folder(TEST_FOLDER)
        test_path_traversal_protection()
        
        print("\n" + "="*70)
        print("  ✅ ALL FILE MANAGER TESTS COMPLETED")
        print("="*70 + "\n")
        
    finally:
        # Cleanup
        cleanup_test_image()


if __name__ == "__main__":
    main()
