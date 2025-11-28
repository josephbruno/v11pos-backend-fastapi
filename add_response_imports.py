"""
Script to add standard response formatting imports to all route files
"""
import os
import glob

# Find all route files
route_files = glob.glob("/home/brunodoss/docs/pos/pos/pos-fastapi/app/routes/*.py")

for file_path in route_files:
    filename = os.path.basename(file_path)
    
    # Skip files already updated
    if filename in ['__init__.py', 'auth.py', 'categories.py']:
        print(f"Skipping {filename} (already updated)")
        continue
    
    print(f"Processing {filename}...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if already has the import
    if 'from app.response_formatter import' in content:
        print(f"  - {filename} already has response_formatter import")
        continue
    
    # Find the last import line
    lines = content.split('\n')
    last_import_idx = 0
    
    for i, line in enumerate(lines):
        if line.startswith('from ') or line.startswith('import '):
            last_import_idx = i
    
    # Insert the import after the last import
    import_line = "from app.response_formatter import success_response, created_response, list_response, deleted_response, error_response"
    lines.insert(last_import_idx + 1, import_line)
    
    # Write back
    with open(file_path, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"  ✓ Added response_formatter import to {filename}")

print("\n✓ All route files processed!")
