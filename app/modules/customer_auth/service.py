import random
from datetime import datetime
from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token, get_password_hash, verify_password
from app.modules.customer.model import Customer
from app.modules.customer.service import CustomerService
from app.modules.customer_auth.model import CustomerEmailOTP


class CustomerAuthError(Exception):
    def __init__(self, message: str, code: str = "AUTH_ERROR", status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


class CustomerAuthService:
    OTP_TTL_SECONDS = 10 * 60
    OTP_RESEND_MIN_SECONDS = 60
    OTP_MAX_ATTEMPTS = 5

    @staticmethod
    def _generate_otp() -> str:
        return f"{random.randint(0, 999999):06d}"

    @staticmethod
    async def _get_or_create_customer_by_email(db: AsyncSession, email: str) -> Customer:
        customer = await CustomerService.get_customer_by_email(db, email)
        if customer:
            return customer

        # Minimal bootstrap customer record if this is their first login.
        derived_name = (email.split("@", 1)[0] or "Customer").strip()[:255] or "Customer"
        customer = Customer(name=derived_name, email=email, is_active=True)
        db.add(customer)
        await db.commit()
        await db.refresh(customer)
        return customer

    @staticmethod
    async def request_email_otp(
        db: AsyncSession,
        email: str,
        ip_address: Optional[str] = None,
    ) -> tuple[Customer, str, int]:
        customer = await CustomerAuthService._get_or_create_customer_by_email(db, email)

        # Rate limit: avoid spamming OTP requests
        last = await db.execute(
            select(CustomerEmailOTP)
            .where(CustomerEmailOTP.email == email)
            .order_by(desc(CustomerEmailOTP.created_at))
            .limit(1)
        )
        last_otp = last.scalar_one_or_none()
        now = datetime.utcnow()
        if last_otp and (now - last_otp.created_at).total_seconds() < CustomerAuthService.OTP_RESEND_MIN_SECONDS:
            raise CustomerAuthError(
                "Please wait before requesting another OTP",
                code="OTP_RATE_LIMITED",
                status_code=429,
            )

        otp = CustomerAuthService._generate_otp()
        otp_hash = get_password_hash(otp)
        expires_at = CustomerEmailOTP.default_expiry(now)

        record = CustomerEmailOTP(
            email=email,
            customer_id=customer.id,
            otp_hash=otp_hash,
            attempts=0,
            ip_address=ip_address,
            expires_at=expires_at,
        )
        db.add(record)
        await db.commit()

        expires_in = int((expires_at - now).total_seconds())
        return customer, otp, expires_in

    @staticmethod
    async def verify_email_otp(db: AsyncSession, email: str, otp: str) -> Customer:
        now = datetime.utcnow()
        result = await db.execute(
            select(CustomerEmailOTP)
            .where(
                CustomerEmailOTP.email == email,
                CustomerEmailOTP.consumed_at.is_(None),
                CustomerEmailOTP.expires_at >= now,
            )
            .order_by(desc(CustomerEmailOTP.created_at))
            .limit(1)
        )
        record = result.scalar_one_or_none()
        if not record:
            raise CustomerAuthError("OTP expired or not found", code="OTP_NOT_FOUND", status_code=400)

        if record.attempts >= CustomerAuthService.OTP_MAX_ATTEMPTS:
            raise CustomerAuthError("Too many invalid attempts", code="OTP_LOCKED", status_code=429)

        if not verify_password(otp, record.otp_hash):
            record.attempts += 1
            await db.commit()
            raise CustomerAuthError("Invalid OTP", code="OTP_INVALID", status_code=400)

        record.consumed_at = now
        await db.commit()

        customer = await CustomerService.get_customer_by_id(db, record.customer_id)
        if not customer or not customer.is_active:
            raise CustomerAuthError("Customer not found or inactive", code="CUSTOMER_NOT_FOUND", status_code=401)
        return customer

    @staticmethod
    def issue_tokens(customer: Customer) -> dict:
        access_token = create_access_token(data={"sub": customer.id, "role": "customer"})
        refresh_token = create_refresh_token(data={"sub": customer.id, "role": "customer"})
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    @staticmethod
    async def refresh_access_token(db: AsyncSession, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if not payload:
            raise CustomerAuthError("Invalid or expired refresh token", code="INVALID_REFRESH_TOKEN", status_code=401)

        if payload.get("type") != "refresh":
            raise CustomerAuthError("Invalid token type", code="INVALID_TOKEN_TYPE", status_code=401)

        if payload.get("role") != "customer":
            raise CustomerAuthError("Invalid token role", code="INVALID_TOKEN_ROLE", status_code=401)

        customer_id = payload.get("sub")
        if not customer_id:
            raise CustomerAuthError("Invalid token payload", code="INVALID_TOKEN_PAYLOAD", status_code=401)

        customer = await CustomerService.get_customer_by_id(db, customer_id)
        if not customer or not customer.is_active:
            raise CustomerAuthError("Customer not found or inactive", code="CUSTOMER_NOT_FOUND", status_code=401)

        access_token = create_access_token(data={"sub": customer.id, "role": "customer"})
        return {
            "access_token": access_token,
            "token_type": "bearer",
        }


async def send_customer_email_otp(email: str, otp: str) -> None:
    """
    Placeholder for email delivery.
    If SMTP is not configured, we intentionally do nothing (OTP is only returned in development via API response).
    """
    if not getattr(settings, "SMTP_HOST", None):
        return
    # SMTP sending is intentionally not implemented to avoid introducing blocking IO or new dependencies.
    # Integrate your preferred provider (SMTP/SES/SendGrid/etc) here.
    return
