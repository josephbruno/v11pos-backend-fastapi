# 🎉 ALEMBIC MIGRATION SETUP COMPLETE!

## ✅ What's Been Set Up

### 1. Alembic Initialized ✅
- Created `alembic/` directory with migration infrastructure
- Created `alembic/versions/` for migration scripts
- Created `alembic.ini` configuration file
- Updated `alembic/env.py` to use app database configuration

### 2. First Migration Created ✅
- **Migration File:** `alembic/versions/133309f277b9_add_multi_tenant_schema.py`
- **Detected Changes:**
  - 7 new tables created (restaurants, subscriptions, etc.)
  - 27 existing tables updated with `restaurant_id`
  - All indexes and foreign keys added
  - Unique constraints removed where needed

### 3. Fixed Issues ✅
- Renamed `metadata` to `extra_data` in Subscription and Invoice models (SQLAlchemy reserved name)
- Added missing `ForeignKey` import in settings.py
- Configured Alembic to use app database URL

---

## 🚀 HOW TO USE ALEMBIC

### Basic Commands

#### 1. Check Current Migration Status
```bash
cd /home/brunodoss/docs/pos/pos/pos-fastapi
alembic current
```

#### 2. View Migration History
```bash
alembic history
```

#### 3. Apply Migrations (Upgrade Database)
```bash
# Upgrade to latest
alembic upgrade head

# Upgrade one version
alembic upgrade +1

# Upgrade to specific revision
alembic upgrade 133309f277b9
```

#### 4. Rollback Migrations (Downgrade)
```bash
# Downgrade one version
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade 133309f277b9

# Downgrade all (back to empty database)
alembic downgrade base
```

#### 5. Create New Migration
```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description_of_changes"

# Create empty migration (manual)
alembic revision -m "description_of_changes"
```

---

## 📋 STEP-BY-STEP MIGRATION GUIDE

### Step 1: Backup Your Database ⚠️
```bash
# MySQL backup
mysqldump -u root -p restaurant_pos > backup_$(date +%Y%m%d_%H%M%S).sql

# Or use your database management tool
```

### Step 2: Review the Migration
```bash
# View the generated migration file
cat alembic/versions/133309f277b9_add_multi_tenant_schema.py

# Check what will be applied
alembic upgrade head --sql > migration_preview.sql
```

### Step 3: Test on Development Database First
```bash
# Make sure you're connected to DEV database (check .env)
cat .env | grep DB_

# Apply migration
alembic upgrade head
```

### Step 4: Verify Migration Success
```bash
# Check current version
alembic current

# Verify tables exist
mysql -u root -p restaurant_pos -e "SHOW TABLES;"

# Check restaurant table structure
mysql -u root -p restaurant_pos -e "DESCRIBE restaurants;"
```

### Step 5: Seed Initial Data
```bash
# Run seed script to create default restaurant and subscription plans
python seed_multi_tenant_data.py
```

---

## 🔧 MIGRATION WORKFLOW

### For Development:
```bash
# 1. Make changes to models
# 2. Generate migration
alembic revision --autogenerate -m "add_new_feature"

# 3. Review generated migration
# 4. Apply migration
alembic upgrade head

# 5. Test your changes
```

### For Production:
```bash
# 1. Test migration on staging first
# 2. Backup production database
# 3. Put application in maintenance mode
# 4. Apply migration
alembic upgrade head

# 5. Verify migration
alembic current

# 6. Restart application
# 7. Remove maintenance mode
# 8. Monitor for issues
```

---

## 📝 IMPORTANT NOTES

### Database URL Configuration
Alembic uses the database URL from `app/database.py`:
```python
db_url = f"mysql+pymysql://{settings.db_user}:{quote_plus(settings.db_password)}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
```

This is automatically loaded from your `.env` file:
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=restaurant_pos
```

### Migration File Location
All migrations are stored in: `alembic/versions/`

### Alembic Version Table
Alembic creates a table called `alembic_version` in your database to track which migrations have been applied.

---

## 🎯 COMMON TASKS

### 1. Apply the Multi-Tenant Migration
```bash
# Make sure you're in the project directory
cd /home/brunodoss/docs/pos/pos/pos-fastapi

