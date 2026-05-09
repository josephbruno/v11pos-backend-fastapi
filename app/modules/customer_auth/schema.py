from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.customer.schema import CustomerResponse


class CustomerEmailOTPRequest(BaseModel):
    email: EmailStr
    restaurant_id: str = Field(..., min_length=36, max_length=36)


class CustomerEmailOTPVerify(BaseModel):
    email: EmailStr
    restaurant_id: str = Field(..., min_length=36, max_length=36)
    otp: str = Field(..., min_length=4, max_length=12)


class CustomerRefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10)


class CustomerGoogleLoginRequest(BaseModel):
    """
    Customer login via Google (client-provided identity).

    Note: This endpoint does NOT verify `id_token`. It uses `email` as the identity key
    within the given `restaurant_id` (creates a minimal customer record if missing),
    then issues JWT tokens.
    """

    restaurant_id: str = Field(..., min_length=36, max_length=36)
    email: EmailStr
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    # Backward-compatible field: accepted but ignored (no verification performed).
    id_token: Optional[str] = None


class CustomerAuthTokenResponse(BaseModel):
    """Returned after successful OTP verification: customer profile plus JWT credentials."""

    customer: CustomerResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(from_attributes=True)


class CustomerEmailOTPRequestResponse(BaseModel):
    """OTP request result: otp_sent means a code was stored; email_sent means SMTP accepted the message."""

    otp_sent: bool = True
    email_sent: bool = False
    expires_in_seconds: int
    development_otp: Optional[str] = None
    customer_id: Optional[str] = None
