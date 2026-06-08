from sqlalchemy import String, Boolean, DateTime, Integer, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timedelta
from typing import Optional
from app.core.database import Base
import enum


class LoginAttemptStatus(str, enum.Enum):
    """Login attempt status enum"""
    SUCCESS = "success"
    FAILED = "failed"
    FORGOT_PASSWORD = "forgot_password"


class LoginAttemptFailureReason(str, enum.Enum):
    """Login attempt failure reason enum"""
    INVALID_EMAIL = "invalid_email"
    INVALID_PASSWORD = "invalid_password"
    ACCOUNT_INACTIVE = "account_inactive"
    ACCOUNT_LOCKED = "account_locked"
    NONE = "none"


class LoginLog(Base):
    """Login log database model"""
    
    __tablename__ = "login_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Mandatory fields
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)  # IPv6 max length
    device_type: Mapped[str] = mapped_column(String(100), nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Status and reason
    status: Mapped[LoginAttemptStatus] = mapped_column(
        SQLEnum(LoginAttemptStatus),
        nullable=False,
        index=True
    )
    failure_reason: Mapped[LoginAttemptFailureReason] = mapped_column(
        SQLEnum(LoginAttemptFailureReason),
        nullable=False,
        default=LoginAttemptFailureReason.NONE
    )
    
    # Additional fields
    user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)  # Null if login failed
    user_agent: Mapped[str] = mapped_column(Text, nullable=True)  # Full user agent string
    browser: Mapped[str] = mapped_column(String(100), nullable=True)
    operating_system: Mapped[str] = mapped_column(String(100), nullable=True)
    location: Mapped[str] = mapped_column(String(255), nullable=True)  # City, Country
    
    # Security tracking
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return f"<LoginLog(id={self.id}, email={self.email}, status={self.status}, ip={self.ip_address})>"


class PasswordResetOTP(Base):
    """OTP records for admin/staff password reset."""

    __tablename__ = "password_reset_otps"

    OTP_TTL_SECONDS = 600  # 10 minutes
    MAX_ATTEMPTS = 5

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    otp_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    consumed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    @staticmethod
    def default_expiry(now: Optional[datetime] = None) -> datetime:
        base = now or datetime.utcnow()
        return base + timedelta(seconds=PasswordResetOTP.OTP_TTL_SECONDS)

    def __repr__(self) -> str:
        return f"<PasswordResetOTP(id={self.id}, email={self.email})>"
