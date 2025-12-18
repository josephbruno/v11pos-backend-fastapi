from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum


class LoginAttemptStatus(str, Enum):
    """Login attempt status"""
    SUCCESS = "success"
    FAILED = "failed"
    FORGOT_PASSWORD = "forgot_password"


class LoginAttemptFailureReason(str, Enum):
    """Login attempt failure reason"""
    INVALID_EMAIL = "invalid_email"
    INVALID_PASSWORD = "invalid_password"
    ACCOUNT_INACTIVE = "account_inactive"
    ACCOUNT_LOCKED = "account_locked"
    NONE = "none"


class LoginRequest(BaseModel):
    """Schema for login request"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request"""
    email: EmailStr


class LoginLogCreate(BaseModel):
    """Schema for creating login log"""
    email: str
    ip_address: str
    device_type: str
    status: LoginAttemptStatus
    failure_reason: LoginAttemptFailureReason = LoginAttemptFailureReason.NONE
    user_id: Optional[str] = None
    user_agent: Optional[str] = None
    browser: Optional[str] = None
    operating_system: Optional[str] = None
    location: Optional[str] = None
    is_suspicious: bool = False
    notes: Optional[str] = None


class LoginLogResponse(BaseModel):
    """Schema for login log response"""
    id: int
    email: str
    ip_address: str
    device_type: str
    attempted_at: datetime
    status: LoginAttemptStatus
    failure_reason: LoginAttemptFailureReason
    user_id: Optional[str]
    user_agent: Optional[str]
    browser: Optional[str]
    operating_system: Optional[str]
    location: Optional[str]
    is_suspicious: bool
    notes: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)