# Backup database first!
mysqldump -u root -p restaurant_pos > backup_before_multitenant.sql

# Apply migration
alembic upgrade head

# Verify
alembic current
```

### 2. Create a Default Restaurant
After migration, create a default restaurant for existing data:
```python
# Create a Python script or use Python shell
from app.database import SessionLocal
from app.models.restaurant import Restaurant, SubscriptionPlan
from datetime import datetime, timedelta
import uuid

db = SessionLocal()

# Create default restaurant
restaurant = Restaurant(
    id=str(uuid.uuid4()),
    name="Default Restaurant",
    slug="default",
    business_name="Default Restaurant",
    email="admin@restaurant.com",
    phone="1234567890",
    subscription_plan="trial",
    subscription_status="active",
    trial_ends_at=datetime.utcnow() + timedelta(days=14),
    is_active=True
)
db.add(restaurant)
db.commit()

print(f"Created restaurant: {restaurant.id}")
```

### 3. Update Existing Data
After creating the default restaurant, update existing records:
```sql
-- Update all users
UPDATE users SET restaurant_id = 'YOUR_RESTAURANT_ID' WHERE restaurant_id IS NULL;

-- Update all products
UPDATE products SET restaurant_id = 'YOUR_RESTAURANT_ID' WHERE restaurant_id IS NULL;

-- Update all orders
UPDATE orders SET restaurant_id = 'YOUR_RESTAURANT_ID' WHERE restaurant_id IS NULL;

-- ... repeat for all tables
```

### 4. Rollback if Needed
```bash
# If something goes wrong, rollback
alembic downgrade -1

# Restore from backup
mysql -u root -p restaurant_pos < backup_before_multitenant.sql
```

---

## 🐛 TROUBLESHOOTING

### Issue: "Can't locate revision identified by 'head'"
**Solution:** This means no migrations have been applied yet.
```bash
alembic upgrade head
```

### Issue: "Target database is not up to date"
**Solution:** Apply pending migrations
```bash
alembic upgrade head
```

### Issue: "Multiple head revisions are present"
**Solution:** Merge the heads
```bash
alembic merge heads -m "merge_heads"
alembic upgrade head
```

### Issue: Migration fails midway
**Solution:**
1. Check the error message
2. Fix the issue in the migration file
3. Rollback: `alembic downgrade -1`
4. Apply again: `alembic upgrade head`

---

## 📊 MIGRATION CHECKLIST

### Before Running Migration:
- [ ] Backup database
- [ ] Test on development database
- [ ] Review migration file
- [ ] Check database connection settings
- [ ] Plan for downtime (if production)

### After Running Migration:
- [ ] Verify migration applied: `alembic current`
- [ ] Check new tables exist
- [ ] Verify foreign keys created
- [ ] Test application functionality
- [ ] Monitor for errors

---

## 🎉 NEXT STEPS

### 1. Apply the Migration
```bash
cd /home/brunodoss/docs/pos/pos/pos-fastapi
alembic upgrade head
```

### 2. Create Seed Data
Create subscription plans and default restaurant:
```bash
python seed_multi_tenant_data.py
```

### 3. Test the System
- Register a new restaurant via onboarding
- Login with restaurant context
- Test data isolation

### 4. Update Remaining Routes
Continue updating the remaining API routes to use restaurant filtering.

---

## 📚 ADDITIONAL RESOURCES

### Alembic Documentation
- Official Docs: https://alembic.sqlalchemy.org/
- Tutorial: https://alembic.sqlalchemy.org/en/latest/tutorial.html
- Auto-generate: https://alembic.sqlalchemy.org/en/latest/autogenerate.html

### Project Files
- Migration file: `alembic/versions/133309f277b9_add_multi_tenant_schema.py`
- Alembic config: `alembic.ini`
- Alembic env: `alembic/env.py`
- Database config: `app/database.py`

---

**You're all set! Alembic is configured and ready to manage your database migrations! 🚀**

**To apply the multi-tenant migration:**
```bash
alembic upgrade head
```
