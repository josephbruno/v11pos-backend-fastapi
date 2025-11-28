"""
Complete Setup and Installation Guide for RestaurantPOS FastAPI

This script automates the setup process for the POS system.
"""

import os
import sys
import subprocess
import json
from pathlib import Path


def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"→ {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} - Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} - Failed")
        print(f"  Error: {e.stderr}")
        return False


def create_env_file():
    """Create .env file with database configuration"""
    env_content = """
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=restaurant_pos

# Security
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=7

# API Configuration
API_VERSION=1.0.0
API_TITLE=RestaurantPOS API
DEBUG=False

# Business Configuration
CURRENCY=USD
TIMEZONE=UTC
LANGUAGE=en

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# Email Configuration (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-password

# Payment Gateway (optional)
STRIPE_API_KEY=your-stripe-key
RAZORPAY_KEY=your-razorpay-key
"""
    
    with open(".env", "w") as f:
        f.write(env_content.strip())
    print("✓ Created .env file")


def create_project_structure():
    """Create necessary project directories"""
    directories = [
        "logs",
        "uploads",
        "uploads/products",
        "uploads/customers",
        "uploads/qr_codes",
        "tests",
        "migrations",
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}")


def setup_database():
    """Setup database and create tables"""
    print_section("DATABASE SETUP")
    
    print("To set up the database, run the following Python code:")
    print("""
from app.database import create_tables
create_tables()
    """)


def install_dependencies():
    """Install Python dependencies"""
    print_section("INSTALLING DEPENDENCIES")
    
    requirements_file = "requirements.txt"
    if os.path.exists(requirements_file):
        run_command(
            f"pip install -r {requirements_file}",
            "Installing dependencies from requirements.txt"
        )
    else:
        print("✗ requirements.txt not found")
        return False
    
    # Add additional development dependencies
    dev_dependencies = [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "black>=23.0.0",
        "flake8>=6.0.0",
        "mypy>=1.0.0",
    ]
    
    print("\nInstalling development dependencies...")
    for dep in dev_dependencies:
        run_command(f"pip install {dep}", f"Installing {dep}")
    
    return True


def create_alembic_config():
    """Initialize Alembic for database migrations"""
    print_section("ALEMBIC MIGRATION SETUP")
    
    if not os.path.exists("alembic"):
        run_command("alembic init alembic", "Initializing Alembic")
        print("\nAlembic initialized. Configure alembic/env.py with your database URL.")
    else:
        print("✓ Alembic already configured")


def run_migrations():
    """Run database migrations"""
    print_section("RUNNING MIGRATIONS")
    
    print("To run migrations, use:")
    print("""
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
    """)


def print_startup_instructions():
    """Print instructions for starting the server"""
    print_section("SERVER STARTUP")
    
    instructions = """
To start the RestaurantPOS API server, run:

    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Then access:
    - API Documentation: http://localhost:8000/docs
    - ReDoc: http://localhost:8000/redoc
    - API Root: http://localhost:8000/

Default Credentials:
    - Email: admin@example.com
    - Password: admin123456 (change after first login)

Useful Endpoints:
    - POST /api/v1/auth/register - Register new user
    - POST /api/v1/auth/login - Login user
    - GET /api/v1/products - List products
    - POST /api/v1/orders - Create order
    - GET /api/v1/customers - List customers
    """
    
    print(instructions)


def print_project_summary():
    """Print project summary and key features"""
    print_section("PROJECT SUMMARY")
    
    summary = """
RestaurantPOS FastAPI - A Complete Point of Sale System

KEY FEATURES:
✓ User Management (Admin, Manager, Staff, Cashier roles)
✓ Product Catalog (Categories, Products, Modifiers, Combos)
✓ Customer Management (Profiles, Tags, Loyalty Program)
✓ Order Processing (Dine-in, Takeaway, Delivery, QR Ordering)
✓ Kitchen Order Tickets (KOT) Management
✓ QR Table Ordering System
✓ Loyalty Points System
✓ Tax Management
✓ Analytics & Reporting
✓ Real-time Order Tracking
✓ Payment Integration Ready

DATABASE MODELS: 26 tables
API ENDPOINTS: 111+ endpoints
AUTHENTICATION: JWT + Role-Based Access Control

QUICK START CHECKLIST:
☐ Install dependencies (pip install -r requirements.txt)
☐ Create .env file with database credentials
☐ Create database: CREATE DATABASE restaurant_pos;
☐ Run migrations: alembic upgrade head
☐ Start server: uvicorn app.main:app --reload
☐ Access API docs: http://localhost:8000/docs

PROJECT STRUCTURE:
app/
├── main.py              - FastAPI application entry point
├── config.py            - Configuration management
├── database.py          - Database connection and setup
├── enums.py             - Enumeration definitions
├── security.py          - JWT and authentication utilities
├── business_logic.py    - Core business logic (calculations, validations)
├── dependencies.py      - Route dependencies and middleware
├── models/              - SQLAlchemy database models
├── schemas/             - Pydantic request/response schemas
├── routes/              - API route handlers
└── utils.py             - Utility functions

TESTING:
Run tests: pytest tests/ -v
With coverage: pytest tests/ --cov=app --cov-report=html

CODE QUALITY:
Format code: black app/
Lint: flake8 app/
Type check: mypy app/

DOCUMENTATION:
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- README.md: Project overview
- SETUP_GUIDE.md: Detailed setup instructions
- API_REFERENCE.md: Complete API documentation

SUPPORT & TROUBLESHOOTING:
See SETUP_GUIDE.md for common issues and solutions
    """
    
    print(summary)


def main():
    """Main setup orchestration"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║         RestaurantPOS FastAPI - Setup Assistant           ║
║                                                           ║
║  A Complete Point of Sale System for Restaurants         ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    print_section("SETUP STARTED")
    
    # Step 1: Create project structure
    print("STEP 1: Creating project structure...")
    create_project_structure()
    
    # Step 2: Create environment file
    print("\nSTEP 2: Creating environment configuration...")
    if not os.path.exists(".env"):
        create_env_file()
    else:
        print("✓ .env file already exists")
    
    # Step 3: Install dependencies
    print("\nSTEP 3: Installing dependencies...")
    if not install_dependencies():
        print("✗ Failed to install dependencies")
        return False
    
    # Step 4: Setup Alembic
    print("\nSTEP 4: Setting up database migrations...")
    create_alembic_config()
    
    # Print additional instructions
    print_startup_instructions()
    print_project_summary()
    
    print_section("SETUP COMPLETE")
    
    print("""
NEXT STEPS:
1. Edit .env file with your database credentials
2. Create MySQL database: CREATE DATABASE restaurant_pos;
3. Run: python -m alembic upgrade head
4. Start server: uvicorn app.main:app --reload
5. Create admin user through /api/v1/auth/register endpoint
6. Access API documentation at http://localhost:8000/docs

For more help, see SETUP_GUIDE.md
    """)
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        sys.exit(1)
