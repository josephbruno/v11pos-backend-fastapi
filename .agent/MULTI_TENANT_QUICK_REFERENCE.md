# Multi-Tenant SaaS - Quick Reference Guide

## 🎯 What Has Changed

Your single-restaurant POS system is being converted to a **Multi-Tenant SaaS Platform** where:
- Multiple restaurants can use the same system
- Each restaurant has completely isolated data
- Each restaurant manages their own staff and settings
- Centralized subscription and billing management

---

## 📁 New Files Created

### Models
- `app/models/restaurant.py` - 7 new models for multi-tenancy

### Scripts
- `migrate_to_multi_tenant.py` - Database migration script

### Documentation
- `.agent/PROJECT_ANALYSIS.md` - Complete project analysis
- `.agent/MULTI_TENANT_IMPLEMENTATION_PLAN.md` - Detailed implementation plan
- `.agent/MULTI_TENANT_PROGRESS.md` - Progress tracking
- `.agent/MULTI_TENANT_QUICK_REFERENCE.md` - This file

---

## 🗄️ New Database Tables

### Core Multi-Tenant Tables

**restaurants** - Each restaurant (tenant)
```sql
- id (PK)
- name, slug, business_name
- email, phone, address
- subscription_plan, subscription_status
- max_users, max_products, max_orders_per_month
- is_active, is_verified
```

**restaurant_owners** - Restaurant ownership
```sql
- id (PK)
- restaurant_id (FK)
- user_id (FK)
- role (owner, co_owner)
```

**subscriptions** - Subscription tracking
```sql
- id (PK)
- restaurant_id (FK)
- plan, status
- price_per_month, billing_cycle
- current_period_start, current_period_end
```

**subscription_plans** - Available plans
```sql
- id (PK)
- name (trial, basic, pro, enterprise)
- price_monthly, price_yearly
- max_users, max_products, max_orders_per_month
- features (JSON)
```

**invoices** - Billing invoices
```sql
- id (PK)
- subscription_id (FK)
- invoice_number, amount, status
- invoice_date, due_date, paid_at
```

**platform_admins** - Super admins
```sql
- id (PK)
- user_id (FK)
- role, permissions
- can_access_all_restaurants
```

**restaurant_invitations** - Team invitations
```sql
- id (PK)
- restaurant_id (FK)
- email, role, token
- status, expires_at
```

---

## 🔄 Modified Tables

All existing tables now have:
- `restaurant_id` column (Foreign Key to restaurants)
- Index on `restaurant_id`
- Foreign key constraint with CASCADE delete

**Modified Tables:**
- users, shift_schedules, staff_performance
- categories, products, modifiers, modifier_options
- product_modifiers, combo_products, combo_items
- customers, customer_tags, customer_tag_mapping
- loyalty_rules, loyalty_transactions
- orders, order_items, order_item_modifiers
- kot_groups, order_taxes, order_status_history
- qr_tables, qr_sessions, qr_settings
- tax_rules, settings, translations

---

## 🔐 Authentication Changes

### Old JWT Token
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "role": "admin"
}
```

### New JWT Token
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "role": "restaurant_admin",
  "restaurant_id": "restaurant-uuid",
  "restaurant_slug": "my-restaurant",
  "is_platform_admin": false
}
```

### New User Roles

**Platform Level:**
- `platform_admin` - Manages entire SaaS
- `platform_support` - Customer support

**Restaurant Level:**
- `restaurant_owner` - Full control of restaurant
- `restaurant_admin` - Admin access
- `manager` - Manage operations
- `staff` - Limited access
- `cashier` - POS only

---

## 🛣️ New API Endpoints

### Platform Management (Platform Admin Only)
```
POST   /api/v1/platform/restaurants
GET    /api/v1/platform/restaurants
GET    /api/v1/platform/restaurants/{id}
PUT    /api/v1/platform/restaurants/{id}
DELETE /api/v1/platform/restaurants/{id}
PUT    /api/v1/platform/restaurants/{id}/status
GET    /api/v1/platform/analytics/overview
```

### Restaurant Onboarding (Public)
```
POST   /api/v1/onboarding/register
POST   /api/v1/onboarding/verify-email
POST   /api/v1/onboarding/complete
GET    /api/v1/onboarding/status
```

