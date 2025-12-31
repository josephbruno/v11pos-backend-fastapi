from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import decode_token
from app.modules.user.model import User
from sqlalchemy import select
from typing import Optional


# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token
    
    Args:
        credentials: HTTP Authorization credentials
        db: Database session
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    # Decode token
    payload = decode_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user ID from token
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database with restaurant timezone
    from app.modules.restaurant.model import Restaurant
    result = await db.execute(
        select(User, Restaurant.timezone, Restaurant.date_format, Restaurant.time_format, Restaurant.country)
        .join(Restaurant, User.restaurant_id == Restaurant.id, isouter=True)
        .where(User.id == user_id)
    )
    row = result.one_or_none()
    
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = row[0]
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Add timezone settings to user object for easy access
    user.timezone = row[1] or 'Asia/Kolkata'
    user.date_format = row[2] or 'DD/MM/YYYY'
    user.time_format = row[3] or '24h'
    user.country = row[4] or 'India'
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current active user
    
    Args:
        current_user: Current user from token
        
    Returns:
        Current active user
    """
    return current_user


async def get_current_superadmin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current super admin user
    
    Args:
        current_user: Current user from token
        
    Returns:
        Current super admin user
        
    Raises:
        HTTPException: If user is not a super admin
    """
    if not current_user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Super admin privileges required."
        )
    
    return current_user


async def get_restaurant_timezone(
    current_user: User = Depends(get_current_user)
) -> str:
    """
    Dependency to get restaurant timezone
    
    Args:
        current_user: Current user from token
        
    Returns:
        Restaurant timezone string
    """
    return getattr(current_user, 'timezone', 'Asia/Kolkata')
