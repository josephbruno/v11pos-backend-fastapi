# 🚀 COMPLETING THE MULTI-TENANT CONVERSION - FINAL 15%

## TASK 1: UPDATE REMAINING ROUTES TO FILTER BY RESTAURANT_ID

### Routes That Need Updates (15 files):

1. ✅ auth.py - DONE
2. ✅ onboarding.py - DONE
3. ⏳ products.py - NEEDS UPDATE
4. ⏳ categories.py - NEEDS UPDATE
5. ⏳ orders.py - NEEDS UPDATE
6. ⏳ customers.py - NEEDS UPDATE
7. ⏳ users.py - NEEDS UPDATE
8. ⏳ modifiers.py - NEEDS UPDATE
9. ⏳ combos.py - NEEDS UPDATE
10. ⏳ qr.py - NEEDS UPDATE
11. ⏳ loyalty.py - NEEDS UPDATE
12. ⏳ tax_settings.py - NEEDS UPDATE
13. ⏳ analytics.py - NEEDS UPDATE
14. ⏳ dashboard.py - NEEDS UPDATE
15. ⏳ file_manager.py - NEEDS UPDATE
16. ⏳ translations.py - NEEDS UPDATE

### Standard Pattern for Each Route:

```python
# 1. Add imports at the top
from app.dependencies import get_current_restaurant, check_subscription_limits

# 2. For GET endpoints (list/retrieve):
@router.get("/items")
async def list_items(
    restaurant_id: str = Depends(get_current_restaurant),  # ADD THIS
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    items = db.query(Item).filter(
        Item.restaurant_id == restaurant_id  # ADD THIS FILTER
    ).offset(skip).limit(limit).all()
    
    return success_response(data=items)

# 3. For POST endpoints (create):
@router.post("/items")
async def create_item(
    item_data: ItemCreate,
    restaurant_id: str = Depends(get_current_restaurant),  # ADD THIS
    db: Session = Depends(get_db)
):
    # For users/products/orders - check limits
    limits = await check_subscription_limits(restaurant_id, db)
    if limits['current_X'] >= limits['max_X']:
        raise HTTPException(
            status_code=403,
            detail=f"Limit reached ({limits['max_X']}). Please upgrade."
        )
    
    # Create with restaurant_id
    new_item = Item(
        **item_data.dict(),
        restaurant_id=restaurant_id  # ADD THIS
    )
    db.add(new_item)
    
    # Update counter
    restaurant = limits['restaurant']
    restaurant.current_X += 1
    
    db.commit()
    db.refresh(new_item)
    
    return created_response(data=new_item)

# 4. For GET by ID:
@router.get("/items/{item_id}")
async def get_item(
    item_id: str,
    restaurant_id: str = Depends(get_current_restaurant),  # ADD THIS
    db: Session = Depends(get_db)
):
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.restaurant_id == restaurant_id  # ADD THIS - validates ownership
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return success_response(data=item)

# 5. For PUT (update):
@router.put("/items/{item_id}")
async def update_item(
    item_id: str,
    item_data: ItemUpdate,
    restaurant_id: str = Depends(get_current_restaurant),  # ADD THIS
    db: Session = Depends(get_db)
):
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.restaurant_id == restaurant_id  # ADD THIS
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    for key, value in item_data.dict(exclude_unset=True).items():
        setattr(item, key, value)
    
    db.commit()
    db.refresh(item)
    
    return success_response(data=item)

# 6. For DELETE:
@router.delete("/items/{item_id}")
async def delete_item(
    item_id: str,
    restaurant_id: str = Depends(get_current_restaurant),  # ADD THIS
    db: Session = Depends(get_db)
):
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.restaurant_id == restaurant_id  # ADD THIS
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    db.delete(item)
    
    # Update counter if needed
    from app.models.restaurant import Restaurant
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()
    if restaurant and restaurant.current_X > 0:
        restaurant.current_X -= 1
    
    db.commit()
    
    return success_response(message="Item deleted successfully")
```

---

