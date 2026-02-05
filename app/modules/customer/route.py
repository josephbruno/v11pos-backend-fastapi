from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.response import success_response, error_response
from app.modules.customer.schema import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse
)
from app.modules.customer.service import CustomerService
from app.modules.user.model import User


router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new customer
    
    - **name**: Customer name (required)
    - **email**: Customer email
    - **phone**: Customer phone number
    - **address**: Street address
    - **city**: City
    - **state**: State/Province
    - **postal_code**: Postal/ZIP code
    - **country**: Country
    - **latitude**: Geographic latitude (-90 to 90)
    - **longitude**: Geographic longitude (-180 to 180)
    - **notes**: Additional notes
    """
    try:
        customer = await CustomerService.create_customer(db, customer_data)
        return success_response(
            data=CustomerResponse.model_validate(customer),
            message="Customer created successfully"
        )
    except Exception as e:
        return error_response(
            message="Failed to create customer",
            error=str(e)
        )


@router.get("/{customer_id}", response_model=dict)
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get customer by ID"""
    customer = await CustomerService.get_customer_by_id(db, customer_id)
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    return success_response(
        data=CustomerResponse.model_validate(customer),
        message="Customer retrieved successfully"
    )


@router.get("/", response_model=dict)
async def get_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name, email, or phone"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get paginated list of customers with optional filtering
    
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return (max 100)
    - **search**: Search term for name, email, or phone
    - **is_active**: Filter by active status
    """
    customers, total = await CustomerService.get_customers(
        db,
        skip=skip,
        limit=limit,
        search=search,
        is_active=is_active
    )
    
    return success_response(
        data=[CustomerResponse.model_validate(c) for c in customers],
        meta={
            "total": total,
            "skip": skip,
            "limit": limit
        },
        message="Customers retrieved successfully"
    )


@router.put("/{customer_id}", response_model=dict)
async def update_customer(
    customer_id: str,
    customer_data: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update customer information"""
    customer = await CustomerService.update_customer(db, customer_id, customer_data)
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    return success_response(
        data=CustomerResponse.model_validate(customer),
        message="Customer updated successfully"
    )


@router.delete("/{customer_id}", response_model=dict)
async def delete_customer(
    customer_id: str,
    permanent: bool = Query(False, description="Permanently delete customer"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete customer (soft delete by default, set permanent=true for hard delete)
    
    - **customer_id**: Customer ID
    - **permanent**: If true, permanently delete the customer from database
    """
    if permanent:
        success = await CustomerService.permanently_delete_customer(db, customer_id)
    else:
        success = await CustomerService.delete_customer(db, customer_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    return success_response(
        data={"id": customer_id},
        message="Customer deleted successfully"
    )


@router.get("/search/by-location", response_model=dict)
async def search_customers_by_location(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(10.0, ge=0.1, le=100, description="Search radius in kilometers"),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search customers by proximity to a location
    
    - **latitude**: Center latitude (-90 to 90)
    - **longitude**: Center longitude (-180 to 180)
    - **radius_km**: Search radius in kilometers (0.1 to 100)
    - **limit**: Maximum number of results (max 100)
    """
    customers = await CustomerService.search_customers_by_location(
        db,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        limit=limit
    )
    
    return success_response(
        data=[CustomerResponse.model_validate(c) for c in customers],
        meta={
            "total": len(customers),
            "center": {"latitude": latitude, "longitude": longitude},
            "radius_km": radius_km
        },
        message="Customers retrieved successfully"
    )
