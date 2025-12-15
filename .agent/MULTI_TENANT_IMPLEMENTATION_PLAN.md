# Multi-Tenant SaaS Conversion - Implementation Plan

## 🎯 Overview

Convert the single-restaurant POS system into a **Multi-Tenant SaaS Platform** where:
- Multiple restaurants can use the same system
- Each restaurant has isolated data
- Each restaurant manages their own staff
- Centralized billing and subscription management
- Restaurant owners can customize their settings

---

## 🏗️ Architecture Changes

### Multi-Tenancy Strategy: **Shared Database with Tenant Isolation**

**Approach:** Single database with `restaurant_id` foreign key in all tables
- ✅ Cost-effective (shared infrastructure)
- ✅ Easy to maintain and backup
- ✅ Efficient resource usage
- ✅ Simple cross-tenant analytics for platform owner

**Alternative Approaches Considered:**
- ❌ Separate Database per Tenant (expensive, hard to maintain)
- ❌ Separate Schema per Tenant (complex migrations)

---

## 📊 New Models Required

### 1. **Restaurant** (Tenant Model)
The core tenant entity representing each restaurant business.

```python
class Restaurant(Base):
    __tablename__ = "restaurants"
    
    # Identity
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    
    # Business Information
    business_name = Column(String(200), nullable=False)
    business_type = Column(String(50))  # cafe, restaurant, bar, food_truck
    cuisine_type = Column(JSON)  # ["italian", "mexican"]
    
    # Contact Information
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    
    # Branding
    logo = Column(String(500))
    primary_color = Column(String(7), default='#00A19D')
    accent_color = Column(String(7), default='#FF6D00')
    
    # Settings
    timezone = Column(String(50), default='UTC')
    currency = Column(String(3), default='USD')
    language = Column(String(5), default='en')
    
    # Subscription & Billing
    subscription_plan = Column(String(50), default='trial')  # trial, basic, pro, enterprise
    subscription_status = Column(String(20), default='active')  # active, suspended, cancelled
    trial_ends_at = Column(DateTime(timezone=True))
    subscription_started_at = Column(DateTime(timezone=True))
    billing_email = Column(String(255))
    
    # Limits (based on plan)
    max_users = Column(Integer, default=5)
    max_products = Column(Integer, default=100)
    max_orders_per_month = Column(Integer, default=1000)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    onboarding_completed = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_activity = Column(DateTime(timezone=True))
    
    # Relationships
    users = relationship("User", back_populates="restaurant")
    categories = relationship("Category", back_populates="restaurant")
    products = relationship("Product", back_populates="restaurant")
    # ... all other models
```

### 2. **RestaurantOwner** (Platform Admin)
Links users to restaurants they own/manage.

```python
class RestaurantOwner(Base):
    __tablename__ = "restaurant_owners"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), default='owner')  # owner, co_owner
    permissions = Column(JSON, default=list)
    invited_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    restaurant = relationship("Restaurant")
    user = relationship("User", foreign_keys=[user_id])
```

### 3. **Subscription** (Billing Management)
Track subscription history and billing.

```python
class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False)
    
    plan = Column(String(50), nullable=False)  # trial, basic, pro, enterprise
    status = Column(String(20), nullable=False)  # active, cancelled, expired, suspended
    
    # Pricing
    price_per_month = Column(Integer, default=0)  # in cents
    billing_cycle = Column(String(20), default='monthly')  # monthly, yearly
    
    # Dates
    started_at = Column(DateTime(timezone=True), nullable=False)
    current_period_start = Column(DateTime(timezone=True))
    current_period_end = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))
    
    # Payment
    payment_method = Column(String(50))  # stripe, paypal, etc.
    payment_gateway_subscription_id = Column(String(255))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    restaurant = relationship("Restaurant")
```

### 4. **SubscriptionPlan** (Plan Configuration)
Define available subscription plans.

```python
class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), unique=True, nullable=False)  # trial, basic, pro, enterprise
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Pricing
    price_monthly = Column(Integer, default=0)  # in cents
    price_yearly = Column(Integer, default=0)  # in cents
    
    # Limits
    max_users = Column(Integer, default=5)
    max_products = Column(Integer, default=100)
    max_orders_per_month = Column(Integer, default=1000)
    max_locations = Column(Integer, default=1)
    
    # Features
    features = Column(JSON, default=list)  # ["qr_ordering", "analytics", "loyalty"]
    
    # Status
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

### 5. **PlatformAdmin** (Super Admin)
Platform administrators who manage the entire SaaS.

```python
class PlatformAdmin(Base):
    __tablename__ = "platform_admins"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    role = Column(String(20), default='admin')  # admin, support, billing
    permissions = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
