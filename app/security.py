"""
Authentication utilities for JWT token management and password hashing
Multi-tenant support added
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import uuid

# Configuration
SECRET_KEY = "your-secret-key-change-in-production"  # Should be in .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """Token data structure with multi-tenant support"""
    user_id: str
    email: EmailStr
    role: str
    restaurant_id: Optional[str] = None
    restaurant_slug: Optional[str] = None
    is_platform_admin: bool = False
    exp: datetime


class TokenResponse(BaseModel):
    """Token response structure"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int  # in seconds
    restaurant_id: Optional[str] = None
    restaurant_slug: Optional[str] = None


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: str,
    email: str,
    role: str,
    restaurant_id: Optional[str] = None,
    restaurant_slug: Optional[str] = None,
    is_platform_admin: bool = False,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token with multi-tenant support
    
    Args:
        user_id: User UUID
        email: User email
        role: User role
        restaurant_id: Restaurant UUID (optional for platform admins)
        restaurant_slug: Restaurant slug for easy identification
        is_platform_admin: Whether user is a platform admin
        expires_delta: Custom expiration time
    
    Returns:
        Encoded JWT token
    """
    to_encode = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "type": "access",
        "is_platform_admin": is_platform_admin
    }
    
    # Add restaurant context if provided
    if restaurant_id:
        to_encode["restaurant_id"] = restaurant_id
    if restaurant_slug:
        to_encode["restaurant_slug"] = restaurant_slug
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_platform_admin_token(
    user_id: str,
    email: str,
    role: str = "platform_admin",
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT token for platform admins (no restaurant context)
    
    Args:
        user_id: User UUID
        email: User email
        role: User role (defaults to platform_admin)
        expires_delta: Custom expiration time
    
    Returns:
        Encoded JWT token
    """
    return create_access_token(
        user_id=user_id,
        email=email,
        role=role,
        restaurant_id=None,
        restaurant_slug=None,
        is_platform_admin=True,
        expires_delta=expires_delta
    )


def create_refresh_token(user_id: str) -> str:
    """
    Create a JWT refresh token
    
    Args:
        user_id: User UUID
    
    Returns:
        Encoded JWT refresh token
    """
    to_encode = {
        "user_id": user_id,
        "type": "refresh",
        "jti": str(uuid.uuid4())
    }
    
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token
    
    Args:
        token: JWT token to verify
    
    Returns:
        Token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def create_token_pair(
    user_id: str,
    email: str,
    role: str,
    restaurant_id: Optional[str] = None,
    restaurant_slug: Optional[str] = None,
    is_platform_admin: bool = False
) -> TokenResponse:
    """
    Create both access and refresh tokens with multi-tenant support
    
    Args:
        user_id: User UUID
        email: User email
        role: User role
        restaurant_id: Restaurant UUID
        restaurant_slug: Restaurant slug
        is_platform_admin: Whether user is platform admin
    
    Returns:
        TokenResponse with access and refresh tokens
    """
    access_token = create_access_token(
        user_id, 
        email, 
        role,
        restaurant_id=restaurant_id,
        restaurant_slug=restaurant_slug,
        is_platform_admin=is_platform_admin
    )
    refresh_token = create_refresh_token(user_id)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        restaurant_id=restaurant_id,
        restaurant_slug=restaurant_slug
    )

