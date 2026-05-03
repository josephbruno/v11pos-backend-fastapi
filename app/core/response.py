from typing import Any, Optional, Dict
from pydantic import BaseModel
from datetime import datetime
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from app.core.timezone import convert_datetime_fields, get_utc_now


class ErrorDetail(BaseModel):
    """Error detail structure"""
    code: str
    message: str
    details: Optional[str] = None
    field: Optional[str] = None


class MetaData(BaseModel):
    """Metadata structure for pagination and additional info"""
    page: Optional[int] = None
    limit: Optional[int] = None
    total: Optional[int] = None
    total_pages: Optional[int] = None


class APIResponse(BaseModel):
    """Standard API response format"""
    success: bool  # true for success, false for error
    status_code: int  # HTTP status code (200, 201, 400, 404, 500, etc.)
    message: str
    data: Optional[Any] = None
    error: Optional[ErrorDetail] = None
    meta: Optional[MetaData] = None
    timestamp: str


def success_response(
    message: str,
    data: Any = None,
    meta: Optional[Dict[str, Any]] = None,
    status_code: int = 200,
    timezone: Optional[str] = None
) -> JSONResponse:
    """
    Create a success response following industry standards
    
    Args:
        message: Success message
        data: Response data (can be dict, list, or any serializable object)
        meta: Optional metadata (pagination info, etc.)
        status_code: HTTP status code (default: 200, use 201 for created)
        timezone: Optional timezone for datetime conversion (if None, returns UTC)
        
    Returns:
        JSONResponse with standardized success response format:
        {
            "success": true,
            "status_code": 200,
            "message": "Operation successful",
            "data": {...},
            "error": null,
            "meta": {...},
            "timestamp": "2024-01-01T12:00:00.000Z"
        }
    """
    # Convert datetime fields to restaurant timezone if specified
    if timezone and data:
        data = convert_datetime_fields(data, timezone)
    
    response = {
        "success": True,
        "status_code": status_code,
        "message": message,
        "data": jsonable_encoder(data),
        "error": None,
        "timestamp": get_utc_now().isoformat()
    }
    
    if meta:
        response["meta"] = jsonable_encoder(meta)
    
    return JSONResponse(content=response, status_code=status_code)


def error_response(
    message: str,
    error_code: str,
    error_details: Optional[str] = None,
    data: Any = None,
    field: Optional[str] = None,
    status_code: int = 400
) -> JSONResponse:
    """
    Create an error response following industry standards
    
    Args:
        message: User-friendly error message
        error_code: Machine-readable error code (e.g., "INVALID_CREDENTIALS", "NOT_FOUND")
        error_details: Detailed technical error information (optional)
        data: Optional data (usually None for errors)
        field: Specific field that caused the error (for validation errors)
        status_code: HTTP status code (default: 400, use 401, 404, 500, etc.)
        
    Returns:
        JSONResponse with standardized error response format:
        {
            "success": false,
            "status_code": 400,
            "message": "User-friendly message",
            "data": null,
            "error": {
                "code": "ERROR_CODE",
                "message": "User-friendly error message",
                "details": "Technical details",
                "field": "fieldName"
            },
            "timestamp": "2024-01-01T12:00:00.000Z"
        }
    """
    response_content = {
        "success": False,
        "status_code": status_code,
        "message": message,
        "data": jsonable_encoder(data),
        "error": {
            "code": error_code,
            "message": message,
            "details": error_details,
            "field": field
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    return JSONResponse(content=response_content, status_code=status_code)


def paginated_response(
    message: str,
    data: Any,
    page: int,
    limit: int,
    total: int
) -> dict:
    """
    Create a paginated response with metadata
    
    Args:
        message: Success message
        data: List of items for current page
        page: Current page number (1-indexed)
        limit: Items per page
        total: Total number of items
        
    Returns:
        Standardized paginated response with metadata
    """
    total_pages = (total + limit - 1) // limit if limit > 0 else 0
    
    return success_response(
        message=message,
        data=data,
        meta={
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    )


def validation_error_response(
    message: str = "Validation failed",
    errors: list = None,
    status_code: int = 422
) -> JSONResponse:
    """
    Create a validation error response for multiple field errors
    
    Args:
        message: Error message
        errors: List of validation errors [{"field": "email", "message": "Invalid format"}]
        status_code: HTTP status code (default: 422 Unprocessable Entity)
        
    Returns:
        JSONResponse with standardized validation error response
    """
    response_content = {
        "success": False,
        "status_code": status_code,
        "message": message,
        "data": None,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": message,
            "details": "One or more fields contain invalid data",
            "errors": errors or []
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    return JSONResponse(content=response_content, status_code=status_code)


def sanitize_validation_errors_for_json(value: Any) -> Any:
    """
    Recursively replace binary values so validation error payloads are JSON-safe.

    Pydantic v2 may include raw bytes in error details (for example multipart
    bodies or file fields). FastAPI's default handler passes errors through
    ``jsonable_encoder``, which decodes ``bytes`` as UTF-8 and can raise
    ``UnicodeDecodeError`` on image or other binary content.
    """
    if isinstance(value, (bytes, bytearray, memoryview)):
        return f"<binary data: {len(value)} bytes>"
    if isinstance(value, dict):
        return {k: sanitize_validation_errors_for_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize_validation_errors_for_json(v) for v in value]
    if isinstance(value, set):
        return [sanitize_validation_errors_for_json(v) for v in value]
    return value


async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """422 handler that never fails when error ``input`` contains binary data."""
    safe_detail = sanitize_validation_errors_for_json(exc.errors())
    return JSONResponse(
        status_code=422,
        content={"detail": jsonable_encoder(safe_detail)},
    )
