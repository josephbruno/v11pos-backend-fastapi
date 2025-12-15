"""
Drop all tables and recreate with multi-tenant schema
WARNING: This will delete ALL data!
"""
from sqlalchemy import text
from app.database import engine, Base
from app.models import *
import sys

def confirm_drop():
    """Ask for confirmation before dropping tables"""
    print("=" * 60)
    print("⚠️  WARNING: DROP ALL TABLES")
    print("=" * 60)
    print("\nThis will:")
    print("  1. DROP all existing tables")
    print("  2. DELETE all data permanently")
    print("  3. CREATE fresh tables with multi-tenant schema")
    print("\n" + "=" * 60)
    
    response = input("\nType 'YES' to confirm (anything else to cancel): ")
    return response == "YES"

def drop_all_tables():
    """Drop all tables in the database"""
    print("\n🗑️  Dropping all tables...")
    
    with engine.connect() as conn:
        # Disable foreign key checks
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        conn.commit()
        
        # Get all tables
        result = conn.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result]
        
        # Drop each table
        for table in tables:
            print(f"  - Dropping table: {table}")
            conn.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
            conn.commit()
        
        # Re-enable foreign key checks
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        conn.commit()
    
    print("✅ All tables dropped successfully!")

def create_all_tables():
    """Create all tables from models"""
    print("\n🔨 Creating all tables with multi-tenant schema...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("✅ All tables created successfully!")

def verify_tables():
    """Verify tables were created"""
    print("\n🔍 Verifying tables...")
    
    with engine.connect() as conn:
        result = conn.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result]
        
        print(f"\n📊 Total tables created: {len(tables)}")
        print("\nTables:")
        for table in sorted(tables):
            print(f"  ✓ {table}")
    
    return tables

def seed_initial_data():
    """Create initial subscription plans"""
    from app.database import SessionLocal
    from app.models.restaurant import SubscriptionPlan
    from datetime import datetime
    import uuid
    
    print("\n🌱 Seeding initial data...")
    
    db = SessionLocal()
    
    try:
        # Create subscription plans
        plans = [
            {
                "id": str(uuid.uuid4()),
                "name": "trial",
                "display_name": "Trial Plan",
                "description": "14-day free trial with basic features",
                "tagline": "Try before you buy",
                "price_monthly": 0,
                "price_yearly": 0,
                "discount_yearly": 0,
                "max_users": 2,
                "max_products": 50,
                "max_orders_per_month": 100,
                "max_locations": 1,
                "max_storage_gb": 1,
                "features": ["qr_ordering", "basic_analytics"],
                "is_active": True,
                "is_public": True,
                "is_featured": False,
                "sort_order": 1,
                "trial_days": 14
            },
            {
                "id": str(uuid.uuid4()),
                "name": "basic",
                "display_name": "Basic Plan",
                "description": "Perfect for small restaurants",
                "tagline": "Get started with essential features",
                "price_monthly": 2900,  # $29
                "price_yearly": 29000,  # $290 (save $58)
                "discount_yearly": 17,
                "max_users": 5,
                "max_products": 200,
                "max_orders_per_month": 500,
                "max_locations": 1,
                "max_storage_gb": 5,
                "features": ["qr_ordering", "analytics", "loyalty", "email_support"],
                "is_active": True,
                "is_public": True,
                "is_featured": False,
                "sort_order": 2,
                "trial_days": 14
            },
            {
                "id": str(uuid.uuid4()),
                "name": "pro",
                "display_name": "Pro Plan",
                "description": "Advanced features for growing businesses",
                "tagline": "Most Popular",
                "price_monthly": 7900,  # $79
                "price_yearly": 79000,  # $790 (save $158)
                "discount_yearly": 17,
                "max_users": 15,
                "max_products": 1000,
                "max_orders_per_month": 2000,
                "max_locations": 3,
                "max_storage_gb": 20,
                "features": ["qr_ordering", "advanced_analytics", "loyalty", "multi_location", "api_access", "priority_support"],
                "is_active": True,
                "is_public": True,
                "is_featured": True,
                "sort_order": 3,
                "badge": "Most Popular",
                "trial_days": 14
            },
            {
                "id": str(uuid.uuid4()),
                "name": "enterprise",
                "display_name": "Enterprise Plan",
                "description": "Custom solution for large operations",
                "tagline": "Unlimited everything",
                "price_monthly": 19900,  # $199
                "price_yearly": 199000,  # $1990 (save $398)
                "discount_yearly": 17,
                "max_users": 999,
                "max_products": 99999,
                "max_orders_per_month": 99999,
                "max_locations": 99,
                "max_storage_gb": 100,
                "features": ["qr_ordering", "advanced_analytics", "loyalty", "multi_location", "api_access", "white_label", "dedicated_support", "custom_integrations"],
                "is_active": True,
                "is_public": True,
                "is_featured": False,
                "sort_order": 4,
                "badge": "Best Value",
                "trial_days": 30
            }
        ]
        
        for plan_data in plans:
            plan = SubscriptionPlan(**plan_data)
            db.add(plan)
            print(f"  ✓ Created plan: {plan.display_name}")
        
        db.commit()
        print("✅ Initial data seeded successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding data: {str(e)}")
        raise
    finally:
        db.close()

def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("🚀 MULTI-TENANT DATABASE SETUP")
    print("=" * 60)
    
    # Confirm action
    if not confirm_drop():
        print("\n❌ Operation cancelled.")
        sys.exit(0)
    
    try:
        # Step 1: Drop all tables
        drop_all_tables()
        
        # Step 2: Create all tables
        create_all_tables()
        
        # Step 3: Verify tables
        tables = verify_tables()
        
        # Step 4: Seed initial data
        seed_initial_data()
        
        print("\n" + "=" * 60)
        print("✅ DATABASE SETUP COMPLETE!")
        print("=" * 60)
        print(f"\n📊 Total tables: {len(tables)}")
        print("\n🎯 Next steps:")
        print("  1. Register a restaurant: POST /api/v1/onboarding/register")
        print("  2. Login: POST /api/v1/auth/login/json")
        print("  3. Start using the multi-tenant system!")
        print("\n" + "=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
