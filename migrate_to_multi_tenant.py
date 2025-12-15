"""
Database Migration Script for Multi-Tenant Conversion
This script converts the single-restaurant POS system to a multi-tenant SaaS platform.

WARNING: This is a major database migration. Always backup your database before running!

Usage:
    python migrate_to_multi_tenant.py

Steps:
1. Creates new tables (restaurants, subscriptions, etc.)
2. Creates a default restaurant from existing data
3. Adds restaurant_id to all existing tables
4. Populates restaurant_id with default restaurant
5. Adds foreign key constraints
6. Creates indexes for performance
"""

import sys
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text, inspect, Column, String, ForeignKey, Index
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.database import Base, engine
from urllib.parse import quote_plus

# Import all models to ensure they're registered with Base
from app.models import *

def print_step(step_num, message):
    """Print formatted step message"""
    print(f"\n{'='*80}")
    print(f"STEP {step_num}: {message}")
    print(f"{'='*80}")

def confirm_migration():
    """Ask user to confirm migration"""
    print("\n" + "!"*80)
    print("WARNING: This will modify your database structure!")
    print("Make sure you have backed up your database before proceeding.")
    print("!"*80 + "\n")
    
    response = input("Have you backed up your database? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Migration cancelled. Please backup your database first.")
        sys.exit(0)
    
    response = input("Type 'MIGRATE' to confirm and proceed: ").strip()
    if response != 'MIGRATE':
        print("Migration cancelled.")
        sys.exit(0)

