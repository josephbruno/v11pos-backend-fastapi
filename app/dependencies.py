"""
Middleware for authentication and authorization
"""
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from typing import Optional
import jwt

# Using a placeholder for SECRET_KEY - should be imported from security module
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"

security = HTTPBearer()


async def verify_token(
    credentials: HTTPAuthCredentials = Depends(security),
) -> dict:
    """
    Verify JWT token from request header
    
    Args:
        credentials: HTTP credentials from Bearer token
    
    Returns:
        Token payload
    
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
            "role": role
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
        "status": user.status
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