### Subscription Management (Restaurant Owner)
```
GET    /api/v1/subscriptions/plans
GET    /api/v1/subscriptions/current
POST   /api/v1/subscriptions/upgrade
POST   /api/v1/subscriptions/cancel
GET    /api/v1/subscriptions/invoices
POST   /api/v1/subscriptions/payment-method
```

### Restaurant Settings (Restaurant Owner)
```
GET    /api/v1/restaurant/settings
PUT    /api/v1/restaurant/settings
PUT    /api/v1/restaurant/branding
GET    /api/v1/restaurant/team
POST   /api/v1/restaurant/team/invite
DELETE /api/v1/restaurant/team/{user_id}
```

---

## 💰 Subscription Plans

### Trial (Free - 14 days)
- 2 users
- 50 products
- 100 orders/month
- Basic features

### Basic ($29/month)
- 5 users
- 200 products
- 1,000 orders/month
- QR ordering
- Basic analytics

### Pro ($79/month) - Most Popular
- 15 users
- 1,000 products
- 10,000 orders/month
- Advanced analytics
- Loyalty program
- Multi-location (3 locations)

### Enterprise ($199/month)
- Unlimited users
- Unlimited products
- Unlimited orders
- All features
- API access
- Dedicated support

---

## 🚀 Running the Migration

### Prerequisites
```bash
# 1. BACKUP YOUR DATABASE!
mysqldump -u root -p restaurant_pos > backup_$(date +%Y%m%d).sql

# 2. Test on development first
# Create a copy of your database for testing
```

### Run Migration
```bash
# The script will ask for confirmation
python migrate_to_multi_tenant.py
```

### What the Migration Does
1. Creates new multi-tenant tables
2. Creates a default restaurant for existing data
3. Adds `restaurant_id` to all existing tables
4. Populates `restaurant_id` with default restaurant ID
5. Adds foreign key constraints
6. Creates indexes for performance
7. Creates restaurant owner for existing admin
8. Creates 4 subscription plans
9. Verifies migration success

### After Migration
```bash
# Restart your application
docker-compose restart

# Or if running locally
# Stop and start your server
```

---

## 🔍 How to Query Data Now

### Old Way (Single Restaurant)
```python
# Get all products
products = db.query(Product).all()
```

### New Way (Multi-Tenant)
```python
# Get products for specific restaurant
products = db.query(Product).filter(
    Product.restaurant_id == restaurant_id
).all()
```

### Using Middleware (Recommended)
```python
@router.get("/products")
async def list_products(
    restaurant_id: str = Depends(get_current_restaurant),
    db: Session = Depends(get_db)
):
    # restaurant_id automatically extracted from JWT token
    products = db.query(Product).filter(
        Product.restaurant_id == restaurant_id
    ).all()
    return products
```

---

## ⚠️ Important Security Rules

### 1. Always Filter by restaurant_id
```python
# ✅ CORRECT
products = db.query(Product).filter(
    Product.restaurant_id == restaurant_id
).all()

# ❌ WRONG - Returns data from ALL restaurants!
products = db.query(Product).all()
```

### 2. Never Trust Client Input
```python
# ❌ WRONG - Client could send any restaurant_id
restaurant_id = request.json.get('restaurant_id')

# ✅ CORRECT - Get from authenticated JWT token
restaurant_id = token_data.get('restaurant_id')
```

### 3. Validate Ownership
```python
# Before updating a product
product = db.query(Product).filter(
    Product.id == product_id,
    Product.restaurant_id == restaurant_id  # Ensure it belongs to this restaurant
).first()

if not product:
    raise HTTPException(status_code=404, detail="Product not found")
```

---

## 📊 Usage Limit Enforcement

### Check Before Creating
```python
@router.post("/products")
async def create_product(
    product_data: ProductCreate,
    restaurant_id: str = Depends(get_current_restaurant),
    db: Session = Depends(get_db)
):
    # Get restaurant
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()
    
    # Check product limit
    current_products = db.query(Product).filter(
        Product.restaurant_id == restaurant_id
    ).count()
    
    if current_products >= restaurant.max_products:
        raise HTTPException(
            status_code=403,
            detail=f"Product limit reached ({restaurant.max_products}). Please upgrade your plan."
        )
    
    # Create product...
```

