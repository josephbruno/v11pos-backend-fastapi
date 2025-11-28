"""
Authentication Pydantic schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from app.enums import UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1440  # 24 hours in minutes
    user: Optional[dict] = None  # User information


class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserRegister(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=6, max_length=100)
    role: UserRole = UserRole.STAFF


class ChangePassword(BaseModel):
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to send OTP")


class VerifyOTPRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")


class ResetPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")
    new_password: str = Field(..., min_length=6, max_length=100, description="New password")
