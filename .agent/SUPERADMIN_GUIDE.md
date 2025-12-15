# 🎉 SUPERADMIN ROLE - COMPLETE GUIDE

## ✅ SUPERADMIN CREATED SUCCESSFULLY!

### 👤 SuperAdmin Details:
```
Name:     Super Admin
Email:    admin@platform.com
Password: admin123
Phone:    9999999999
Role:     Platform Admin (SuperAdmin)
Status:   Active
```

---

## 🔐 SUPERADMIN CAPABILITIES

### What SuperAdmin Can Do:
1. ✅ **Access ALL Restaurants** - View and manage any restaurant
2. ✅ **Monitor All Orders** - See orders across all tenants
3. ✅ **View All Sales** - Platform-wide analytics
4. ✅ **Manage Subscriptions** - Upgrade/downgrade any restaurant
5. ✅ **Suspend/Activate Restaurants** - Control restaurant access
6. ✅ **View Platform Analytics** - System-wide metrics
7. ✅ **Access All Data** - Cross-tenant data access
8. ✅ **Manage Platform Settings** - System configuration

### Special Features:
- ❌ **No Restaurant ID** - SuperAdmin doesn't belong to any restaurant
- ✅ **Bypass Tenant Isolation** - Can access data across all tenants
- ✅ **Platform-Wide Permissions** - All permissions (`*`)
- ✅ **JWT Token Flag** - `is_platform_admin: true` in token

---

## 🚀 HOW TO USE SUPERADMIN

### 1. Login as SuperAdmin

**API Request:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@platform.com",
    "password": "admin123"
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ...",
    "token_type": "bearer",
    "restaurant_id": null,
    "restaurant_slug": null,
    "user": {
      "id": "100916ad-178f-44fd-a4ee-3b92f906d0a2",
      "name": "Super Admin",
      "email": "admin@platform.com",
      "role": "admin",
      "status": "active",
      "restaurant_id": null
    }
  }
}
```

**JWT Token Payload:**
```json
{
  "user_id": "100916ad-178f-44fd-a4ee-3b92f906d0a2",
  "email": "admin@platform.com",
  "role": "admin",
  "restaurant_id": null,
  "restaurant_slug": null,
  "is_platform_admin": true,
  "type": "access",
  "exp": 1234567890
}
```

---

## 📋 SUPERADMIN MANAGEMENT COMMANDS

### Create a New SuperAdmin:
```bash
python3 create_superadmin.py create "Admin Name" admin@email.com password123 "1234567890"
```

### List All SuperAdmins:
```bash
python3 create_superadmin.py list
```

### Test SuperAdmin Login:
```bash
python3 create_superadmin.py test admin@platform.com admin123
```

---

## 🔧 SUPERADMIN API ROUTES

### Routes That Need to Be Created:

#### 1. Platform Admin Dashboard
```python
# app/routes/platform_admin.py

@router.get("/api/v1/platform/dashboard")
async def platform_dashboard(
    token_data: dict = Depends(require_platform_admin),
    db: Session = Depends(get_db)
):
    """Platform-wide dashboard for SuperAdmin"""
    # Get all restaurants
    restaurants = db.query(Restaurant).all()
    
    # Get total stats
    total_users = db.query(User).count()
    total_products = db.query(Product).count()
    total_orders = db.query(Order).count()
    
    return {
        "total_restaurants": len(restaurants),
        "total_users": total_users,
        "total_products": total_products,
        "total_orders": total_orders,
        "restaurants": restaurants
    }
