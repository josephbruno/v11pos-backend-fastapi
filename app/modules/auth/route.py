from fastapi import APIRouter, Depends, status, Request, Form, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.response import success_response, error_response
from app.modules.auth.schema import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    VerifyOTPRequest,
    ResetPasswordRequest,
    LoginLogResponse
)
from app.modules.auth.service import AuthService, LoginLogService, PasswordResetService, send_password_reset_email
from app.modules.user.model import User
from app.modules.user.service import UserService


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
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and get access + refresh tokens
    
    Accepts both JSON and form-encoded data:
    - JSON: {"email": "user@example.com", "password": "password123"}
    - Form: email=user@example.com&password=password123
    
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
        user_email = None
        user_password = None
        
        # Check content type and parse accordingly
        content_type = request.headers.get("content-type", "").lower()
        
        if "application/json" in content_type:
            # Parse JSON body
            try:
                body = await request.json()
                user_email = body.get("email")
                user_password = body.get("password")
            except Exception:
                return error_response(
                    message="Invalid JSON",
                    error_code="INVALID_JSON",
                    error_details="Request body must be valid JSON",
                    status_code=400
                )
        elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            # Parse form data
            try:
                form = await request.form()
                user_email = form.get("email")
                user_password = form.get("password")
            except Exception:
                return error_response(
                    message="Invalid form data",
                    error_code="INVALID_FORM",
                    error_details="Request body must be valid form data",
                    status_code=400
                )
        else:
            return error_response(
                message="Unsupported content type",
                error_code="UNSUPPORTED_CONTENT_TYPE",
                error_details="Content-Type must be application/json or application/x-www-form-urlencoded",
                status_code=400
            )
        
        # Validate credentials are provided
        if not user_email or not user_password:
            return error_response(
                message="Missing credentials",
                error_code="MISSING_CREDENTIALS",
                error_details="Email and password are required",
                status_code=400
            )
        
        # Extract request metadata
        ip_address = get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "unknown")
        device_type = get_device_type(user_agent)
        parsed_ua = parse_user_agent(user_agent)
        
        tokens = await AuthService.login(
            db,
            user_email,
            user_password,
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
    Request a 6-digit password reset OTP. The OTP is emailed to the user.
    Returns 404 if the email is not registered.
    """
    try:
        user = await UserService.get_user_by_email(db, forgot_data.email)
        if not user:
            return error_response(
                message="Email not found",
                error_code="USER_NOT_FOUND",
                error_details=f"No account found with email {forgot_data.email}",
                status_code=status.HTTP_404_NOT_FOUND
            )

        ip_address = get_client_ip(request)

        try:
            otp, expires_in = await PasswordResetService.create_otp(
                db, forgot_data.email, ip_address=ip_address
            )
        except ValueError as ve:
            return error_response(
                message=str(ve),
                error_code="OTP_RATE_LIMIT",
                status_code=429
            )

        user_name = getattr(user, "full_name", None) or getattr(user, "name", None) or forgot_data.email.split("@")[0]
        await send_password_reset_email(forgot_data.email, user_name, otp)

        # Also log the forgot-password attempt
        user_agent = request.headers.get("User-Agent", "unknown")
        device_type = get_device_type(user_agent)
        parsed_ua = parse_user_agent(user_agent)
        await AuthService.log_forgot_password(
            db, forgot_data.email,
            ip_address=ip_address,
            device_type=device_type,
            user_agent=user_agent,
            browser=parsed_ua["browser"],
            operating_system=parsed_ua["operating_system"]
        )

        return success_response(
            message="OTP has been sent to your email address",
            data={"email": forgot_data.email, "expires_in": expires_in}
        )
    except Exception as e:
        return error_response(
            message="Request failed",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.post("/verify-otp", response_model=None)
async def verify_otp(
    body: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Pre-validate OTP before the user submits a new password.
    Does NOT consume the OTP — call /reset-password to finalize.
    """
    try:
        await PasswordResetService.verify_otp(db, body.email, body.otp)
        return success_response(message="OTP is valid", data={"valid": True})
    except ValueError as ve:
        return error_response(
            message=str(ve),
            error_code="INVALID_OTP",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return error_response(
            message="Verification failed",
            error_code="INTERNAL_ERROR",
            error_details=str(e)
        )


@router.post("/reset-password", response_model=None)
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify OTP and reset the user's password in one step.
    Consumes the OTP — it cannot be reused.
    """
    try:
        await PasswordResetService.reset_password(db, body.email, body.otp, body.new_password)
        return success_response(
            message="Password has been reset successfully",
            data={"email": body.email}
        )
    except ValueError as ve:
        return error_response(
            message=str(ve),
            error_code="RESET_FAILED",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return error_response(
            message="Password reset failed",
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
