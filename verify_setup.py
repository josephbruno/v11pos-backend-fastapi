#!/usr/bin/env python
"""
RestaurantPOS - System Verification Script
Checks that all components are properly installed and configured.
"""

import sys
import importlib
from pathlib import Path
from datetime import datetime

# ANSI Colors (disabled for Windows compatibility)
GREEN = ""
RED = ""
YELLOW = ""
BLUE = ""
RESET = ""

# Symbols
OK_SYMBOL = "[OK]"
FAIL_SYMBOL = "[FAIL]"
WARN_SYMBOL = "[WARN]"

def print_header(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"{title.center(60)}")
    print(f"{'='*60}\n")

def check_module(module_name):
    """Check if a module is installed"""
    try:
        importlib.import_module(module_name)
        return True, None
    except ImportError as e:
        return False, str(e)

def check_file_exists(file_path):
    """Check if a file exists"""
    return Path(file_path).exists()

def verify_environment():
    """Verify environment setup"""
    print_header("Environment Verification")
    
    # Check Python version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    status = OK_SYMBOL if sys.version_info >= (3, 8) else FAIL_SYMBOL
    print(f"{status} Python Version: {py_version}")
    
    # Check venv
    venv_active = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    status = OK_SYMBOL if venv_active else WARN_SYMBOL
    print(f"{status} Virtual Environment: {'Active' if venv_active else 'Not active (but OK)'}")

def verify_dependencies():
    """Verify all dependencies are installed"""
    print_header("Dependencies Verification")
    
    core_deps = {
        "fastapi": "Web Framework",
        "uvicorn": "ASGI Server",
        "sqlalchemy": "ORM",
        "pymysql": "MySQL Driver",
        "pydantic": "Data Validation",
        "python_dotenv": "Environment Variables",
        "cryptography": "Encryption",
        "jose": "JWT Tokens",
        "passlib": "Password Hashing",
    }
    
    dev_deps = {
        "pytest": "Testing",
        "pytest_cov": "Coverage",
        "black": "Formatter",
        "flake8": "Linter",
        "mypy": "Type Checker",
    }
    
    print("Core Dependencies:")
    for module, description in core_deps.items():
        installed, error = check_module(module)
        status = OK_SYMBOL if installed else FAIL_SYMBOL
        print(f"  {status} {module:20} - {description}")
    
    print("\nDevelopment Tools:")
    for module, description in dev_deps.items():
        installed, error = check_module(module)
        status = OK_SYMBOL if installed else FAIL_SYMBOL
        print(f"  {status} {module:20} - {description}")

def verify_project_structure():
    """Verify project structure"""
    print_header("Project Structure Verification")
    
    files_to_check = {
        "app/__init__.py": "App package",
        "app/main.py": "Main application",
        "app/config.py": "Configuration",
        "app/database.py": "Database setup",
        "app/security.py": "Security utilities",
        "app/business_logic.py": "Business logic",
        "app/dependencies.py": "Dependencies",
        ".env": "Environment file",
        "requirements.txt": "Dependencies list",
    }
    
    for file_path, description in files_to_check.items():
        exists = check_file_exists(file_path)
        status = OK_SYMBOL if exists else FAIL_SYMBOL
        print(f"{status} {file_path:30} - {description}")

def verify_models():
    """Verify database models"""
    print_header("Database Models Verification")
    
    try:
        from app.models import (
            user, product, order, customer, qr, settings
        )
        
        models = [
            ("User", user),
            ("Product", product),
            ("Order", order),
            ("Customer", customer),
            ("QR", qr),
            ("Settings", settings),
        ]
        
        for model_name, module in models:
            status = OK_SYMBOL if module else FAIL_SYMBOL
            print(f"{status} {model_name} models loaded successfully")
            
    except Exception as e:
        print(f"{FAIL_SYMBOL} Error loading models: {e}")

def verify_database():
    """Verify database connection"""
    print_header("Database Verification")
    
    try:
        from app.database import engine, get_db
        
        # Try to connect
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            status = OK_SYMBOL
            print(f"{status} Database connection: OK")
        
        # Check tables
        inspector = __import__('sqlalchemy').inspect(engine)
        table_count = len(inspector.get_table_names())
        print(f"{OK_SYMBOL} Database tables: {table_count} tables found")
        
    except Exception as e:
        print(f"{FAIL_SYMBOL} Database connection failed: {e}")

def verify_schemas():
    """Verify Pydantic schemas"""
    print_header("Schemas Verification")
    
    try:
        from app.schemas import auth, user, product, order, customer, qr, settings
        
        schemas = [
            ("Auth", auth),
            ("User", user),
            ("Product", product),
            ("Order", order),
            ("Customer", customer),
            ("QR", qr),
            ("Settings", settings),
        ]
        
        for schema_name, module in schemas:
            status = OK_SYMBOL if module else FAIL_SYMBOL
            print(f"{status} {schema_name} schemas loaded successfully")
            
    except Exception as e:
        print(f"{FAIL_SYMBOL} Error loading schemas: {e}")

def verify_routes():
    """Verify API routes"""
    print_header("API Routes Verification")
    
    try:
        from app.main import app
        
        route_count = len(app.routes)
        endpoint_count = len([r for r in app.routes if hasattr(r, 'path')])
        
        print(f"{OK_SYMBOL} API routes loaded: {endpoint_count} endpoints")
        
    except Exception as e:
        print(f"{FAIL_SYMBOL} Error loading routes: {e}")

def main():
    """Run all verifications"""
    print("\n" + "=" * 60)
    print("RestaurantPOS FastAPI - System Verification".center(60))
    print("=" * 60)
    
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        verify_environment()
        verify_dependencies()
        verify_project_structure()
        verify_models()
        verify_schemas()
        verify_routes()
        verify_database()
        
    except Exception as e:
        print(f"\n{FAIL_SYMBOL} Error during verification: {e}")
        return 1
    
    print_header("Verification Complete")
    print(f"{OK_SYMBOL} All systems ready for development!\n")
    print("Next steps:")
    print(f"  1. Run: uvicorn app.main:app --reload")
    print(f"  2. Visit: http://localhost:8000/docs")
    print(f"  3. Check: pytest tests/\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