```

#### 2. View All Restaurants
```python
@router.get("/api/v1/platform/restaurants")
async def list_all_restaurants(
    token_data: dict = Depends(require_platform_admin),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """List all restaurants (SuperAdmin only)"""
    restaurants = db.query(Restaurant).offset(skip).limit(limit).all()
    return {"restaurants": restaurants}
```

#### 3. View Restaurant Details
```python
@router.get("/api/v1/platform/restaurants/{restaurant_id}")
async def get_restaurant_details(
    restaurant_id: str,
    token_data: dict = Depends(require_platform_admin),
    db: Session = Depends(get_db)
):
    """Get detailed restaurant info (SuperAdmin only)"""
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()
    
    if not restaurant:
        raise HTTPException(404, "Restaurant not found")
    
    # Get restaurant stats
    users = db.query(User).filter(User.restaurant_id == restaurant_id).count()
    products = db.query(Product).filter(Product.restaurant_id == restaurant_id).count()
    orders = db.query(Order).filter(Order.restaurant_id == restaurant_id).count()
    
    return {
        "restaurant": restaurant,
        "stats": {
            "users": users,
            "products": products,
            "orders": orders
        }
    }
```

#### 4. Suspend/Activate Restaurant
```python
@router.put("/api/v1/platform/restaurants/{restaurant_id}/status")
async def update_restaurant_status(
    restaurant_id: str,
    is_active: bool,
    suspension_reason: Optional[str] = None,
    token_data: dict = Depends(require_platform_admin),
    db: Session = Depends(get_db)
):
    """Suspend or activate a restaurant (SuperAdmin only)"""
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()
    
    if not restaurant:
        raise HTTPException(404, "Restaurant not found")
    
    restaurant.is_active = is_active
    restaurant.is_suspended = not is_active
    if suspension_reason:
        restaurant.suspension_reason = suspension_reason
    
    db.commit()
    
    return {"message": f"Restaurant {'activated' if is_active else 'suspended'}"}
```

#### 5. View All Orders (Cross-Tenant)
```python
@router.get("/api/v1/platform/orders")
async def list_all_orders(
    token_data: dict = Depends(require_platform_admin),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """List all orders across all restaurants (SuperAdmin only)"""
    orders = db.query(Order).offset(skip).limit(limit).all()
    return {"orders": orders}
```

#### 6. Platform Analytics
```python
@router.get("/api/v1/platform/analytics")
async def platform_analytics(
    token_data: dict = Depends(require_platform_admin),
    db: Session = Depends(get_db)
):
    """Platform-wide analytics (SuperAdmin only)"""
    from sqlalchemy import func
    
    # Revenue by restaurant
    revenue_by_restaurant = db.query(
        Restaurant.name,
        func.sum(Order.total).label('total_revenue')
    ).join(Order).group_by(Restaurant.id).all()
    
    # Orders by status
    orders_by_status = db.query(
        Order.status,
        func.count(Order.id).label('count')
    ).group_by(Order.status).all()
    
    return {
        "revenue_by_restaurant": revenue_by_restaurant,
        "orders_by_status": orders_by_status
    }
```

---

## 🔐 MIDDLEWARE USAGE

### Using SuperAdmin Middleware:

```python
from app.dependencies import require_platform_admin

@router.get("/admin-only-endpoint")
async def admin_endpoint(
    token_data: dict = Depends(require_platform_admin),
    db: Session = Depends(get_db)
):
    """This endpoint requires platform admin access"""
    # Only SuperAdmins can access this
    return {"message": "Welcome, SuperAdmin!"}
```

### Checking Platform Admin in Code:

```python
from app.dependencies import verify_token

@router.get("/some-endpoint")
async def some_endpoint(
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    is_platform_admin = token_data.get("is_platform_admin", False)
    
    if is_platform_admin:
        # SuperAdmin can access all data
        data = db.query(Model).all()
    else:
        # Regular users see only their restaurant data
        restaurant_id = token_data.get("restaurant_id")
        data = db.query(Model).filter(
            Model.restaurant_id == restaurant_id
        ).all()
    
    return {"data": data}
```

---

## 📊 SUPERADMIN VS RESTAURANT ADMIN

### Comparison:

| Feature | SuperAdmin | Restaurant Admin |
|---------|-----------|------------------|
| Access Scope | All Restaurants | Single Restaurant |
| Restaurant ID | None (null) | Has restaurant_id |
| Can View Other Restaurants | ✅ Yes | ❌ No |
| Can Manage Subscriptions | ✅ Yes | ❌ No |
| Can Suspend Restaurants | ✅ Yes | ❌ No |
| Platform Analytics | ✅ Yes | ❌ No |
| Manage Own Restaurant | ❌ No | ✅ Yes |
| JWT Flag | is_platform_admin: true | is_platform_admin: false |

---

## 🎯 USE CASES

### When to Use SuperAdmin:

1. **Platform Monitoring** - Monitor all restaurants' health
2. **Customer Support** - Help restaurants with issues
3. **Subscription Management** - Upgrade/downgrade plans
4. **Compliance** - Ensure all restaurants follow rules
5. **Analytics** - Platform-wide business intelligence
6. **Troubleshooting** - Debug issues across tenants
7. **Moderation** - Suspend problematic restaurants

### When NOT to Use SuperAdmin:

1. **Regular Operations** - Use restaurant admin instead
2. **Daily Management** - Each restaurant should self-manage
3. **Customer-Facing** - SuperAdmin is for internal use only

---

## 🔒 SECURITY BEST PRACTICES

### SuperAdmin Security:

1. ✅ **Strong Passwords** - Use complex passwords
2. ✅ **Limited Access** - Only create SuperAdmins when needed
3. ✅ **Audit Logging** - Log all SuperAdmin actions
4. ✅ **2FA** - Implement two-factor authentication
5. ✅ **IP Whitelist** - Restrict access by IP
6. ✅ **Session Timeout** - Short session timeouts
7. ✅ **Regular Review** - Audit SuperAdmin list regularly

### Audit Log Example:
```python
# Log SuperAdmin actions
def log_admin_action(admin_id, action, target, details):
    log = AdminAuditLog(
        admin_id=admin_id,
        action=action,
        target=target,
        details=details,
        timestamp=datetime.utcnow()
    )
    db.add(log)
    db.commit()
```

---

## 📝 QUICK REFERENCE

### Current SuperAdmin:
```
Email:    admin@platform.com
Password: admin123
```

### Management Commands:
```bash
# Create SuperAdmin
python3 create_superadmin.py create "Name" email@domain.com password

# List SuperAdmins
python3 create_superadmin.py list

# Test Login
python3 create_superadmin.py test email@domain.com password
```

### API Endpoints to Create:
- GET `/api/v1/platform/dashboard` - Platform overview
- GET `/api/v1/platform/restaurants` - All restaurants
- GET `/api/v1/platform/restaurants/{id}` - Restaurant details
- PUT `/api/v1/platform/restaurants/{id}/status` - Suspend/activate
- GET `/api/v1/platform/orders` - All orders
- GET `/api/v1/platform/analytics` - Platform analytics
- GET `/api/v1/platform/users` - All users
- GET `/api/v1/platform/subscriptions` - All subscriptions

---

## 🎉 SUCCESS!

**SuperAdmin is now ready to monitor all restaurants!**

**Login Credentials:**
- Email: `admin@platform.com`
- Password: `admin123`

**Capabilities:**
- ✅ Access all restaurants
- ✅ Monitor all orders
- ✅ Manage subscriptions
- ✅ Platform analytics
- ✅ Cross-tenant access

**Next Steps:**
1. Create platform admin routes
2. Implement audit logging
3. Add 2FA for SuperAdmin
4. Create admin dashboard UI

---

*SuperAdmin created: 2025-12-15 14:47:04*
*Status: Active and Ready*
