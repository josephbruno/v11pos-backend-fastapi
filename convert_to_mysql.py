#!/usr/bin/env python3
"""
Script to convert PostgreSQL UUID columns to MySQL CHAR(36) columns
"""
import os
import re

model_files = [
    "app/models/user.py",
    "app/models/product.py",
    "app/models/customer.py",
    "app/models/qr.py",
    "app/models/order.py",
    "app/models/settings.py"
]

for filepath in model_files:
    print(f"Processing {filepath}...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Remove PostgreSQL UUID import
    content = re.sub(r'from sqlalchemy\.dialects\.postgresql import UUID\n', '', content)
    
    # Replace UUID columns with String(36)
    # Primary keys: UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    content = re.sub(
        r'Column\(UUID\(as_uuid=True\), primary_key=True, default=uuid\.uuid4\)',
        'Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))',
        content
    )
    
    # Foreign keys and regular UUID columns: UUID(as_uuid=True)
    content = re.sub(
        r'UUID\(as_uuid=True\)',
        'String(36)',
        content
    )
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"✅ Converted {filepath}")

print("\n✅ All models converted to MySQL compatible format!")
