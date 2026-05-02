from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.response import error_response, success_response
from app.modules.customer.service import CustomerService
from app.modules.customer.schema import CustomerResponse
from app.modules.customer_auth.schema import (
    CustomerAuthTokenResponse,
    CustomerEmailOTPRequest,
    CustomerEmailOTPRequestResponse,
    CustomerEmailOTPVerify,
    CustomerRefreshTokenRequest,
)
from app.modules.customer_auth.service import CustomerAuthError, CustomerAuthService, send_customer_email_otp
from app.core.dependencies import get_current_customer
from app.modules.customer.model import Customer


router = APIRouter(prefix="/customer-auth", tags=["Customer Authentication"])


async def _request_customer_otp(
    payload: CustomerEmailOTPRequest,
    request: Request,
    db: AsyncSession,
):
    customer, otp, expires_in = await CustomerAuthService.request_email_otp(
        db, str(payload.email).lower(), ip_address=_client_ip(request)
    )
    email_sent = await send_customer_email_otp(str(payload.email).lower(), otp)

    data = CustomerEmailOTPRequestResponse(
        otp_sent=True,
        email_sent=email_sent,
        expires_in_seconds=expires_in,
        customer_id=customer.id,
        development_otp=(otp if settings.is_development else None),
    ).model_dump()
    return success_response(message="OTP sent", data=data)


async def _verify_customer_otp(payload: CustomerEmailOTPVerify, db: AsyncSession):
    customer = await CustomerAuthService.verify_email_otp(db, str(payload.email).lower(), payload.otp)
    customer_full = await CustomerService.get_customer_by_id(db, customer.id)
    customer_out = customer_full or customer
    tokens = CustomerAuthService.issue_tokens(customer_out)
    resp = CustomerAuthTokenResponse(
        customer=CustomerResponse.model_validate(customer_out),
        **tokens,
    )
    return success_response(
        message="OTP verified successfully",
        data=resp.model_dump(),
    )


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/send-otp", response_model=None)
async def send_otp(
    payload: CustomerEmailOTPRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 1 — Customer authentication: send a one-time code to the customer's email.

    Next call **POST /customer-auth/verify-otp** with the same email and the OTP.
    """
    try:
        return await _request_customer_otp(payload, request, db)
    except CustomerAuthError as e:
        return error_response(
            message=str(e),
            error_code=e.code,
            error_details=str(e),
            status_code=e.status_code,
        )
    except Exception as e:
        return error_response(message="Failed to send OTP", error_code="INTERNAL_ERROR", error_details=str(e))


@router.post("/verify-otp", response_model=None)
async def verify_otp(
    payload: CustomerEmailOTPVerify,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 2 — Customer authentication: verify the OTP.

    On success, **data** includes **customer** (full profile) and JWT **access_token** / **refresh_token**.
    """
    try:
        return await _verify_customer_otp(payload, db)
    except CustomerAuthError as e:
        return error_response(
            message=str(e),
            error_code=e.code,
            error_details=str(e),
            status_code=e.status_code,
        )
    except Exception as e:
        return error_response(message="Failed to verify OTP", error_code="INTERNAL_ERROR", error_details=str(e))


@router.post("/email/request-otp", response_model=None)
async def request_email_otp(
    payload: CustomerEmailOTPRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Same as **POST /customer-auth/send-otp** (kept for backward compatibility)."""
    try:
        return await _request_customer_otp(payload, request, db)
    except CustomerAuthError as e:
        return error_response(
            message=str(e),
            error_code=e.code,
            error_details=str(e),
            status_code=e.status_code,
        )
    except Exception as e:
        return error_response(message="Failed to request OTP", error_code="INTERNAL_ERROR", error_details=str(e))


@router.post("/email/verify-otp", response_model=None)
async def verify_email_otp(
    payload: CustomerEmailOTPVerify,
    db: AsyncSession = Depends(get_db),
):
    """Same as **POST /customer-auth/verify-otp** (kept for backward compatibility)."""
    try:
        return await _verify_customer_otp(payload, db)
    except CustomerAuthError as e:
        return error_response(
            message=str(e),
            error_code=e.code,
            error_details=str(e),
            status_code=e.status_code,
        )
    except Exception as e:
        return error_response(message="Failed to verify OTP", error_code="INTERNAL_ERROR", error_details=str(e))


@router.post("/refresh", response_model=None)
async def refresh_customer_access_token(
    payload: CustomerRefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        data = await CustomerAuthService.refresh_access_token(db, payload.refresh_token)
        return success_response(message="Token refreshed successfully", data=data)
    except CustomerAuthError as e:
        return error_response(
            message=str(e),
            error_code=e.code,
            error_details=str(e),
            status_code=e.status_code,
        )
    except Exception as e:
        return error_response(message="Token refresh failed", error_code="INTERNAL_ERROR", error_details=str(e))


@router.get("/me", response_model=None)
async def get_current_customer_profile(
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    customer_with_addresses = await CustomerService.get_customer_by_id(db, customer.id)
    return success_response(
        message="Customer profile retrieved successfully",
        data=CustomerResponse.model_validate(customer_with_addresses or customer).model_dump(),
    )
