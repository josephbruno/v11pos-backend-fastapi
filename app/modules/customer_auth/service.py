import asyncio
import logging
import random
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr
from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token, get_password_hash, verify_password
from app.modules.customer.model import Customer
from app.modules.customer.service import CustomerService
from app.modules.customer_auth.model import CustomerEmailOTP
from app.modules.restaurant.service import RestaurantService

logger = logging.getLogger(__name__)


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
    async def _get_or_create_customer_by_email(
        db: AsyncSession, email: str, restaurant_id: str
    ) -> Customer:
        customer = await CustomerService.get_customer_by_email(db, email, restaurant_id)
        if customer:
            return customer

        # Minimal bootstrap customer record if this is their first login at this restaurant.
        derived_name = (email.split("@", 1)[0] or "Customer").strip()[:255] or "Customer"
        customer = Customer(
            name=derived_name,
            email=email,
            restaurant_id=restaurant_id,
            is_active=True,
        )
        db.add(customer)
        await db.commit()
        await db.refresh(customer)
        return customer

    @staticmethod
    async def request_email_otp(
        db: AsyncSession,
        email: str,
        restaurant_id: str,
        ip_address: Optional[str] = None,
    ) -> tuple[Customer, str, int]:
        restaurant = await RestaurantService.get_restaurant_by_id(db, restaurant_id)
        if not restaurant:
            raise CustomerAuthError("Invalid restaurant_id", code="INVALID_RESTAURANT", status_code=404)

        customer = await CustomerAuthService._get_or_create_customer_by_email(db, email, restaurant_id)

        # Rate limit: avoid spamming OTP requests (per restaurant + email)
        last = await db.execute(
            select(CustomerEmailOTP)
            .where(
                CustomerEmailOTP.email == email,
                CustomerEmailOTP.restaurant_id == restaurant_id,
            )
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
            restaurant_id=restaurant_id,
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
    async def verify_email_otp(
        db: AsyncSession, email: str, restaurant_id: str, otp: str
    ) -> Customer:
        now = datetime.utcnow()
        result = await db.execute(
            select(CustomerEmailOTP)
            .where(
                CustomerEmailOTP.email == email,
                CustomerEmailOTP.restaurant_id == restaurant_id,
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
        if customer.restaurant_id and customer.restaurant_id != restaurant_id:
            raise CustomerAuthError("Restaurant mismatch", code="RESTAURANT_MISMATCH", status_code=401)
        return customer

    @staticmethod
    def issue_tokens(customer: Customer) -> dict:
        token_data = {"sub": customer.id, "role": "customer"}
        if customer.restaurant_id:
            token_data["restaurant_id"] = customer.restaurant_id
        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)
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

        token_data = {"sub": customer.id, "role": "customer"}
        if customer.restaurant_id:
            token_data["restaurant_id"] = customer.restaurant_id
        access_token = create_access_token(data=token_data)
        return {
            "access_token": access_token,
            "token_type": "bearer",
        }


def _send_plain_email_sync(to_email: str, subject: str, body: str) -> None:
    """Blocking SMTP send (run via asyncio.to_thread)."""
    from_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
    if not from_email:
        raise ValueError("Set SENDER_EMAIL / SMTP_FROM_EMAIL or SMTP_USER / SMTP_USERNAME to send email")

    if settings.SENDER_NAME:
        from_header = formataddr((settings.SENDER_NAME, from_email))
    else:
        from_header = from_email

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_header
    msg["To"] = to_email
    msg.set_content(body)

    host = settings.SMTP_HOST
    port = settings.SMTP_PORT
    ctx = ssl.create_default_context()

    logger.info(
        "SMTP send starting to=%s host=%s port=%s use_tls=%s use_ssl=%s login_user_set=%s",
        to_email,
        host,
        port,
        settings.SMTP_USE_TLS,
        settings.SMTP_USE_SSL,
        bool(settings.SMTP_USER),
    )

    if settings.SMTP_USE_SSL:
        with smtplib.SMTP_SSL(host, port, context=ctx, timeout=30) as smtp:
            if settings.SMTP_USER:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD or "")
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.ehlo()
            if settings.SMTP_USE_TLS:
                smtp.starttls(context=ctx)
                smtp.ehlo()
            if settings.SMTP_USER:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD or "")
            smtp.send_message(msg)

    logger.info("SMTP server accepted message to=%s", to_email)


async def send_customer_email_otp(to_email: str, otp: str) -> bool:
    """
    Send the OTP to the customer's email via SMTP when SMTP_HOST is configured.

    Returns True if the message was accepted by SMTP, False if EMAIL_ENABLED is false,
    SMTP is not configured, or delivery failed (failure is logged; OTP already exists in the database).
    """
    logger.info(
        "Customer OTP email: checking to=%s email_enabled=%s smtp_host_set=%s",
        to_email,
        settings.EMAIL_ENABLED,
        bool(settings.SMTP_HOST),
    )

    if not settings.EMAIL_ENABLED:
        logger.info(
            "Customer OTP email_sent=false reason=EMAIL_DISABLED to=%s",
            to_email,
        )
        return False
    if not settings.SMTP_HOST:
        logger.info(
            "Customer OTP email_sent=false reason=NO_SMTP_HOST to=%s",
            to_email,
        )
        return False

    subject = "Your login verification code"
    body = (
        f"Your one-time code is: {otp}\n\n"
        "It expires in 10 minutes. If you did not request this, you can ignore this email."
    )
    try:
        await asyncio.to_thread(_send_plain_email_sync, to_email, subject, body)
        logger.info("Customer OTP email_sent=true to=%s", to_email)
        return True
    except Exception:
        logger.exception(
            "Customer OTP email_sent=false reason=SMTP_ERROR to=%s",
            to_email,
        )
        return False
