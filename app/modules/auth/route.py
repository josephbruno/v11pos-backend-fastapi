from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.response import success_response, error_response
from app.modules.auth.schema import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    LoginLogResponse
)
from app.modules.auth.service import AuthService, LoginLogService
from app.modules.user.model import User


router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_device_type(user_agent: str) -> str:
    """Determine device type from user agent"""
    user_agent_lower = user_agent.lower()
    
    if "mobile" in user_agent_lower or "android" in user_agent_lower or "iphone" in user_agent_lower:
        return "mobile"
    elif "tablet" in user_agent_lower or "ipad" in user_agent_lower:
        return "tablet"
    else:
        return "desktop"


def parse_user_agent(user_agent: str) -> dict:
    """Parse user agent to extract browser and OS"""
    user_agent_lower = user_agent.lower()
    
    # Detect browser
    browser = "unknown"
    if "chrome" in user_agent_lower and "edg" not in user_agent_lower:
        browser = "Chrome"
    elif "firefox" in user_agent_lower:
        browser = "Firefox"
    elif "safari" in user_agent_lower and "chrome" not in user_agent_lower:
        browser = "Safari"
    elif "edg" in user_agent_lower:
        browser = "Edge"
    elif "opera" in user_agent_lower or "opr" in user_agent_lower:
        browser = "Opera"
    
    # Detect OS
    operating_system = "unknown"
    if "windows" in user_agent_lower:
        operating_system = "Windows"
    elif "mac" in user_agent_lower:
        operating_system = "macOS"
    elif "linux" in user_agent_lower:
        operating_system = "Linux"
    elif "android" in user_agent_lower:
        operating_system = "Android"
    elif "iphone" in user_agent_lower or "ipad" in user_agent_lower:
        operating_system = "iOS"
    
    return {
        "browser": browser,
        "operating_system": operating_system
    }


@router.post("/login", response_model=None)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and get access + refresh tokens
    
    Logs all login attempts with:
    - IP address
    - Device type
    - Timestamp
    - Success/failure status
    - Failure reason (if applicable)
    
    - **email**: User email
    - **password**: User password
    
    Returns access_token and refresh_token on success
    """
    try:
        # Extract request metadata
        ip_address = get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "unknown")
        device_type = get_device_type(user_agent)
        parsed_ua = parse_user_agent(user_agent)
        
        tokens = await AuthService.login(
            db,
            login_data.email,
            login_data.password,
            ip_address=ip_address,
            device_type=device_type,
            user_agent=user_agent,
            browser=parsed_ua["browser"],
            operating_system=parsed_ua["operating_system"]
        )
        
        if not tokens:
            return error_response(
                message="Login failed",
                error_code="INVALID_CREDENTIALS",
                error_details="Invalid email or password, or account is locked due to too many failed attempts"
            )
        
        return success_response(
            message="Login successful",
            data=tokens
        )
    except Exception as e:
        return error_response(
            message="Login failed",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.post("/refresh", response_model=None)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get new access token using refresh token
    
    - **refresh_token**: Valid refresh token
    
    Returns new access_token on success
    """
    try:
        tokens = await AuthService.refresh_access_token(db, refresh_data.refresh_token)
        
        if not tokens:
            return error_response(
                message="Token refresh failed",
                error_code="INVALID_REFRESH_TOKEN",
                error_details="Invalid or expired refresh token"
            )
        
        return success_response(
            message="Token refreshed successfully",
            data=tokens
        )
    except Exception as e:
        return error_response(
            message="Token refresh failed",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.post("/forgot-password", response_model=None)
async def forgot_password(
    forgot_data: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Request password reset (logs the attempt)
    
    - **email**: User email
    
    Note: This endpoint always returns success for security reasons,
    but logs the attempt for tracking purposes.
    """
    try:
        # Extract request metadata
        ip_address = get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "unknown")
        device_type = get_device_type(user_agent)
        parsed_ua = parse_user_agent(user_agent)
        
        # Log the forgot password attempt
        await AuthService.log_forgot_password(
            db,
            forgot_data.email,
            ip_address=ip_address,
            device_type=device_type,
            user_agent=user_agent,
            browser=parsed_ua["browser"],
            operating_system=parsed_ua["operating_system"]
        )
        
        # Always return success for security (don't reveal if email exists)
        return success_response(
            message="If the email exists, a password reset link has been sent",
            data={"email": forgot_data.email}
        )
    except Exception as e:
        return error_response(
            message="Request failed",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.post("/logout", response_model=None)
async def logout():
    """
    Logout user (client should discard tokens)
    
    Note: Since we're using stateless JWT, actual logout is handled client-side
    by discarding the tokens. This endpoint is provided for consistency.
    """
    return success_response(
        message="Logout successful",
        data={"message": "Please discard your tokens"}
    )


@router.get("/login-logs/me", response_model=None)
async def get_my_login_logs(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get login logs for current authenticated user
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    try:
        logs = await LoginLogService.get_logs_by_user_id(db, current_user.id, skip=skip, limit=limit)
        logs_data = [LoginLogResponse.model_validate(log).model_dump() for log in logs]
        
        return success_response(
            message="Login logs retrieved successfully",
            data=logs_data
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve login logs",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.get("/login-logs/email/{email}", response_model=None)
async def get_login_logs_by_email(
    email: str,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get login logs for a specific email (requires authentication)
    
    - **email**: Email address to query
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    try:
        # Only allow superusers or the user themselves to view logs
        if not current_user.is_superuser and current_user.email != email:
            return error_response(
                message="Access denied",
                error_code="FORBIDDEN",
                error_details="You can only view your own login logs"
            )
        
        logs = await LoginLogService.get_logs_by_email(db, email, skip=skip, limit=limit)
        logs_data = [LoginLogResponse.model_validate(log).model_dump() for log in logs]
        
        return success_response(
            message="Login logs retrieved successfully",
            data=logs_data
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve login logs",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.get("/login-logs/suspicious", response_model=None)
async def get_suspicious_login_logs(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get suspicious login attempts (superuser only)
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    try:
        if not current_user.is_superuser:
            return error_response(
                message="Access denied",
                error_code="FORBIDDEN",
                error_details="Only superusers can view suspicious login logs"
            )
        
        logs = await LoginLogService.get_suspicious_logs(db, skip=skip, limit=limit)
        logs_data = [LoginLogResponse.model_validate(log).model_dump() for log in logs]
        
        return success_response(
            message="Suspicious login logs retrieved successfully",
            data=logs_data
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve suspicious login logs",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )
