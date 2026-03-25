#!/usr/bin/env python3
"""
Script to add timezone conversion to all API endpoints
"""
import os
import re

def add_timezone_to_success_response(content):
    """Add timezone parameter to success_response calls"""
    
    # Pattern 1: success_response with data parameter
    pattern1 = r'return success_response\(\s*message="([^"]+)",\s*data=([^)]+)\s*\)'
    replacement1 = r'return success_response(\n            message="\1",\n            data=\2,\n            timezone=getattr(current_user, \'timezone\', None)\n        )'
    
    # Pattern 2: success_response with data and meta
    pattern2 = r'return success_response\(\s*message="([^"]+)",\s*data=([^,]+),\s*meta=([^)]+)\s*\)'
    replacement2 = r'return success_response(\n            message="\1",\n            data=\2,\n            meta=\3,\n            timezone=getattr(current_user, \'timezone\', None)\n        )'
    
    # Pattern 3: success_response without data
    pattern3 = r'return success_response\(\s*message="([^"]+)"\s*\)'
    replacement3 = r'return success_response(\n            message="\1",\n            timezone=getattr(current_user, \'timezone\', None)\n        )'
    
    # Apply replacements
    content = re.sub(pattern2, replacement2, content)
    content = re.sub(pattern1, replacement1, content)
    # Don't replace pattern3 as timezone not needed without data
    
    return content

def ensure_current_user_dependency(content, route_function):
    """Ensure current_user is in function parameters"""
    
    # Check if current_user already exists
    if 'current_user: User = Depends(get_current_active_user)' in route_function or \
       'current_user: User = Depends(get_current_user)' in route_function:
        return route_function
    
    # Add current_user before db parameter
    if 'db: AsyncSession = Depends(get_db)' in route_function:
        route_function = route_function.replace(
            'db: AsyncSession = Depends(get_db)',
            'current_user: User = Depends(get_current_active_user),\n    db: AsyncSession = Depends(get_db)'
        )
    
    return route_function

def process_route_file(filepath):
    """Process a single route file"""
    
    print(f"Processing {filepath}...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Skip if already has timezone in success_response
    if "timezone=getattr(current_user, 'timezone', None)" in content:
        print(f"  ✓ Already has timezone support")
        return
    
    # Add timezone to success_response calls
    updated_content = add_timezone_to_success_response(content)
    
    # Write back
    if updated_content != content:
        with open(filepath, 'w') as f:
            f.write(updated_content)
        print(f"  ✓ Updated with timezone support")
    else:
        print(f"  - No changes needed")

def main():
    """Main function"""
    
    # Get all route files
    modules_dir = '/home/brunodoss/docs/pos/pos/pos-fastapi/app/modules'
    
    route_files = []
    for root, dirs, files in os.walk(modules_dir):
        for file in files:
            if file == 'route.py':
                route_files.append(os.path.join(root, file))
    
    print(f"Found {len(route_files)} route files\n")
    
    for route_file in route_files:
        try:
            process_route_file(route_file)
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print(f"\n✅ Completed processing all route files")

if __name__ == '__main__':
    main()
