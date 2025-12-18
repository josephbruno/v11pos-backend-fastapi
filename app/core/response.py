from typing import Any, Optional
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Error detail structure"""
    code: str
    details: str


class APIResponse(BaseModel):
    """Standard API response format"""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[ErrorDetail] = None


def success_response(
    message: str,
    data: Any = None
) -> dict:
    """
    Create a success response
    
    Args:
        message: Success message
        data: Response data
        
    Returns:
        Standardized success response dictionary
    """
    return {
        "success": True,
        "message": message,
        "data": data,
        "error": None
    }


def error_response(
    message: str,
    error_code: str,
    error_details: str,
    data: Any = None
) -> dict:
    """
    Create an error response
    
    Args:
        message: Error message
        error_code: Error code identifier
        error_details: Detailed error information
        data: Optional data
        
    Returns:
        Standardized error response dictionary
    """
    return {
        "success": False,
        "message": message,
        "data": data,
        "error": {
            "code": error_code,
            "details": error_details
        }
    }