```

---

## 🔄 Model Modifications Required

### All Existing Models Need:

1. **Add `restaurant_id` foreign key:**
```python
restaurant_id = Column(String(36), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
```

2. **Add relationship:**
```python
restaurant = relationship("Restaurant", back_populates="<model_plural>")
```

3. **Update indexes to include `restaurant_id`:**
```python
__table_args__ = (
    Index('idx_restaurant_entity', 'restaurant_id', 'id'),
    # other indexes
)
```

### Models to Modify:

✅ **User** - Add restaurant_id, user belongs to one restaurant
✅ **Category** - Add restaurant_id
✅ **Product** - Add restaurant_id
✅ **Modifier** - Add restaurant_id
✅ **ModifierOption** - Add restaurant_id
✅ **ProductModifier** - Add restaurant_id
✅ **ComboProduct** - Add restaurant_id
✅ **ComboItem** - Add restaurant_id
✅ **Customer** - Add restaurant_id
✅ **CustomerTag** - Add restaurant_id
✅ **CustomerTagMapping** - Add restaurant_id
✅ **LoyaltyRule** - Add restaurant_id
✅ **LoyaltyTransaction** - Add restaurant_id
✅ **Order** - Add restaurant_id
✅ **OrderItem** - Add restaurant_id (or derive from order)
✅ **OrderItemModifier** - Add restaurant_id (or derive from order)
✅ **KOTGroup** - Add restaurant_id
✅ **OrderTax** - Add restaurant_id
✅ **OrderStatusHistory** - Add restaurant_id
✅ **QRTable** - Add restaurant_id
✅ **QRSession** - Add restaurant_id
✅ **QRSettings** - Add restaurant_id (or make unique per restaurant)
✅ **TaxRule** - Add restaurant_id
✅ **Settings** - Add restaurant_id (or make unique per restaurant)
✅ **Translation** - Add restaurant_id
✅ **ShiftSchedule** - Add restaurant_id
✅ **StaffPerformance** - Add restaurant_id
✅ **PasswordResetToken** - No change needed (user-level)

---

## 🔐 Authentication & Authorization Changes

### New User Roles Hierarchy:

```
Platform Level:
├── platform_admin (manages entire SaaS)
└── platform_support (customer support)

Restaurant Level:
├── restaurant_owner (full control of their restaurant)
├── restaurant_admin (admin access to restaurant)
├── manager (manage operations)
├── staff (limited access)
└── cashier (POS only)
```

### JWT Token Structure Update:

```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "role": "restaurant_admin",
  "restaurant_id": "restaurant-uuid",
  "restaurant_slug": "my-restaurant",
  "is_platform_admin": false,
  "type": "access",
  "exp": 1234567890
}
```

### Middleware Changes:

1. **Add Tenant Context Middleware:**
```python
async def get_current_restaurant(
    token_data: dict = Depends(verify_token)
) -> str:
    """Extract restaurant_id from token"""
    restaurant_id = token_data.get("restaurant_id")
    if not restaurant_id:
        raise HTTPException(status_code=403, detail="No restaurant context")
    return restaurant_id
```

2. **Update All Route Dependencies:**
```python
@router.get("/products")
async def list_products(
    restaurant_id: str = Depends(get_current_restaurant),
    db: Session = Depends(get_db)
):
    # Automatically filter by restaurant_id
    products = db.query(Product).filter(
        Product.restaurant_id == restaurant_id
    ).all()
    return products
```

3. **Add Platform Admin Check:**
```python
async def require_platform_admin(
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
) -> dict:
    """Verify user is platform admin"""
    user_id = token_data.get("user_id")
    admin = db.query(PlatformAdmin).filter(
        PlatformAdmin.user_id == user_id,
        PlatformAdmin.is_active == True
    ).first()
    
    if not admin:
        raise HTTPException(status_code=403, detail="Platform admin access required")
    
    return token_data