def check_existing_migration(session):
    """Check if migration has already been run"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if 'restaurants' in tables:
        print("\n⚠️  Migration appears to have already been run (restaurants table exists).")
        response = input("Do you want to continue anyway? (yes/no): ").strip().lower()
        if response != 'yes':
            print("Migration cancelled.")
            sys.exit(0)

def create_new_tables(session):
    """Step 1: Create new multi-tenant tables"""
    print_step(1, "Creating new multi-tenant tables")
    
    try:
        # Create all tables defined in models
        Base.metadata.create_all(bind=engine)
        print("✓ New tables created successfully")
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        raise

def create_default_restaurant(session):
    """Step 2: Create default restaurant for existing data"""
    print_step(2, "Creating default restaurant")
    
    try:
        # Check if default restaurant already exists
        existing = session.execute(
            text("SELECT id FROM restaurants WHERE slug = 'default' LIMIT 1")
        ).fetchone()
        
        if existing:
            print(f"✓ Default restaurant already exists: {existing[0]}")
            return existing[0]
        
        # Create default restaurant
        default_restaurant_id = str(uuid.uuid4())
        trial_end = datetime.utcnow() + timedelta(days=14)
        
        session.execute(text("""
            INSERT INTO restaurants (
                id, name, slug, business_name, email, phone,
                subscription_plan, subscription_status, trial_ends_at,
                max_users, max_products, max_orders_per_month,
                is_active, is_verified, onboarding_completed,
                created_at, updated_at
            ) VALUES (
                :id, :name, :slug, :business_name, :email, :phone,
                :plan, :status, :trial_end,
                :max_users, :max_products, :max_orders,
                :is_active, :is_verified, :onboarding,
                :created_at, :updated_at
            )
        """), {
            'id': default_restaurant_id,
            'name': 'Default Restaurant',
            'slug': 'default',
            'business_name': 'Default Restaurant',
            'email': 'admin@restaurant.com',
            'phone': '1234567890',
            'plan': 'enterprise',  # Give unlimited access to existing restaurant
            'status': 'active',
            'trial_end': trial_end,
            'max_users': 999,
            'max_products': 9999,
            'max_orders': 999999,
            'is_active': True,
            'is_verified': True,
            'onboarding': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })
        
        session.commit()
        print(f"✓ Default restaurant created: {default_restaurant_id}")
        return default_restaurant_id
        
    except Exception as e:
        session.rollback()
        print(f"✗ Error creating default restaurant: {e}")
        raise

def get_tables_to_migrate():
    """Get list of tables that need restaurant_id"""
    return [
        # User tables
        'users',
        'shift_schedules',
        'staff_performance',
        
        # Product tables
        'categories',
        'products',
        'modifiers',
        'modifier_options',
        'product_modifiers',
        'combo_products',
        'combo_items',
        
        # Customer tables
        'customers',
        'customer_tags',
        'customer_tag_mapping',
        'loyalty_rules',
        'loyalty_transactions',
        
        # Order tables
        'orders',
        'order_items',
        'order_item_modifiers',
        'kot_groups',
        'order_taxes',
        'order_status_history',
        
        # QR tables
        'qr_tables',
        'qr_sessions',
        'qr_settings',
        
        # Settings tables
        'tax_rules',
        'settings',
        
        # Translation table
        'translations'
    ]

def add_restaurant_id_columns(session, default_restaurant_id):
    """Step 3: Add restaurant_id column to all tables"""
    print_step(3, "Adding restaurant_id columns to existing tables")
    
    inspector = inspect(engine)
    tables = get_tables_to_migrate()
    
    for table in tables:
        try:
            # Check if table exists
            if table not in inspector.get_table_names():
                print(f"  ⊘ Table '{table}' does not exist, skipping")
                continue
            
            # Check if column already exists
            columns = [col['name'] for col in inspector.get_columns(table)]
            if 'restaurant_id' in columns:
                print(f"  ⊘ Column restaurant_id already exists in '{table}', skipping")
                continue
            
            # Special handling for users table (nullable for platform admins)
            nullable = 'NULL' if table == 'users' else 'NOT NULL'
            
            # Add column
            session.execute(text(f"""
                ALTER TABLE {table}
                ADD COLUMN restaurant_id VARCHAR(36) {nullable}
            """))
            
            print(f"  ✓ Added restaurant_id to '{table}'")
            
        except Exception as e:
            print(f"  ✗ Error adding column to '{table}': {e}")
            # Continue with other tables
    
    session.commit()

def populate_restaurant_id(session, default_restaurant_id):
    """Step 4: Populate restaurant_id with default restaurant"""
    print_step(4, "Populating restaurant_id with default restaurant")
    
    inspector = inspect(engine)
    tables = get_tables_to_migrate()
    
    for table in tables:
        try:
            # Check if table exists
            if table not in inspector.get_table_names():
                continue
            
            # Check if column exists
            columns = [col['name'] for col in inspector.get_columns(table)]
            if 'restaurant_id' not in columns:
                continue
            
            # Update all rows
            result = session.execute(text(f"""
                UPDATE {table}
                SET restaurant_id = :restaurant_id
                WHERE restaurant_id IS NULL
            """), {'restaurant_id': default_restaurant_id})
            
            rows_updated = result.rowcount
            print(f"  ✓ Updated {rows_updated} rows in '{table}'")
            
        except Exception as e:
            print(f"  ✗ Error updating '{table}': {e}")
            # Continue with other tables
    
    session.commit()

def add_foreign_keys(session):
    """Step 5: Add foreign key constraints"""
    print_step(5, "Adding foreign key constraints")
    
    inspector = inspect(engine)
    tables = get_tables_to_migrate()
    
    for table in tables:
        try:
            # Check if table exists
            if table not in inspector.get_table_names():
                continue
            
            # Check if column exists
            columns = [col['name'] for col in inspector.get_columns(table)]
            if 'restaurant_id' not in columns:
                continue
            
            # Check if foreign key already exists
            foreign_keys = inspector.get_foreign_keys(table)
            fk_exists = any(
                fk['referred_table'] == 'restaurants' and 'restaurant_id' in fk['constrained_columns']
                for fk in foreign_keys
            )
            
            if fk_exists:
                print(f"  ⊘ Foreign key already exists for '{table}', skipping")
                continue
            
            # Add foreign key
            fk_name = f"fk_{table}_restaurant"
            session.execute(text(f"""
                ALTER TABLE {table}
                ADD CONSTRAINT {fk_name}
                FOREIGN KEY (restaurant_id)
                REFERENCES restaurants(id)
                ON DELETE CASCADE
            """))
            
            print(f"  ✓ Added foreign key to '{table}'")
            
        except Exception as e:
            print(f"  ✗ Error adding foreign key to '{table}': {e}")
            # Continue with other tables
    
    session.commit()

def add_indexes(session):
    """Step 6: Add indexes for performance"""
    print_step(6, "Adding indexes for performance")
    
    inspector = inspect(engine)
    tables = get_tables_to_migrate()
    
    for table in tables:
        try:
            # Check if table exists
            if table not in inspector.get_table_names():
                continue
            
            # Check if column exists
            columns = [col['name'] for col in inspector.get_columns(table)]
            if 'restaurant_id' not in columns:
                continue
            
            # Check if index already exists
            indexes = inspector.get_indexes(table)
            idx_exists = any(
                'restaurant_id' in idx['column_names']
                for idx in indexes
            )
            
            if idx_exists:
                print(f"  ⊘ Index already exists for '{table}', skipping")
                continue
            
            # Add index
            idx_name = f"idx_{table}_restaurant"
            session.execute(text(f"""
                CREATE INDEX {idx_name}
                ON {table}(restaurant_id)
            """))
            
            print(f"  ✓ Added index to '{table}'")
            
        except Exception as e:
            print(f"  ✗ Error adding index to '{table}': {e}")
            # Continue with other tables
    
    session.commit()

def create_default_admin_owner(session, default_restaurant_id):
    """Step 7: Create restaurant owner for existing admin"""
    print_step(7, "Creating restaurant owner for existing admin")
    
    try:
        # Find first admin user
        admin_user = session.execute(text("""
            SELECT id FROM users
            WHERE role = 'admin'
            AND restaurant_id = :restaurant_id
            LIMIT 1
        """), {'restaurant_id': default_restaurant_id}).fetchone()
        
        if not admin_user:
            print("  ⊘ No admin user found, skipping")
            return
        
        admin_user_id = admin_user[0]
        
        # Check if owner already exists
        existing_owner = session.execute(text("""
            SELECT id FROM restaurant_owners
            WHERE restaurant_id = :restaurant_id
            AND user_id = :user_id
        """), {
            'restaurant_id': default_restaurant_id,
            'user_id': admin_user_id
        }).fetchone()
        
        if existing_owner:
            print(f"  ⊘ Restaurant owner already exists")
            return
        
        # Create restaurant owner
        owner_id = str(uuid.uuid4())
        session.execute(text("""
            INSERT INTO restaurant_owners (
                id, restaurant_id, user_id, role, is_active, joined_at, created_at
            ) VALUES (
                :id, :restaurant_id, :user_id, :role, :is_active, :joined_at, :created_at
            )
        """), {
            'id': owner_id,
            'restaurant_id': default_restaurant_id,
            'user_id': admin_user_id,
            'role': 'owner',
            'is_active': True,
            'joined_at': datetime.utcnow(),
            'created_at': datetime.utcnow()
        })
        
        session.commit()
        print(f"  ✓ Created restaurant owner for admin user: {admin_user_id}")
        
    except Exception as e:
        session.rollback()
        print(f"  ✗ Error creating restaurant owner: {e}")

def create_subscription_plans(session):
    """Step 8: Create default subscription plans"""
    print_step(8, "Creating subscription plans")
    
    plans = [
        {
            'name': 'trial',
            'display_name': 'Trial',
            'description': '14-day free trial with limited features',
            'price_monthly': 0,
            'price_yearly': 0,
            'max_users': 2,
            'max_products': 50,
            'max_orders_per_month': 100,
            'max_locations': 1,
            'max_storage_gb': 1,
            'features': ['basic_pos', 'order_management'],
            'trial_days': 14,
            'is_public': True,
            'sort_order': 1
        },
        {
            'name': 'basic',
            'display_name': 'Basic',
            'description': 'Perfect for small restaurants',
            'tagline': 'Best for getting started',
            'price_monthly': 2900,  # $29/month
            'price_yearly': 29000,  # $290/year (2 months free)
            'max_users': 5,
            'max_products': 200,
            'max_orders_per_month': 1000,
            'max_locations': 1,
            'max_storage_gb': 5,
            'features': ['basic_pos', 'order_management', 'qr_ordering', 'basic_analytics'],
            'trial_days': 14,
            'is_public': True,
            'is_featured': False,
            'sort_order': 2
        },
        {
            'name': 'pro',
            'display_name': 'Professional',
            'description': 'For growing restaurants',
            'tagline': 'Most Popular',
            'price_monthly': 7900,  # $79/month
            'price_yearly': 79000,  # $790/year (2 months free)
            'max_users': 15,
            'max_products': 1000,
            'max_orders_per_month': 10000,
            'max_locations': 3,
            'max_storage_gb': 20,
            'features': [
                'basic_pos', 'order_management', 'qr_ordering',
                'advanced_analytics', 'loyalty_program', 'multi_location',
                'email_support', 'custom_reports'
            ],
            'trial_days': 14,
            'is_public': True,
            'is_featured': True,
            'badge': 'Most Popular',
            'sort_order': 3
        },
        {
            'name': 'enterprise',
            'display_name': 'Enterprise',
            'description': 'For large restaurant chains',
            'tagline': 'Unlimited Everything',
            'price_monthly': 19900,  # $199/month
            'price_yearly': 199000,  # $1990/year (2 months free)
            'max_users': 999,
            'max_products': 9999,
            'max_orders_per_month': 999999,
            'max_locations': 99,
            'max_storage_gb': 100,
            'features': [
                'basic_pos', 'order_management', 'qr_ordering',
                'advanced_analytics', 'loyalty_program', 'multi_location',
                'api_access', 'custom_integrations', 'dedicated_support',
                'custom_reports', 'white_label', 'sla_guarantee'
            ],
            'trial_days': 30,
            'is_public': True,
            'is_featured': False,
            'badge': 'Best Value',
            'sort_order': 4
        }
    ]
    
    for plan in plans:
        try:
            # Check if plan already exists
            existing = session.execute(text("""
                SELECT id FROM subscription_plans WHERE name = :name
            """), {'name': plan['name']}).fetchone()
            
            if existing:
                print(f"  ⊘ Plan '{plan['name']}' already exists, skipping")
                continue
            
            # Create plan
            plan_id = str(uuid.uuid4())
            session.execute(text("""
                INSERT INTO subscription_plans (
                    id, name, display_name, description, tagline,
                    price_monthly, price_yearly,
                    max_users, max_products, max_orders_per_month,
                    max_locations, max_storage_gb,
                    features, trial_days, is_active, is_public,
                    is_featured, sort_order, badge,
                    created_at, updated_at
                ) VALUES (
                    :id, :name, :display_name, :description, :tagline,
                    :price_monthly, :price_yearly,
                    :max_users, :max_products, :max_orders_per_month,
                    :max_locations, :max_storage_gb,
                    :features, :trial_days, :is_active, :is_public,
                    :is_featured, :sort_order, :badge,
                    :created_at, :updated_at
                )
            """), {
                'id': plan_id,
                'name': plan['name'],
                'display_name': plan['display_name'],
                'description': plan['description'],
                'tagline': plan.get('tagline'),
                'price_monthly': plan['price_monthly'],
                'price_yearly': plan['price_yearly'],
                'max_users': plan['max_users'],
                'max_products': plan['max_products'],
                'max_orders_per_month': plan['max_orders_per_month'],
                'max_locations': plan['max_locations'],
                'max_storage_gb': plan['max_storage_gb'],
                'features': str(plan['features']),  # Convert to JSON string
                'trial_days': plan['trial_days'],
                'is_active': True,
                'is_public': plan['is_public'],
                'is_featured': plan.get('is_featured', False),
                'sort_order': plan['sort_order'],
                'badge': plan.get('badge'),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            })
            
            print(f"  ✓ Created plan: {plan['display_name']}")
            
        except Exception as e:
            print(f"  ✗ Error creating plan '{plan['name']}': {e}")
    
    session.commit()

def verify_migration(session, default_restaurant_id):
    """Step 9: Verify migration was successful"""
    print_step(9, "Verifying migration")
    
    try:
        # Check restaurant exists
        restaurant = session.execute(text("""
            SELECT id, name FROM restaurants WHERE id = :id
        """), {'id': default_restaurant_id}).fetchone()
        
        if restaurant:
            print(f"  ✓ Default restaurant exists: {restaurant[1]}")
        else:
            print(f"  ✗ Default restaurant not found!")
            return False
        
        # Check users have restaurant_id
        users_count = session.execute(text("""
            SELECT COUNT(*) FROM users WHERE restaurant_id = :id
        """), {'id': default_restaurant_id}).scalar()
        print(f"  ✓ Users migrated: {users_count}")
        
        # Check products have restaurant_id
        products_count = session.execute(text("""
            SELECT COUNT(*) FROM products WHERE restaurant_id = :id
        """), {'id': default_restaurant_id}).scalar()
        print(f"  ✓ Products migrated: {products_count}")
        
        # Check orders have restaurant_id
        orders_count = session.execute(text("""
            SELECT COUNT(*) FROM orders WHERE restaurant_id = :id
        """), {'id': default_restaurant_id}).scalar()
        print(f"  ✓ Orders migrated: {orders_count}")
        
        # Check subscription plans
        plans_count = session.execute(text("""
            SELECT COUNT(*) FROM subscription_plans
        """)).scalar()
        print(f"  ✓ Subscription plans created: {plans_count}")
        
        print("\n✓ Migration verification completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n✗ Migration verification failed: {e}")
        return False

def main():
    """Main migration function"""
    print("\n" + "="*80)
    print("MULTI-TENANT DATABASE MIGRATION")
    print("="*80)
    
    # Confirm migration
    confirm_migration()
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # Check if migration already run
        check_existing_migration(session)
        
        # Step 1: Create new tables
        create_new_tables(session)
        
        # Step 2: Create default restaurant
        default_restaurant_id = create_default_restaurant(session)
        
        # Step 3: Add restaurant_id columns
        add_restaurant_id_columns(session, default_restaurant_id)
        
        # Step 4: Populate restaurant_id
        populate_restaurant_id(session, default_restaurant_id)
        
        # Step 5: Add foreign keys
        add_foreign_keys(session)
        
        # Step 6: Add indexes
        add_indexes(session)
        
        # Step 7: Create restaurant owner
        create_default_admin_owner(session, default_restaurant_id)
        
        # Step 8: Create subscription plans
        create_subscription_plans(session)
        
        # Step 9: Verify migration
        success = verify_migration(session, default_restaurant_id)
        
        if success:
            print("\n" + "="*80)
            print("MIGRATION COMPLETED SUCCESSFULLY!")
            print("="*80)
            print(f"\nDefault Restaurant ID: {default_restaurant_id}")
            print("You can now restart your application.")
        else:
            print("\n" + "="*80)
            print("MIGRATION COMPLETED WITH WARNINGS")
            print("="*80)
            print("Please review the output above for any errors.")
        
    except Exception as e:
        session.rollback()
        print(f"\n✗ MIGRATION FAILED: {e}")
        print("\nPlease restore from backup and contact support.")
        sys.exit(1)
    
    finally:
        session.close()

if __name__ == "__main__":
    main()
