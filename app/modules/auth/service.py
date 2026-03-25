from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from app.modules.user.service import UserService
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.modules.user.model import User
from app.modules.auth.model import LoginLog, LoginAttemptStatus, LoginAttemptFailureReason
from app.modules.auth.schema import LoginLogCreate


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