### Update Usage Counters
```python
# After creating a user
restaurant.current_users += 1
db.commit()

# After creating a product
restaurant.current_products += 1
db.commit()

# Reset monthly order counter (scheduled job)
# Run on 1st of each month
restaurant.current_orders_this_month = 0
db.commit()
```

---

## 🧪 Testing Multi-Tenancy

### Create Test Restaurants
```python
# Create Restaurant A
restaurant_a = Restaurant(
    name="Restaurant A",
    slug="restaurant-a",
    email="a@test.com",
    phone="1111111111"
)
db.add(restaurant_a)

# Create Restaurant B
restaurant_b = Restaurant(
    name="Restaurant B",
    slug="restaurant-b",
    email="b@test.com",
    phone="2222222222"
)
db.add(restaurant_b)
db.commit()
```

### Test Data Isolation
```python
# Create product for Restaurant A
product_a = Product(
    restaurant_id=restaurant_a.id,
    name="Product A",
    price=1000
)
db.add(product_a)

# Create product for Restaurant B
product_b = Product(
    restaurant_id=restaurant_b.id,
    name="Product B",
    price=2000
)
db.add(product_b)
db.commit()

# Query for Restaurant A - should only return Product A
products_a = db.query(Product).filter(
    Product.restaurant_id == restaurant_a.id
).all()
assert len(products_a) == 1
assert products_a[0].name == "Product A"

# Query for Restaurant B - should only return Product B
products_b = db.query(Product).filter(
    Product.restaurant_id == restaurant_b.id
).all()
assert len(products_b) == 1
assert products_b[0].name == "Product B"
```

---

## 🐛 Common Issues & Solutions

### Issue: "restaurant_id cannot be null"
**Solution:** Make sure you're setting restaurant_id when creating records
```python
product = Product(
    restaurant_id=restaurant_id,  # Don't forget this!
    name="My Product",
    price=1000
)
```

### Issue: "Foreign key constraint fails"
**Solution:** Ensure the restaurant exists before creating related records
```python
restaurant = db.query(Restaurant).filter(
    Restaurant.id == restaurant_id
).first()
if not restaurant:
    raise HTTPException(status_code=404, detail="Restaurant not found")
```

### Issue: "Seeing data from other restaurants"
**Solution:** You forgot to filter by restaurant_id
```python
# Add this filter to ALL queries
.filter(Model.restaurant_id == restaurant_id)
```

---

## 📈 Monitoring & Metrics

### Restaurant-Level Metrics
- Active users count
- Products count
- Orders this month
- Revenue this month
- Storage used

### Platform-Level Metrics
- Total restaurants
- Active subscriptions
- Churn rate
- MRR (Monthly Recurring Revenue)
- Average revenue per restaurant

---

## 🔄 Rollback Plan

If migration fails:

```bash
# 1. Stop application
docker-compose down

# 2. Restore database from backup
mysql -u root -p restaurant_pos < backup_YYYYMMDD.sql

# 3. Revert code changes
git checkout main  # or your previous branch

# 4. Restart application
docker-compose up -d
```

---

## 📞 Support

If you encounter issues:

1. Check the migration output for errors
2. Review `.agent/MULTI_TENANT_PROGRESS.md` for status
3. Check database logs
4. Verify all foreign keys are in place
5. Test data isolation between restaurants

---

## ✅ Checklist Before Going Live

- [ ] Database backed up
- [ ] Migration tested on development
- [ ] Migration tested on staging
- [ ] All routes updated to filter by restaurant_id
- [ ] Usage limits implemented
- [ ] Subscription plans configured
- [ ] Payment gateway integrated (if applicable)
- [ ] Data isolation tested
- [ ] Performance tested with multiple tenants
- [ ] Security audit completed
- [ ] Documentation updated
- [ ] Team trained on new features
- [ ] Rollback plan ready

---

## 🎯 Key Takeaways

1. **Every table now has restaurant_id** - Always filter by it
2. **JWT tokens include restaurant context** - Use middleware to extract it
3. **Subscription limits must be enforced** - Check before creating records
4. **Data isolation is critical** - Never query without restaurant_id filter
5. **Platform admins are special** - They can access all restaurants
6. **Migration is one-way** - Always backup before running

---

This is a major architectural change. Take your time, test thoroughly, and don't hesitate to ask questions!
