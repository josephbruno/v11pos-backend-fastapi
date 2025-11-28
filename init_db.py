#!/usr/bin/env python3
"""
Database initialization script for RestaurantPOS
Run this script to create all database tables
"""
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import create_tables, engine
from app.models import *  # Import all models
from sqlalchemy import inspect


def check_database_connection():
    """Check if database connection is working"""
    try:
        connection = engine.connect()
        connection.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\nPlease check:")
        print("1. PostgreSQL is running")
        print("2. Database credentials in .env are correct")
        print("3. Database 'restaurant_pos' exists")
        return False


def list_tables():
    """List all tables in the database"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    return tables


def initialize_database():
    """Initialize database with all tables"""
    print("\n" + "="*60)
    print("RestaurantPOS Database Initialization")
    print("="*60 + "\n")
    
    # Check connection
    if not check_database_connection():
        return False
    
    # Get existing tables
    existing_tables = list_tables()
    if existing_tables:
        print(f"\n⚠️  Found {len(existing_tables)} existing tables:")
        for table in existing_tables:
            print(f"   - {table}")
        
        response = input("\nDo you want to drop and recreate all tables? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Operation cancelled")
            return False
        
        # Drop all tables
        from app.database import Base
        print("\n🗑️  Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        print("✅ All tables dropped")
    
    # Create all tables
    print("\n🔨 Creating all tables...")
    try:
        create_tables()
        print("✅ All tables created successfully")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    
    # List created tables
    new_tables = list_tables()
    print(f"\n✅ Created {len(new_tables)} tables:")
    for table in sorted(new_tables):
        print(f"   - {table}")
    
    print("\n" + "="*60)
    print("Database initialization complete!")
    print("="*60)
    print("\nYou can now run the application:")
    print("  uvicorn app.main:app --reload")
    print("\nAPI Documentation will be available at:")
    print("  http://localhost:8000/docs")
    print("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    initialize_database()
