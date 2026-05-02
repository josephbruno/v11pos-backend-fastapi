from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.customer.schema import CustomerResponse


class CustomerEmailOTPRequest(BaseModel):
    email: EmailStr


class CustomerEmailOTPVerify(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=4, max_length=12)


class CustomerRefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10)


class CustomerAuthTokenResponse(BaseModel):
    """Returned after successful OTP verification: customer profile plus JWT credentials."""

    customer: CustomerResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(from_attributes=True)


class CustomerEmailOTPRequestResponse(BaseModel):
    otp_sent: bool = True
    expires_in_seconds: int
    development_otp: Optional[str] = None
    customer_id: Optional[str] = None