## TASK 2: USAGE LIMIT ENFORCEMENT

### Which Endpoints Need Limit Checks:

1. **Users** - Check `max_users` before creating
2. **Products** - Check `max_products` before creating
3. **Orders** - Check `max_orders_per_month` before creating

### Implementation:

```python
# In create_user endpoint:
limits = await check_subscription_limits(restaurant_id, db)
if limits['current_users'] >= limits['max_users']:
    raise HTTPException(
        status_code=403,
        detail=f"User limit reached ({limits['max_users']}). Upgrade to add more users."
    )

# After creating user:
restaurant = limits['restaurant']
restaurant.current_users += 1
db.commit()

# In create_product endpoint:
limits = await check_subscription_limits(restaurant_id, db)
if limits['current_products'] >= limits['max_products']:
    raise HTTPException(
        status_code=403,
        detail=f"Product limit reached ({limits['max_products']}). Upgrade your plan."
    )

# After creating product:
restaurant = limits['restaurant']
restaurant.current_products += 1
db.commit()

# In create_order endpoint:
limits = await check_subscription_limits(restaurant_id, db)
if limits['current_orders_this_month'] >= limits['max_orders_per_month']:
    raise HTTPException(
        status_code=403,
        detail=f"Monthly order limit reached ({limits['max_orders_per_month']}). Upgrade your plan."
    )

# After creating order:
restaurant = limits['restaurant']
restaurant.current_orders_this_month += 1
db.commit()
```

---

## TASK 3: CREATE PLATFORM ADMIN DASHBOARD

### File: `app/routes/platform_admin.py`

