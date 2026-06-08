import asyncio
import logging
import random
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from app.modules.user.service import UserService
from app.core.security import create_access_token, create_refresh_token, decode_token, get_password_hash, verify_password
from app.modules.user.model import User
from app.modules.auth.model import LoginLog, LoginAttemptStatus, LoginAttemptFailureReason, PasswordResetOTP
from app.modules.auth.schema import LoginLogCreate
from app.core.config import settings

logger = logging.getLogger(__name__)


class LoginLogService:
    """Service layer for login log operations"""
    
    @staticmethod
    async def create_log(db: AsyncSession, log_data: LoginLogCreate) -> LoginLog:
        """
        Create a login log entry
        
        Args:
            db: Database session
            log_data: Login log data
            
        Returns:
            Created login log
        """
        db_log = LoginLog(
            email=log_data.email,
            ip_address=log_data.ip_address,
            device_type=log_data.device_type,
            status=log_data.status,
            failure_reason=log_data.failure_reason,
            user_id=log_data.user_id,
            user_agent=log_data.user_agent,
            browser=log_data.browser,
            operating_system=log_data.operating_system,
            location=log_data.location,
            is_suspicious=log_data.is_suspicious,
            notes=log_data.notes
        )
        
        db.add(db_log)
        await db.commit()
        await db.refresh(db_log)
        
        return db_log
    
    @staticmethod
    async def get_logs_by_email(
        db: AsyncSession,
        email: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[LoginLog]:
        """
        Get login logs for a specific email
        
        Args:
            db: Database session
            email: User email
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of login logs
        """
        result = await db.execute(
            select(LoginLog)
            .where(LoginLog.email == email)
            .order_by(desc(LoginLog.attempted_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_logs_by_user_id(
        db: AsyncSession,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[LoginLog]:
        """
        Get login logs for a specific user
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of login logs
        """
        result = await db.execute(
            select(LoginLog)
            .where(LoginLog.user_id == user_id)
            .order_by(desc(LoginLog.attempted_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_failed_attempts(
        db: AsyncSession,
        email: str,
        since_minutes: int = 30
    ) -> int:
        """
        Count failed login attempts for an email in the last X minutes
        
        Args:
            db: Database session
            email: User email
            since_minutes: Time window in minutes
            
        Returns:
            Number of failed attempts
        """
        since_time = datetime.utcnow() - timedelta(minutes=since_minutes)
        
        result = await db.execute(
            select(LoginLog)
            .where(
                LoginLog.email == email,
                LoginLog.status == LoginAttemptStatus.FAILED,
                LoginLog.attempted_at >= since_time
            )
        )
        
        return len(list(result.scalars().all()))
    
    @staticmethod
    async def get_suspicious_logs(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[LoginLog]:
        """
        Get suspicious login attempts
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of suspicious login logs
        """
        result = await db.execute(
            select(LoginLog)
            .where(LoginLog.is_suspicious == True)
            .order_by(desc(LoginLog.attempted_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


class AuthService:
    """Service layer for authentication operations"""
    
    @staticmethod
    async def login(
        db: AsyncSession,
        email: str,
        password: str,
        ip_address: str,
        device_type: str,
        user_agent: Optional[str] = None,
        browser: Optional[str] = None,
        operating_system: Optional[str] = None
    ) -> Optional[Dict[str, str]]:
        """
        Authenticate user and generate tokens with login logging
        
        Args:
            db: Database session
            email: User email
            password: User password
            ip_address: Client IP address
            device_type: Device type (mobile, desktop, tablet, etc.)
            user_agent: Full user agent string
            browser: Browser name
            operating_system: Operating system name
            
        Returns:
            Dictionary with access_token and refresh_token, or None if authentication fails
        """
        # Check for too many failed attempts
        failed_attempts = await LoginLogService.get_failed_attempts(db, email, since_minutes=30)
        if failed_attempts >= 5:
            # Log suspicious activity
            await LoginLogService.create_log(
                db,
                LoginLogCreate(
                    email=email,
                    ip_address=ip_address,
                    device_type=device_type,
                    status=LoginAttemptStatus.FAILED,
                    failure_reason=LoginAttemptFailureReason.ACCOUNT_LOCKED,
                    user_agent=user_agent,
                    browser=browser,
                    operating_system=operating_system,
                    is_suspicious=True,
                    notes="Too many failed login attempts"
                )
            )
            return None
        
        # Try to authenticate
        user = await UserService.authenticate_user(db, email, password)
        
        if not user:
            # Check if email exists to determine failure reason
            existing_user = await UserService.get_user_by_email(db, email)
            
            if not existing_user:
                failure_reason = LoginAttemptFailureReason.INVALID_EMAIL
            else:
                failure_reason = LoginAttemptFailureReason.INVALID_PASSWORD
            
            # Log failed attempt
            await LoginLogService.create_log(
                db,
                LoginLogCreate(
                    email=email,
                    ip_address=ip_address,
                    device_type=device_type,
                    status=LoginAttemptStatus.FAILED,
                    failure_reason=failure_reason,
                    user_agent=user_agent,
                    browser=browser,
                    operating_system=operating_system,
                    is_suspicious=failed_attempts >= 3
                )
            )
            return None
        
        if not user.is_active:
            # Log inactive account attempt
            await LoginLogService.create_log(
                db,
                LoginLogCreate(
                    email=email,
                    ip_address=ip_address,
                    device_type=device_type,
                    status=LoginAttemptStatus.FAILED,
                    failure_reason=LoginAttemptFailureReason.ACCOUNT_INACTIVE,
                    user_id=user.id,
                    user_agent=user_agent,
                    browser=browser,
                    operating_system=operating_system
                )
            )
            return None
        
        # Create tokens
        access_token = create_access_token(data={"sub": user.id})
        refresh_token = create_refresh_token(data={"sub": user.id})
        
        # Log successful login
        await LoginLogService.create_log(
            db,
            LoginLogCreate(
                email=email,
                ip_address=ip_address,
                device_type=device_type,
                status=LoginAttemptStatus.SUCCESS,
                failure_reason=LoginAttemptFailureReason.NONE,
                user_id=user.id,
                user_agent=user_agent,
                browser=browser,
                operating_system=operating_system
            )
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    async def log_forgot_password(
        db: AsyncSession,
        email: str,
        ip_address: str,
        device_type: str,
        user_agent: Optional[str] = None,
        browser: Optional[str] = None,
        operating_system: Optional[str] = None
    ) -> None:
        """
        Log forgot password attempt
        
        Args:
            db: Database session
            email: User email
            ip_address: Client IP address
            device_type: Device type
            user_agent: Full user agent string
            browser: Browser name
            operating_system: Operating system name
        """
        user = await UserService.get_user_by_email(db, email)
        
        await LoginLogService.create_log(
            db,
            LoginLogCreate(
                email=email,
                ip_address=ip_address,
                device_type=device_type,
                status=LoginAttemptStatus.FORGOT_PASSWORD,
                failure_reason=LoginAttemptFailureReason.NONE,
                user_id=user.id if user else None,
                user_agent=user_agent,
                browser=browser,
                operating_system=operating_system
            )
        )
    
    @staticmethod
    async def refresh_access_token(db: AsyncSession, refresh_token: str) -> Optional[Dict[str, str]]:
        """
        Generate new access token from refresh token
        
        Args:
            db: Database session
            refresh_token: Valid refresh token
            
        Returns:
            Dictionary with new access_token, or None if refresh token is invalid
        """
        payload = decode_token(refresh_token)
        
        if not payload:
            return None
        
        # Verify token type
        if payload.get("type") != "refresh":
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # Verify user exists and is active
        user = await UserService.get_user_by_id(db, user_id)
        if not user or not user.is_active:
            return None
        
        # Create new access token
        access_token = create_access_token(data={"sub": user.id})
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }


# ==================== Password Reset OTP ====================

def _build_reset_email(otp: str, user_name: str, expiry_minutes: int) -> tuple[str, str, str]:
    """Returns (subject, text_plain, html_body) for password reset OTP."""
    import html as html_mod
    safe_otp = html_mod.escape(otp)
    safe_name = html_mod.escape(user_name or "User")
    app_name = html_mod.escape(settings.SENDER_NAME or "Restaurant POS")
    preheader = f"Use code {otp} to reset your password. Expires in {expiry_minutes} minutes."

    subject = f"{settings.SENDER_NAME or 'Restaurant POS'} — Password Reset OTP"

    text_plain = (
        f"Hi {user_name},\n\n"
        f"You requested a password reset for your {settings.SENDER_NAME or 'Restaurant POS'} account.\n\n"
        f"Your OTP is: {otp}\n\n"
        f"This code expires in {expiry_minutes} minutes.\n\n"
        "If you did not request this, please ignore this email.\n"
        "Do not share this code with anyone.\n"
    )

    html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{app_name}</title>
</head>
<body style="margin:0;padding:0;background-color:#f0f2f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
<span style="display:none!important;visibility:hidden;opacity:0;color:transparent;height:0;width:0;max-height:0;max-width:0;overflow:hidden;">{html_mod.escape(preheader)}</span>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#f0f2f5;padding:24px 12px;">
  <tr><td align="center">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
      style="max-width:560px;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
      <tr><td style="height:4px;background:linear-gradient(90deg,#1a1a2e,#4361ee);"></td></tr>
      <tr><td style="padding:28px 28px 8px;text-align:center;">
        <p style="margin:0 0 4px;font-size:13px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:#64748b;">Password Reset</p>
        <h1 style="margin:0;font-size:22px;font-weight:700;color:#0f172a;">{app_name}</h1>
      </td></tr>
      <tr><td style="padding:8px 28px 24px;">
        <p style="margin:0 0 20px;font-size:15px;line-height:1.55;color:#334155;">
          Hi <strong>{safe_name}</strong>, use the code below to reset your password.
        </p>
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
          style="background:#f8fafc;border-radius:10px;border:1px solid #e2e8f0;">
          <tr><td align="center" style="padding:24px 16px;">
            <p style="margin:0 0 8px;font-size:12px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:#64748b;">Your reset code</p>
            <p style="margin:0;font-size:36px;font-weight:700;letter-spacing:.25em;font-family:monospace;color:#1a1a2e;">{safe_otp}</p>
          </td></tr>
        </table>
        <p style="margin:20px 0 0;font-size:14px;line-height:1.5;color:#64748b;">
          Expires in <strong style="color:#0f172a;">{expiry_minutes} minutes</strong>.
        </p>
      </td></tr>
      <tr><td style="padding:16px 28px 28px;background:#f8fafc;border-top:1px solid #e2e8f0;">
        <p style="margin:0;font-size:12px;line-height:1.6;color:#94a3b8;">
          If you did not request a password reset, please ignore this email.
          Never share this code with anyone.
        </p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>"""

    return subject, text_plain, html_body


def _send_email_sync(to_email: str, subject: str, plain_body: str, html_body: str) -> None:
    """Blocking SMTP send — run via asyncio.to_thread."""
    from_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
    if not from_email:
        raise ValueError("SENDER_EMAIL / SMTP_FROM_EMAIL not configured")

    display = (settings.SENDER_NAME or "").strip()
    from_header = formataddr((display, from_email)) if display else from_email

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_header
    msg["To"] = to_email
    msg.set_content(plain_body, subtype="plain", charset="utf-8")
    msg.add_alternative(html_body, subtype="html", charset="utf-8")

    ctx = ssl.create_default_context()
    host = settings.SMTP_HOST
    port = settings.SMTP_PORT

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

    logger.info("Password reset OTP email sent to %s", to_email)


async def send_password_reset_email(to_email: str, user_name: str, otp: str) -> bool:
    """Send password reset OTP email. Returns True on success."""
    if not settings.EMAIL_ENABLED:
        logger.info("EMAIL_ENABLED=false — skipping reset email to %s", to_email)
        return False
    if not settings.SMTP_HOST:
        logger.warning("SMTP_HOST not set — cannot send reset email to %s", to_email)
        return False

    expiry_minutes = max(1, PasswordResetOTP.OTP_TTL_SECONDS // 60)
    subject, plain_body, html_body = _build_reset_email(otp, user_name, expiry_minutes)

    try:
        await asyncio.to_thread(_send_email_sync, to_email, subject, plain_body, html_body)
        return True
    except Exception:
        logger.exception("Failed to send password reset OTP email to %s", to_email)
        return False


class PasswordResetService:
    """OTP generation, storage, verification, and password update for admin/staff."""

    OTP_RESEND_MIN_SECONDS = 60

    @staticmethod
    def _generate_otp() -> str:
        return f"{random.randint(0, 999999):06d}"

    @staticmethod
    async def create_otp(db: AsyncSession, email: str, ip_address: Optional[str] = None) -> tuple[str, int]:
        """
        Generate a new OTP for the given email, store hashed in DB.
        Enforces a 60-second resend cooldown.
        Returns (otp_plain, expires_in_seconds).
        """
        now = datetime.utcnow()

        # Rate-limit check
        result = await db.execute(
            select(PasswordResetOTP)
            .where(PasswordResetOTP.email == email)
            .order_by(desc(PasswordResetOTP.created_at))
            .limit(1)
        )
        last = result.scalar_one_or_none()
        if last and (now - last.created_at).total_seconds() < PasswordResetService.OTP_RESEND_MIN_SECONDS:
            wait = int(PasswordResetService.OTP_RESEND_MIN_SECONDS - (now - last.created_at).total_seconds())
            raise ValueError(f"Please wait {wait} seconds before requesting another OTP")

        otp = PasswordResetService._generate_otp()
        otp_hash = get_password_hash(otp)
        expires_at = PasswordResetOTP.default_expiry(now)

        record = PasswordResetOTP(
            email=email,
            otp_hash=otp_hash,
            attempts=0,
            expires_at=expires_at,
            ip_address=ip_address,
        )
        db.add(record)
        await db.commit()

        expires_in = int((expires_at - now).total_seconds())
        return otp, expires_in

    @staticmethod
    async def verify_otp(db: AsyncSession, email: str, otp: str) -> bool:
        """
        Verify OTP without consuming it (pre-check). Returns True if valid.
        Raises ValueError on invalid/expired OTP.
        """
        now = datetime.utcnow()
        result = await db.execute(
            select(PasswordResetOTP)
            .where(
                PasswordResetOTP.email == email,
                PasswordResetOTP.consumed_at.is_(None),
                PasswordResetOTP.expires_at >= now,
            )
            .order_by(desc(PasswordResetOTP.created_at))
            .limit(1)
        )
        record = result.scalar_one_or_none()
        if not record:
            raise ValueError("OTP expired or not found. Please request a new one.")

        if record.attempts >= PasswordResetOTP.MAX_ATTEMPTS:
            raise ValueError("Too many invalid attempts. Please request a new OTP.")

        if not verify_password(otp, record.otp_hash):
            record.attempts += 1
            await db.commit()
            remaining = PasswordResetOTP.MAX_ATTEMPTS - record.attempts
            raise ValueError(f"Invalid OTP. {remaining} attempt(s) remaining.")

        return True

    @staticmethod
    async def reset_password(db: AsyncSession, email: str, otp: str, new_password: str) -> User:
        """
        Verify OTP, consume it, and update user's password.
        Returns the updated User on success.
        """
        now = datetime.utcnow()
        result = await db.execute(
            select(PasswordResetOTP)
            .where(
                PasswordResetOTP.email == email,
                PasswordResetOTP.consumed_at.is_(None),
                PasswordResetOTP.expires_at >= now,
            )
            .order_by(desc(PasswordResetOTP.created_at))
            .limit(1)
        )
        record = result.scalar_one_or_none()
        if not record:
            raise ValueError("OTP expired or not found. Please request a new one.")

        if record.attempts >= PasswordResetOTP.MAX_ATTEMPTS:
            raise ValueError("Too many invalid attempts. Please request a new OTP.")

        if not verify_password(otp, record.otp_hash):
            record.attempts += 1
            await db.commit()
            remaining = PasswordResetOTP.MAX_ATTEMPTS - record.attempts
            raise ValueError(f"Invalid OTP. {remaining} attempt(s) remaining.")

        # Consume OTP
        record.consumed_at = now
        await db.commit()

        # Update password
        user = await UserService.get_user_by_email(db, email)
        if not user:
            raise ValueError("User not found")

        user.hashed_password = get_password_hash(new_password)
        await db.commit()
        await db.refresh(user)
        return user
