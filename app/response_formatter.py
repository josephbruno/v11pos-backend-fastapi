"""
Standard API Response Formatter
All API responses should follow this format:
{
  "status": "success" | "error",
  "message": "Description of the result",
  "data": {...} | [...] | null
}
"""
from typing import Any, Optional, Union, List, Dict
from fastapi.responses import JSONResponse


def success_response(
    data: Optional[Union[Dict, List, Any]] = None,
    message: str = "Operation successful",
    status_code: int = 200
) -> Dict[str, Any]:
    """
    Create a standardized success response
    
    Args:
        data: The response data (can be dict, list, or any serializable object)
        message: Success message
        status_code: HTTP status code (default: 200)
    
    Returns:
        Standardized response dictionary
    """
    return {
        "status": "success",
        "message": message,
        "data": data
    }


def error_response(
    message: str = "An error occurred",
    data: Optional[Union[Dict, List, Any]] = None,
    status_code: int = 400
) -> JSONResponse:
    """
    Create a standardized error response
    
    Args:
        message: Error message
        data: Additional error data (optional)
        status_code: HTTP status code (default: 400)
    
    Returns:
        JSONResponse with standardized error format
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "message": message,
            "data": data
        }
    )


def created_response(
    data: Optional[Union[Dict, List, Any]] = None,
    message: str = "Resource created successfully"
) -> Dict[str, Any]:
    """
    Create a standardized response for resource creation (201)
    
    Args:
        data: The created resource data
        message: Success message
    
    Returns:
        Standardized response dictionary
    """
    return {
        "status": "success",
        "message": message,
        "data": data
    }


def deleted_response(
    message: str = "Resource deleted successfully"
) -> Dict[str, Any]:
    """
    Create a standardized response for resource deletion
    
    Args:
        message: Success message
    
    Returns:
        Standardized response dictionary
    """
    return {
        "status": "success",
        "message": message,
        "data": None
    }


def list_response(
    items: List[Any],
    message: str = "Data fetched successfully",
    total: Optional[int] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create a standardized response for list/collection endpoints
    
    Args:
        items: List of items
        message: Success message
        total: Total count of items (for pagination)
        page: Current page number
        page_size: Items per page
    
    Returns:
        Standardized response dictionary
    """
    data = {
        "items": items,
        "count": len(items)
    }
    
    if total is not None:
        data["total"] = total
    if page is not None:
        data["page"] = page
    if page_size is not None:
        data["page_size"] = page_size
    
    return {
        "status": "success",
        "message": message,
        "data": data
    }
