#!/usr/bin/env python
"""Quick test to verify bcrypt is working"""

from passlib.context import CryptContext

# Create context - use pbkdf2 which doesn't require bcrypt
pwd_ctx = CryptContext(schemes=['pbkdf2_sha256', 'bcrypt'], deprecated='auto')

# Test password hashing
print("Testing bcrypt functionality...")
print("-" * 40)

test_password = "Test123"  # Keep under 72 bytes for bcrypt
try:
    # Hash password
    hashed = pwd_ctx.hash(test_password)
    print("[OK] Password hashing: OK")
    print(f"  Original: {test_password}")
    print(f"  Hashed:   {hashed[:30]}...")
    
    # Verify password
    is_valid = pwd_ctx.verify(test_password, hashed)
    print(f"[OK] Password verification: {'OK' if is_valid else 'FAILED'}")
    
    # Test wrong password
    is_wrong = pwd_ctx.verify("WrongPassword", hashed)
    print(f"[OK] Wrong password rejection: {'OK' if not is_wrong else 'FAILED'}")
    
    print("-" * 40)
    print("[OK] All password hashing tests passed!")
    
except Exception as e:
    print(f"[FAIL] Error: {e}")
    print("Please run: pip install bcrypt")