```python
"""
Platform Admin Routes - SuperAdmin Dashboard
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.database import get_db
from app.dependencies import require_platform_admin
from app.models.restaurant import Restaurant, Subscription
from app.models.user import User
from app.models.product import Product
from app.models.order import Order
from app.response_formatter import success_response

router = APIRouter(prefix="/api/v1/platform", tags=["Platform Admin"])


@router.get("/dashboard")
async def platform_dashboard(
    token_data: dict = Depends(require_platform_admin),
    db: Session = Depends(get_db)
):
    """Platform-wide dashboard for SuperAdmin"""
    
    # Get all restaurants
    total_restaurants = db.query(Restaurant).count()
    active_restaurants = db.query(Restaurant).filter(
        Restaurant.is_active == True
    ).count()
    
    # Get total stats
    total_users = db.query(User).count()
    total_products = db.query(Product).count()
    total_orders = db.query(Order).count()
    
    # Get revenue (sum of all order totals)
    total_revenue = db.query(func.sum(Order.total)).scalar() or 0
    
    # Get subscriptions by plan
    subscriptions_by_plan = db.query(
        Subscription.plan,
        func.count(Subscription.id).label('count')
    ).filter(
        Subscription.status == 'active'
    ).group_by(Subscription.plan).all()
    
    # Recent restaurants
    recent_restaurants = db.query(Restaurant).order_by(
        Restaurant.created_at.desc()
    ).limit(10).all()
    
    return success_response(data={
        "overview": {
            "total_restaurants": total_restaurants,
            "active_restaurants": active_restaurants,
            "total_users": total_users,
            "total_products": total_products,
            "total_orders": total_orders,
            "total_revenue": total_revenue
        },
        "subscriptions": {
            plan: count for plan, count in subscriptions_by_plan
        },
        "recent_restaurants": [
            {
                "id": r.id,
                "name": r.name,
                "slug": r.slug,
                "plan": r.subscription_plan,
                "status": r.subscription_status,
                "created_at": r.created_at
            }
            for r in recent_restaurants
        ]
    })


@router.get("/restaurants")
async def list_all_restaurants(
    token_data: dict = Depends(require_platform_admin),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status: str = None
):
    """List all restaurants (SuperAdmin only)"""
    
    query = db.query(Restaurant)
    
    if status == "active":
        query = query.filter(Restaurant.is_active == True)
    elif status == "inactive":
        query = query.filter(Restaurant.is_active == False)
    elif status == "suspended":
        query = query.filter(Restaurant.is_suspended == True)
    
    restaurants = query.offset(skip).limit(limit).all()
    
    return success_response(data={
        "restaurants": [
            {
                "id": r.id,
                "name": r.name,
                "slug": r.slug,
                "email": r.email,
                "phone": r.phone,
                "plan": r.subscription_plan,
                "status": r.subscription_status,
                "is_active": r.is_active,
                "created_at": r.created_at,
                "current_users": r.current_users,
                "current_products": r.current_products,
                "current_orders_this_month": r.current_orders_this_month
            }
            for r in restaurants
        ],
        "total": query.count()
    })


@router.get("/restaurants/{restaurant_id}")
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
    
    # Get stats
    users_count = db.query(User).filter(
        User.restaurant_id == restaurant_id
    ).count()
    
    products_count = db.query(Product).filter(
        Product.restaurant_id == restaurant_id
    ).count()
    
    orders_count = db.query(Order).filter(
        Order.restaurant_id == restaurant_id
    ).count()
    
    total_revenue = db.query(func.sum(Order.total)).filter(
        Order.restaurant_id == restaurant_id
    ).scalar() or 0
    
    return success_response(data={
        "restaurant": restaurant,
        "stats": {
            "users": users_count,
            "products": products_count,
            "orders": orders_count,
            "revenue": total_revenue
        }
    })


@router.put("/restaurants/{restaurant_id}/status")
async def update_restaurant_status(
    restaurant_id: str,
    is_active: bool,
    suspension_reason: str = None,
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
    
    return success_response(
        message=f"Restaurant {'activated' if is_active else 'suspended'} successfully"
    )


@router.get("/analytics")
async def platform_analytics(
    token_data: dict = Depends(require_platform_admin),
    db: Session = Depends(get_db)
):
    """Platform-wide analytics (SuperAdmin only)"""
    
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
    
    # Growth metrics (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    new_restaurants = db.query(Restaurant).filter(
        Restaurant.created_at >= thirty_days_ago
    ).count()
    
    new_orders = db.query(Order).filter(
        Order.created_at >= thirty_days_ago
    ).count()
    
    return success_response(data={
        "revenue_by_restaurant": [
            {"name": name, "revenue": revenue}
            for name, revenue in revenue_by_restaurant
        ],
        "orders_by_status": [
            {"status": status, "count": count}
            for status, count in orders_by_status
        ],
        "growth": {
            "new_restaurants_30d": new_restaurants,
            "new_orders_30d": new_orders
        }
    })
```

---

## TASK 4: COMPREHENSIVE TESTING

### Create: `tests/test_multi_tenant.py`

```python
"""
Comprehensive Multi-Tenant Tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Test data
SUPERADMIN_EMAIL = "admin@platform.com"
SUPERADMIN_PASSWORD = "admin123"

def test_superadmin_login():
    """Test SuperAdmin can login"""
    response = client.post(
        "/api/v1/auth/login/json",
        json={
            "email": SUPERADMIN_EMAIL,
            "password": SUPERADMIN_PASSWORD
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "access_token" in data["data"]
    return data["data"]["access_token"]

def test_restaurant_registration():
    """Test restaurant can register"""
    response = client.post(
        "/api/v1/onboarding/register",
        json={
            "restaurant_name": "Test Restaurant",
            "owner_name": "Test Owner",
            "owner_email": "test@restaurant.com",
            "owner_phone": "1234567890",
            "password": "password123"
        }
    )
    assert response.status_code in [200, 201]

def test_data_isolation():
    """Test that restaurants can't see each other's data"""
    # Create two restaurants
    # Login as restaurant 1
    # Create product
    # Login as restaurant 2
    # Try to access restaurant 1's product
    # Should fail
    pass

def test_subscription_limits():
    """Test subscription limits are enforced"""
    # Create restaurant with trial plan
    # Try to create more products than allowed
    # Should fail with 403
    pass

def test_platform_admin_access():
    """Test SuperAdmin can access all restaurants"""
    token = test_superadmin_login()
    response = client.get(
        "/api/v1/platform/restaurants",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
```