```

---

## 🛣️ New API Routes Required

### Restaurant Management (Platform Admin)

```
POST   /api/v1/platform/restaurants              # Create new restaurant
GET    /api/v1/platform/restaurants              # List all restaurants
GET    /api/v1/platform/restaurants/{id}         # Get restaurant details
PUT    /api/v1/platform/restaurants/{id}         # Update restaurant
DELETE /api/v1/platform/restaurants/{id}         # Delete restaurant
PUT    /api/v1/platform/restaurants/{id}/status  # Activate/suspend
GET    /api/v1/platform/restaurants/{id}/stats   # Restaurant statistics
```

### Restaurant Onboarding (Public/Restaurant Owner)

```
POST   /api/v1/onboarding/register               # Register new restaurant
POST   /api/v1/onboarding/verify-email           # Verify email
POST   /api/v1/onboarding/complete               # Complete setup
GET    /api/v1/onboarding/status                 # Check onboarding status
```

### Subscription Management

```
GET    /api/v1/subscriptions/plans               # List available plans
GET    /api/v1/subscriptions/current             # Current subscription
POST   /api/v1/subscriptions/upgrade             # Upgrade plan
POST   /api/v1/subscriptions/cancel              # Cancel subscription
GET    /api/v1/subscriptions/invoices            # Billing history
POST   /api/v1/subscriptions/payment-method      # Update payment
```

### Restaurant Settings (Restaurant Owner)

```
GET    /api/v1/restaurant/settings               # Get restaurant settings
PUT    /api/v1/restaurant/settings               # Update settings
PUT    /api/v1/restaurant/branding               # Update branding
GET    /api/v1/restaurant/team                   # List team members
POST   /api/v1/restaurant/team/invite            # Invite team member
DELETE /api/v1/restaurant/team/{user_id}         # Remove team member
```

### Platform Analytics (Platform Admin)

```
GET    /api/v1/platform/analytics/overview       # Platform overview
GET    /api/v1/platform/analytics/revenue        # Revenue analytics
GET    /api/v1/platform/analytics/restaurants    # Restaurant metrics
GET    /api/v1/platform/analytics/subscriptions  # Subscription stats
```

---

## 🗄️ Database Migration Strategy

### Phase 1: Add New Tables
1. Create `restaurants` table
2. Create `restaurant_owners` table
3. Create `subscriptions` table
4. Create `subscription_plans` table
5. Create `platform_admins` table

### Phase 2: Migrate Existing Data
1. Create a default restaurant for existing data
2. Set `restaurant_id` for all existing records
3. Create restaurant owner for existing admin user

### Phase 3: Add Foreign Keys
1. Add `restaurant_id` column to all tables (nullable initially)
2. Populate `restaurant_id` with default restaurant
3. Make `restaurant_id` NOT NULL
4. Add foreign key constraints
5. Add indexes

### Phase 4: Update Application Code
1. Update all models
2. Update all routes to filter by restaurant_id
3. Update authentication middleware
4. Add new routes for multi-tenancy

### Migration Script Example:

```python
# migrations/add_multi_tenancy.py

def upgrade():
    # 1. Create new tables
    op.create_table('restaurants', ...)
    op.create_table('restaurant_owners', ...)
    op.create_table('subscriptions', ...)
    op.create_table('subscription_plans', ...)
    op.create_table('platform_admins', ...)
    
    # 2. Create default restaurant
    default_restaurant_id = str(uuid.uuid4())
    op.execute(f"""
        INSERT INTO restaurants (id, name, slug, email, phone, is_active, created_at)
        VALUES ('{default_restaurant_id}', 'Default Restaurant', 'default', 
                'admin@restaurant.com', '1234567890', 1, NOW())
    """)
    
    # 3. Add restaurant_id to existing tables
    tables_to_update = [
        'users', 'categories', 'products', 'modifiers', 'modifier_options',
        'product_modifiers', 'combo_products', 'combo_items', 'customers',
        'customer_tags', 'customer_tag_mapping', 'loyalty_rules',
        'loyalty_transactions', 'orders', 'order_items', 'order_item_modifiers',
        'kot_groups', 'order_taxes', 'order_status_history', 'qr_tables',
        'qr_sessions', 'qr_settings', 'tax_rules', 'settings', 'translations',
        'shift_schedules', 'staff_performance'
    ]
    
    for table in tables_to_update:
        # Add column
        op.add_column(table, sa.Column('restaurant_id', sa.String(36), nullable=True))
        
        # Populate with default restaurant
        op.execute(f"UPDATE {table} SET restaurant_id = '{default_restaurant_id}'")
        
        # Make NOT NULL
        op.alter_column(table, 'restaurant_id', nullable=False)
        
        # Add foreign key
        op.create_foreign_key(
            f'fk_{table}_restaurant',
            table, 'restaurants',
            ['restaurant_id'], ['id'],
            ondelete='CASCADE'
        )
        
        # Add index
        op.create_index(f'idx_{table}_restaurant', table, ['restaurant_id'])

def downgrade():
    # Remove foreign keys and columns
    pass
