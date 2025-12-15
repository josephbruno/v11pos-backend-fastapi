"""
Enhanced middleware for authentication and authorization with multi-tenancy support
"""
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from app.database import get_db
from typing import Optional
from jose import jwt

# Using a placeholder for SECRET_KEY - should be imported from security module
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"

security = HTTPBearer()


async def verify_token(
    credentials = Depends(security),
) -> dict:
    """
    Verify JWT token from request header with multi-tenant support
    
    Args:
        credentials: HTTP credentials from Bearer token
    
    Returns:
        Token payload including restaurant_id
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        email: str = payload.get("email")
        role: str = payload.get("role")
        token_type: str = payload.get("type")
        restaurant_id: Optional[str] = payload.get("restaurant_id")  # NEW: Multi-tenant support
        is_platform_admin: bool = payload.get("is_platform_admin", False)  # NEW: Platform admin flag
        
        if not all([user_id, email, role, token_type]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token structure"
            )
        
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        return {
            "user_id": user_id,
            "email": email,
            "role": role,
            "restaurant_id": restaurant_id,
            "is_platform_admin": is_platform_admin
        }
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


async def get_current_restaurant(
    token_data: dict = Depends(verify_token)
) -> str:
    """
    Extract restaurant_id from authenticated token
    
    Args:
        token_data: Verified token data
    
    Returns:
        restaurant_id
    
    Raises:
        HTTPException: If no restaurant context found
    """
    restaurant_id = token_data.get("restaurant_id")
    
    # Platform admins might not have restaurant_id in token
    if not restaurant_id and not token_data.get("is_platform_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No restaurant context found. Please login to a specific restaurant."
        )
    
    return restaurant_id


async def require_platform_admin(
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
) -> dict:
    """
    Verify user is a platform admin
    
    Args:
        token_data: Verified token data
        db: Database session
    
    Returns:
        Token data
    
    Raises:
        HTTPException: If user is not a platform admin
    """
    from app.models.restaurant import PlatformAdmin
    
    user_id = token_data.get("user_id")
    
    # Check if user is platform admin
    platform_admin = db.query(PlatformAdmin).filter(
        PlatformAdmin.user_id == user_id,
        PlatformAdmin.is_active == True
    ).first()
    
    if not platform_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform admin access required"
        )
    
    return token_data


async def require_restaurant_owner(
    token_data: dict = Depends(verify_token),
    restaurant_id: str = Depends(get_current_restaurant),
    db: Session = Depends(get_db)
) -> dict:
    """
    Verify user is owner of the current restaurant
    
    Args:
        token_data: Verified token data
        restaurant_id: Current restaurant ID
        db: Database session
    
    Returns:
        Token data
    
    Raises:
        HTTPException: If user is not restaurant owner
    """
    from app.models.restaurant import RestaurantOwner
    
    user_id = token_data.get("user_id")
    
    # Check if user is owner of this restaurant
    owner = db.query(RestaurantOwner).filter(
        RestaurantOwner.user_id == user_id,
        RestaurantOwner.restaurant_id == restaurant_id,
        RestaurantOwner.is_active == True
    ).first()
    
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Restaurant owner access required"
        )
    
    return token_data


async def validate_restaurant_access(
    token_data: dict = Depends(verify_token),
    restaurant_id: str = Depends(get_current_restaurant),
    db: Session = Depends(get_db)
) -> str:
    """
    Validate user has access to the restaurant
    
    Args:
        token_data: Verified token data
        restaurant_id: Restaurant ID to validate
        db: Database session
    
    Returns:
        restaurant_id
    
    Raises:
        HTTPException: If user doesn't have access
    """
    from app.models.user import User
    from app.models.restaurant import Restaurant
    
    user_id = token_data.get("user_id")
    is_platform_admin = token_data.get("is_platform_admin", False)
    
    # Platform admins can access any restaurant
    if is_platform_admin:
        return restaurant_id
    
    # Check if user belongs to this restaurant
    user = db.query(User).filter(
        User.id == user_id,
        User.restaurant_id == restaurant_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this restaurant"
        )
    
    # Check if restaurant is active
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id,
        Restaurant.is_active == True
    ).first()
    
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Restaurant is not active or does not exist"
        )
    
    return restaurant_id


async def check_subscription_limits(
    restaurant_id: str = Depends(get_current_restaurant),
    db: Session = Depends(get_db)
) -> dict:
    """
    Check restaurant subscription limits
    
    Args:
        restaurant_id: Restaurant ID
        db: Database session
    
    Returns:
        Restaurant with limits info
    
    Raises:
        HTTPException: If subscription is inactive or limits exceeded
    """
    from app.models.restaurant import Restaurant
    
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()
    
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )
    
    # Check subscription status
    if restaurant.subscription_status not in ['active', 'trial']:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Subscription is {restaurant.subscription_status}. Please update your subscription."
        )
    
    # Check if trial has expired
    if restaurant.subscription_status == 'trial' and restaurant.trial_ends_at:
        from datetime import datetime
        if datetime.utcnow() > restaurant.trial_ends_at:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Trial period has expired. Please upgrade your subscription."
            )
    
    return {
        "restaurant": restaurant,
        "max_users": restaurant.max_users,
        "max_products": restaurant.max_products,
        "max_orders_per_month": restaurant.max_orders_per_month,
        "current_users": restaurant.current_users,
        "current_products": restaurant.current_products,
        "current_orders_this_month": restaurant.current_orders_this_month
    }


def require_role(*allowed_roles: str):
    """
    Dependency to check if user has required role
    
    Args:
        *allowed_roles: Allowed roles for the endpoint
    
    Returns:
        Dependency function
    """
    async def verify_role(
        token_data: dict = Depends(verify_token)
    ) -> dict:
        """Verify user role"""
        user_role = token_data.get("role")
        
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}"
            )
        
        return token_data
    
    return verify_role


def require_permission(permission: str):
    """
    Dependency to check if user has required permission
    
    Args:
        permission: Required permission
    
    Returns:
        Dependency function
    """
    async def verify_permission(
        token_data: dict = Depends(verify_token),
        db: Session = Depends(get_db)
    ) -> dict:
        """Verify user permission"""
        from app.models.user import User
        
        user_id = token_data.get("user_id")
        
        # Get user and their permissions
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Check permission (assuming permissions are stored as JSON list or similar)
        user_permissions = user.permissions or []
        
        if permission not in user_permissions and user.role not in ["admin", "manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        
        return token_data
    
    return verify_permission


async def get_current_user(
    token_data: dict = Depends(verify_token),
    db: Session = Depends(get_db)
) -> dict:
    """
    Get current authenticated user with details
    
    Args:
        token_data: Verified token data
        db: Database session
    
    Returns:
        User information
    """
    from app.models.user import User
    
    user_id = token_data.get("user_id")
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "status": user.status,
        "restaurant_id": user.restaurant_id
    }


async def get_admin_user(
    token_data: dict = Depends(require_role("admin"))
) -> dict:
    """Get current user with admin role requirement"""
    return token_data


async def get_manager_user(
    token_data: dict = Depends(require_role("admin", "manager"))
) -> dict:
    """Get current user with manager or admin role"""
    return token_data


async def get_staff_user(
    token_data: dict = Depends(require_role("admin", "manager", "staff", "cashier"))
) -> dict:
    """Get current user with staff or higher role"""
    return token_data