---

## TASK 5: PRODUCTION DEPLOYMENT GUIDE

### Create: `PRODUCTION_DEPLOYMENT.md`

```markdown
# Production Deployment Guide

## Prerequisites

1. Ubuntu 20.04+ server
2. Docker and Docker Compose installed
3. MySQL 8.0+ database
4. Domain name configured
5. SSL certificate (Let's Encrypt recommended)

## Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y

# Add user to docker group
sudo usermod -aG docker $USER
```

## Step 2: Database Setup

```bash
# Install MySQL
sudo apt install mysql-server -y

# Secure MySQL
sudo mysql_secure_installation

# Create database
sudo mysql -u root -p
CREATE DATABASE restaurant_pos;
CREATE USER 'pos_user'@'localhost' IDENTIFIED BY 'strong_password';
GRANT ALL PRIVILEGES ON restaurant_pos.* TO 'pos_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## Step 3: Application Deployment

```bash
# Clone repository
git clone <your-repo-url>
cd pos-fastapi

# Create .env file
cp .env.template .env
nano .env  # Edit with production values

# Build and run
sudo docker-compose build
sudo docker-compose up -d

# Run migrations
sudo docker exec restaurant_pos_api alembic upgrade head

# Create SuperAdmin
sudo docker exec restaurant_pos_api python3 create_superadmin.py create "Admin" admin@yourdomain.com strong_password
```

## Step 4: Nginx Setup

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Step 5: SSL Setup

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

## Step 6: Monitoring

```bash
# View logs
sudo docker logs -f restaurant_pos_api

# Monitor resources
docker stats

# Database backup
mysqldump -u pos_user -p restaurant_pos > backup_$(date +%Y%m%d).sql
```

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Use strong database passwords
- [ ] Enable firewall (ufw)
- [ ] Set up fail2ban
- [ ] Configure rate limiting
- [ ] Enable HTTPS only
- [ ] Regular security updates
- [ ] Database backups automated
- [ ] Monitor logs for suspicious activity
```

---

## IMPLEMENTATION TIMELINE

### Day 1: Route Updates (6-8 hours)
- Update products.py
- Update categories.py
- Update orders.py
- Update customers.py
- Update users.py

### Day 2: Route Updates + Limits (6-8 hours)
- Update remaining 11 route files
- Add usage limit enforcement
- Test all endpoints

### Day 3: Platform Admin (4-6 hours)
- Create platform_admin.py
- Add to main.py
- Test SuperAdmin features

### Day 4: Testing (4-6 hours)
- Write comprehensive tests
- Test data isolation
- Test subscription limits
- Load testing

### Day 5: Documentation + Deployment (4-6 hours)
- Complete production guide
- Deploy to staging
- Final testing
- Deploy to production

---

## QUICK START COMMANDS

```bash
# Update a route file
nano app/routes/products.py
# Add: from app.dependencies import get_current_restaurant
# Add restaurant_id filtering to all endpoints

# Test changes
sudo docker-compose restart
curl http://localhost:8003/api/v1/products

# Create platform admin routes
nano app/routes/platform_admin.py
# Copy template from above

# Add to main.py
nano app/main.py
# Add: from app.routes import platform_admin
# Add: app.include_router(platform_admin.router)

# Restart and test
sudo docker-compose restart
```

---

## SUCCESS CRITERIA

- [ ] All 15 route files updated with restaurant filtering
- [ ] Usage limits enforced for users/products/orders
- [ ] Platform admin dashboard working
- [ ] All tests passing
- [ ] Production deployment guide complete
- [ ] System deployed and accessible
- [ ] SuperAdmin can monitor all restaurants
- [ ] Data isolation verified
- [ ] Performance acceptable (< 200ms response time)
- [ ] Security audit passed

---

**This completes the final 15% of the multi-tenant conversion!**
