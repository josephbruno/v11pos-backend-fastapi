"""
Create a SuperAdmin user who can monitor all restaurants
"""
from app.database import SessionLocal
from app.models.user import User
from app.models.restaurant import PlatformAdmin
from app.security import hash_password
import uuid
from datetime import datetime

def create_superadmin(
    name: str,
    email: str,
    password: str,
    phone: str = "0000000000"
):
    """
    Create a SuperAdmin user with platform-wide access
    
    Args:
        name: Admin name
        email: Admin email
        password: Admin password
        phone: Admin phone number
    """
    db = SessionLocal()
    
    try:
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"❌ User with email {email} already exists!")
            
            # Check if already a platform admin
            existing_admin = db.query(PlatformAdmin).filter(
                PlatformAdmin.user_id == existing_user.id
            ).first()
            
            if existing_admin:
                print(f"✅ User is already a Platform Admin!")
                return existing_user, existing_admin
            else:
                # Make existing user a platform admin
                print(f"🔄 Converting existing user to Platform Admin...")
                platform_admin = PlatformAdmin(
                    id=str(uuid.uuid4()),
                    user_id=existing_user.id,
                    role='admin',
                    permissions=['*'],  # All permissions
                    can_access_all_restaurants=True,
                    can_modify_subscriptions=True,
                    can_suspend_restaurants=True,
                    is_active=True
                )
                db.add(platform_admin)
                db.commit()
                print(f"✅ User converted to Platform Admin!")
                return existing_user, platform_admin
        
        # Create new user (without restaurant_id - platform admin)
        user_id = str(uuid.uuid4())
        hashed_password = hash_password(password)
        
        user = User(
            id=user_id,
            restaurant_id=None,  # Platform admins don't belong to a restaurant
            name=name,
            email=email,
            phone=phone,
            password=hashed_password,
            role='admin',  # User role
            status='active'
        )
        
        db.add(user)
        db.flush()
        
        # Create platform admin record
        platform_admin = PlatformAdmin(
            id=str(uuid.uuid4()),
            user_id=user_id,
            role='admin',  # Platform admin role
            permissions=['*'],  # All permissions
            can_access_all_restaurants=True,
            can_modify_subscriptions=True,
            can_suspend_restaurants=True,
            is_active=True
        )
        
        db.add(platform_admin)
        db.commit()
        db.refresh(user)
        db.refresh(platform_admin)
        
        print("\n" + "=" * 60)
        print("✅ SUPERADMIN CREATED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\n👤 User Details:")
        print(f"   - ID: {user.id}")
        print(f"   - Name: {user.name}")
        print(f"   - Email: {user.email}")
        print(f"   - Role: Platform Admin (SuperAdmin)")
        print(f"   - Status: {user.status}")
        
        print(f"\n🔐 Platform Admin Permissions:")
        print(f"   - Access All Restaurants: ✓")
        print(f"   - Modify Subscriptions: ✓")
        print(f"   - Suspend Restaurants: ✓")
        print(f"   - All Permissions: ✓")
        
        print(f"\n🔑 Login Credentials:")
        print(f"   - Email: {email}")
        print(f"   - Password: {password}")
        
        print("\n" + "=" * 60 + "\n")
        
        return user, platform_admin
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error creating SuperAdmin: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


def list_superadmins():
    """List all SuperAdmin users"""
    db = SessionLocal()
    
    try:
        print("\n" + "=" * 60)
        print("👥 PLATFORM ADMINS (SUPERADMINS)")
        print("=" * 60)
        
        platform_admins = db.query(PlatformAdmin).filter(
            PlatformAdmin.is_active == True
        ).all()
        
        if not platform_admins:
            print("\n⚠️  No Platform Admins found!")
            return []
        
        print(f"\n📊 Total Active Platform Admins: {len(platform_admins)}")
        
        for admin in platform_admins:
            user = db.query(User).filter(User.id == admin.user_id).first()
            if user:
                print(f"\n👤 {user.name}")
                print(f"   - Email: {user.email}")
                print(f"   - User ID: {user.id}")
                print(f"   - Platform Admin ID: {admin.id}")
                print(f"   - Role: {admin.role}")
                print(f"   - Status: {'Active' if admin.is_active else 'Inactive'}")
                print(f"   - Created: {admin.created_at}")
        
        print("\n" + "=" * 60 + "\n")
        
        return platform_admins
        
    finally:
        db.close()


def test_superadmin_login(email: str, password: str):
    """Test SuperAdmin login"""
    from app.security import verify_password
    
    db = SessionLocal()
    
    try:
        print("\n" + "=" * 60)
        print("🔐 TESTING SUPERADMIN LOGIN")
        print("=" * 60)
        
        # Find user
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"\n❌ User not found with email: {email}")
            return False
        
        # Verify password
        if not verify_password(password, user.password):
            print(f"\n❌ Invalid password!")
            return False
        
        # Check if platform admin
        platform_admin = db.query(PlatformAdmin).filter(
            PlatformAdmin.user_id == user.id,
            PlatformAdmin.is_active == True
        ).first()
        
        if not platform_admin:
            print(f"\n❌ User is not a Platform Admin!")
            return False
        
        print(f"\n✅ Login successful!")
        print(f"\n👤 Logged in as: {user.name}")
        print(f"   - Email: {user.email}")
        print(f"   - Platform Admin: Yes")
        print(f"   - Can Access All Restaurants: {platform_admin.can_access_all_restaurants}")
        
        # Show what they can do
        print(f"\n🔐 Permissions:")
        print(f"   ✓ View all restaurants")
        print(f"   ✓ Monitor all orders and sales")
        print(f"   ✓ Manage subscriptions")
        print(f"   ✓ Suspend/activate restaurants")
        print(f"   ✓ View platform analytics")
        print(f"   ✓ Access all data across tenants")
        
        print("\n" + "=" * 60 + "\n")
        
        return True
        
    finally:
        db.close()


def main():
    """Main function"""
    import sys
    
    print("\n" + "=" * 60)
    print("🚀 SUPERADMIN MANAGEMENT")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python3 create_superadmin.py create <name> <email> <password> [phone]")
        print("  python3 create_superadmin.py list")
        print("  python3 create_superadmin.py test <email> <password>")
        print("\nExamples:")
        print("  python3 create_superadmin.py create 'Admin User' admin@platform.com admin123")
        print("  python3 create_superadmin.py list")
        print("  python3 create_superadmin.py test admin@platform.com admin123")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "create":
        if len(sys.argv) < 5:
            print("\n❌ Missing arguments!")
            print("Usage: python3 create_superadmin.py create <name> <email> <password> [phone]")
            sys.exit(1)
        
        name = sys.argv[2]
        email = sys.argv[3]
        password = sys.argv[4]
        phone = sys.argv[5] if len(sys.argv) > 5 else "0000000000"
        
        create_superadmin(name, email, password, phone)
    
    elif command == "list":
        list_superadmins()
    
    elif command == "test":
        if len(sys.argv) < 4:
            print("\n❌ Missing arguments!")
            print("Usage: python3 create_superadmin.py test <email> <password>")
            sys.exit(1)
        
        email = sys.argv[2]
        password = sys.argv[3]
        
        test_superadmin_login(email, password)
    
    else:
        print(f"\n❌ Unknown command: {command}")
        print("Available commands: create, list, test")
        sys.exit(1)


if __name__ == "__main__":
    main()