```

---

## 🎨 Frontend Changes Required

### 1. Restaurant Selection
- Add restaurant selector in header (for platform admins)
- Store current restaurant in context/state
- Switch between restaurants without re-login

### 2. Onboarding Flow
- Multi-step registration form
- Email verification
- Business information collection
- Plan selection
- Payment setup (if not trial)

### 3. Subscription Management UI
- Current plan display
- Usage metrics (users, products, orders)
- Upgrade/downgrade options
- Billing history
- Payment method management

### 4. Platform Admin Dashboard
- List all restaurants
- Quick stats per restaurant
- Suspend/activate restaurants
- View restaurant details
- Platform-wide analytics

---

## 📋 Implementation Checklist

### Phase 1: Database & Models (Week 1)
- [ ] Create new models (Restaurant, RestaurantOwner, Subscription, etc.)
- [ ] Create migration script
- [ ] Test migration on development database
- [ ] Update all existing models with restaurant_id
- [ ] Add relationships to Restaurant model

### Phase 2: Authentication & Authorization (Week 1-2)
- [ ] Update JWT token structure
- [ ] Create tenant context middleware
- [ ] Add platform admin checks
- [ ] Update all route dependencies
- [ ] Test authentication flow

### Phase 3: API Routes (Week 2-3)
- [ ] Create restaurant management routes
- [ ] Create onboarding routes
- [ ] Create subscription routes
- [ ] Update all existing routes to filter by restaurant_id
- [ ] Add platform admin routes

### Phase 4: Business Logic (Week 3)
- [ ] Add subscription validation
- [ ] Add usage limit checks
- [ ] Add billing logic
- [ ] Update analytics to be restaurant-specific
- [ ] Add platform-wide analytics

### Phase 5: Testing (Week 4)
- [ ] Unit tests for new models
- [ ] Integration tests for multi-tenancy
- [ ] Test data isolation between restaurants
- [ ] Test subscription limits
- [ ] Load testing

### Phase 6: Documentation (Week 4)
- [ ] Update API documentation
- [ ] Create onboarding guide
- [ ] Create admin guide
- [ ] Update deployment guide

---

## 🚀 Deployment Strategy

### Development Environment
1. Create new branch: `feature/multi-tenant`
2. Implement changes incrementally
3. Test thoroughly with multiple test restaurants

### Staging Environment
1. Deploy to staging
2. Run migration script
3. Test with real-world scenarios
4. Performance testing

### Production Deployment
1. Schedule maintenance window
2. Backup database
3. Run migration script
4. Deploy new code
5. Verify all restaurants working
6. Monitor for issues

---

## 💰 Subscription Plans (Suggested)

### Trial (14 days)
- Free
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

### Pro ($79/month)
- 15 users
- 1,000 products
- 10,000 orders/month
- Advanced analytics
- Loyalty program
- Priority support

### Enterprise (Custom)
- Unlimited users
- Unlimited products
- Unlimited orders
- All features
- Dedicated support
- Custom integrations

---

## 🔒 Security Considerations

1. **Data Isolation:**
   - Always filter by restaurant_id in queries
   - Use database-level row security if available
   - Audit queries for missing restaurant_id filters

2. **Cross-Tenant Access Prevention:**
   - Validate restaurant_id in all requests
   - Never trust client-provided restaurant_id
   - Use middleware to enforce tenant context

3. **API Rate Limiting:**
   - Per-restaurant rate limits
   - Based on subscription plan
   - Prevent abuse

4. **Audit Logging:**
   - Log all cross-restaurant access attempts
   - Track subscription changes
   - Monitor usage limits

---

## 📊 Monitoring & Analytics

### Restaurant-Level Metrics:
- Active users
- Orders per day/month
- Revenue
- Customer count
- Product catalog size

### Platform-Level Metrics:
- Total restaurants
- Active subscriptions
- Churn rate
- MRR (Monthly Recurring Revenue)
- Average order value across platform

---

## 🎯 Success Criteria

✅ Multiple restaurants can operate independently
✅ Complete data isolation between restaurants
✅ Restaurant owners can manage their own team
✅ Subscription plans enforced correctly
✅ Usage limits working properly
✅ Platform admins can manage all restaurants
✅ Onboarding flow is smooth
✅ No performance degradation
✅ All existing features still work
✅ Comprehensive testing completed

---

## 📝 Notes

- This is a major architectural change
- Estimated time: 4-6 weeks for full implementation
- Requires careful testing to ensure data isolation
- Consider using feature flags for gradual rollout
- Plan for data migration carefully
- Have rollback plan ready

---

## 🔄 Next Steps

1. Review and approve this plan
2. Set up development environment
3. Create detailed task breakdown
4. Start with Phase 1 (Database & Models)
5. Implement incrementally with testing at each phase
