from typing import Any, Optional, Dict
from pydantic import BaseModel
from datetime import datetime


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
    status: str  # "success" or "error"
    message: str
    data: Optional[Any] = None
    error: Optional[ErrorDetail] = None
    meta: Optional[MetaData] = None
    timestamp: str


def success_response(
    message: str,
    data: Any = None,
    meta: Optional[Dict[str, Any]] = None
) -> dict:
    """
    Create a success response following industry standards
    
    Args:
        message: Success message
        data: Response data (can be dict, list, or any serializable object)
        meta: Optional metadata (pagination info, etc.)
        
    Returns:
        Standardized success response dictionary with format:
        {
            "status": "success",
            "message": "Operation successful",
            "data": {...},
            "error": None,
            "meta": {...},
            "timestamp": "2024-01-01T12:00:00.000Z"
        }
    """
    response = {
        "status": "success",
        "message": message,
        "data": data,
        "error": None,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    if meta:
        response["meta"] = meta
    
    return response


def error_response(
    message: str,
    error_code: str,
    error_details: Optional[str] = None,
    data: Any = None,
    field: Optional[str] = None
) -> dict:
    """
    Create an error response following industry standards
    
    Args:
        message: User-friendly error message
        error_code: Machine-readable error code (e.g., "INVALID_CREDENTIALS", "NOT_FOUND")
        error_details: Detailed technical error information (optional)
        data: Optional data (usually None for errors)
        field: Specific field that caused the error (for validation errors)
        
    Returns:
        Standardized error response dictionary with format:
        {
            "status": "error",
            "message": "User-friendly message",
            "data": None,
            "error": {
                "code": "ERROR_CODE",
                "message": "User-friendly error message",
                "details": "Technical details",
                "field": "fieldName"
            },
            "timestamp": "2024-01-01T12:00:00.000Z"
        }
    """
    return {
        "status": "error",
        "message": message,
        "data": data,
        "error": {
            "code": error_code,
            "message": message,
            "details": error_details,
            "field": field
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


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
    errors: list = None
) -> dict:
    """
    Create a validation error response for multiple field errors
    
    Args:
        message: Error message
        errors: List of validation errors [{"field": "email", "message": "Invalid format"}]
        
    Returns:
        Standardized validation error response
    """
    return {
        "status": "error",
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
